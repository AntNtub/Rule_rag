export type Mode = 'search' | 'explain' | 'draft'

export interface Source {
  citation_id: string
  document_id: string
  chunk_id: string
  title: string
  section_id: string | null
  issued_at: string | null
  source_url: string | null
  content: string
  distance: number | null
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  warning?: string
}

export interface Conversation {
  id: string
  title: string
  mode: Mode
  messages: Message[]
  updatedAt: string
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  grounded: boolean
  warnings: string[]
}

