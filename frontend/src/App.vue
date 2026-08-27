<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { askPolicy } from './api'
import { loadConversations, saveConversations } from './storage'
import type { Conversation, Message, Mode } from './types'

const conversations = ref<Conversation[]>(loadConversations())
const activeId = ref(conversations.value[0]?.id ?? '')
const input = ref('')
const loading = ref(false)
const feed = ref<HTMLElement | null>(null)

const active = computed(() => conversations.value.find((item) => item.id === activeId.value))

watch(conversations, (value) => saveConversations(value), { deep: true })

function uid(): string {
  return crypto.randomUUID()
}

function createConversation(): void {
  const conversation: Conversation = {
    id: uid(),
    title: '新的校規問題',
    mode: 'search',
    messages: [],
    updatedAt: new Date().toISOString(),
  }
  conversations.value.unshift(conversation)
  activeId.value = conversation.id
}

function renameConversation(conversation: Conversation): void {
  const title = window.prompt('輸入新的對話名稱', conversation.title)?.trim()
  if (title) conversation.title = title.slice(0, 40)
}

function removeConversation(id: string): void {
  if (!window.confirm('確定刪除這個本機對話紀錄？')) return
  conversations.value = conversations.value.filter((item) => item.id !== id)
  if (activeId.value === id) activeId.value = conversations.value[0]?.id ?? ''
}

function setMode(mode: Mode): void {
  if (active.value) active.value.mode = mode
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  feed.value?.scrollTo({ top: feed.value.scrollHeight, behavior: 'smooth' })
}

async function submit(): Promise<void> {
  const question = input.value.trim()
  if (!question || loading.value) return
  if (!active.value) createConversation()
  const conversation = active.value
  if (!conversation) return

  const priorMessages = [...conversation.messages]
  const userMessage: Message = { id: uid(), role: 'user', content: question }
  conversation.messages.push(userMessage)
  if (conversation.messages.length === 1) conversation.title = question.slice(0, 28)
  conversation.updatedAt = new Date().toISOString()
  input.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await askPolicy(question, conversation.mode, priorMessages)
    conversation.messages.push({
      id: uid(),
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      warning: response.warnings.join('；') || undefined,
    })
  } catch (error) {
    conversation.messages.push({
      id: uid(),
      role: 'assistant',
      content: error instanceof Error ? error.message : '服務目前無法使用。',
      warning: '這則訊息不是校規回答。',
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

if (conversations.value.length === 0) createConversation()
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">規</span>
        <div><strong>校規智慧助理</strong><small>Clause-grounded RAG</small></div>
      </div>
      <button class="new-chat" type="button" @click="createConversation">＋ 新增對話</button>
      <nav aria-label="對話紀錄">
        <article
          v-for="conversation in conversations"
          :key="conversation.id"
          class="conversation"
          :class="{ active: conversation.id === activeId }"
          @click="activeId = conversation.id"
        >
          <button class="conversation-title" type="button">{{ conversation.title }}</button>
          <div class="conversation-actions">
            <button type="button" title="重新命名" @click.stop="renameConversation(conversation)">編輯</button>
            <button type="button" title="刪除" @click.stop="removeConversation(conversation.id)">刪除</button>
          </div>
        </article>
      </nav>
      <p class="privacy">對話只保存在這台瀏覽器。正式決策仍應核對官方法規與承辦單位說明。</p>
    </aside>

    <main v-if="active" class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">依據檢索條款回答</p>
          <h1>{{ active.title }}</h1>
        </div>
        <div class="mode-picker" aria-label="回答模式">
          <button :class="{ selected: active.mode === 'search' }" @click="setMode('search')">找條文</button>
          <button :class="{ selected: active.mode === 'explain' }" @click="setMode('explain')">白話解釋</button>
          <button :class="{ selected: active.mode === 'draft' }" @click="setMode('draft')">產生草稿</button>
        </div>
      </header>

      <section ref="feed" class="feed" aria-live="polite">
        <div v-if="active.messages.length === 0" class="empty-state">
          <span class="empty-icon">§</span>
          <h2>從校規依據開始，而不是從猜測開始</h2>
          <p>詢問資格、期限、程序或應備文件。每個回答都必須附上實際檢索到的來源標記。</p>
          <div class="examples">
            <button @click="input = '申請這項程序需要哪些文件與期限？'">申請需要哪些文件與期限？</button>
            <button @click="input = '請用白話解釋這項規定的適用對象。'">解釋規定的適用對象</button>
          </div>
        </div>

        <article v-for="message in active.messages" :key="message.id" class="message" :class="message.role">
          <div class="avatar">{{ message.role === 'user' ? '你' : '規' }}</div>
          <div class="message-body">
            <p class="message-text">{{ message.content }}</p>
            <p v-if="message.warning" class="warning">{{ message.warning }}</p>
            <details v-if="message.sources?.length" class="sources">
              <summary>查看 {{ message.sources.length }} 筆引用依據</summary>
              <article v-for="source in message.sources" :key="source.chunk_id" class="source-card">
                <div class="source-heading">
                  <span>[{{ source.citation_id }}]</span>
                  <strong>{{ source.title }}</strong>
                  <small>{{ source.section_id || '未標示條次' }}</small>
                </div>
                <p>{{ source.content }}</p>
                <a v-if="source.source_url" :href="source.source_url" target="_blank" rel="noopener noreferrer">開啟官方來源 ↗</a>
              </article>
            </details>
          </div>
        </article>
        <div v-if="loading" class="thinking"><span></span><span></span><span></span> 正在檢索條款並核對引用</div>
      </section>

      <form class="composer" @submit.prevent="submit">
        <label for="question">輸入校規問題</label>
        <div class="input-row">
          <textarea
            id="question"
            v-model="input"
            rows="2"
            maxlength="4000"
            placeholder="例如：教師請假有哪些限制與應備文件？"
            @keydown.ctrl.enter="submit"
          ></textarea>
          <button type="submit" :disabled="!input.trim() || loading">送出</button>
        </div>
        <small>Ctrl + Enter 送出｜AI 回答可能有誤，請以官方最新法規為準。</small>
      </form>
    </main>
  </div>
</template>

