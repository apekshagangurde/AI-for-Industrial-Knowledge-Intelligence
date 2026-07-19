export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
}
