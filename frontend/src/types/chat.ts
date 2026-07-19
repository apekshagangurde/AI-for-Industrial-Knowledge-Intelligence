export interface Citation {
  doc_name: string
  page: number
  snippet: string
  chunk_id: string
  score: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
  citations?: Citation[]
  confidence?: number
}
