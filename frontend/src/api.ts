import type { ChatResponse, Message, Mode } from './types'

export async function askPolicy(
  question: string,
  mode: Mode,
  messages: Message[],
): Promise<ChatResponse> {
  const history = messages
    .slice(-12)
    .map(({ role, content }) => ({ role, content }))

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, mode, history }),
  })

  if (!response.ok) {
    let detail = '服務目前無法使用，請稍後再試。'
    try {
      const payload = await response.json() as { detail?: string }
      detail = payload.detail ?? detail
    } catch {
      // Keep the safe user-facing fallback.
    }
    throw new Error(detail)
  }
  return response.json() as Promise<ChatResponse>
}

