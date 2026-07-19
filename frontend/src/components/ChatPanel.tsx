import { useState } from 'react'
import type { ChatMessage } from '../types/chat'
import { queryKnowledgeBase } from '../lib/api'
import { ChatMessageList } from './ChatMessageList'
import { ChatInput } from './ChatInput'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async (text: string) => {
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await queryKnowledgeBase(text)
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        confidence: response.confidence,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'error',
        content: "Couldn't reach the knowledge base. Check that the backend is running and try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-1 flex-col">
      <ChatMessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}
