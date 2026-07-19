import { API_BASE_URL } from './config'
import type { Citation } from '../types/chat'

export interface QueryResponse {
  answer: string
  citations: Citation[]
  confidence: number
}

export async function queryKnowledgeBase(question: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  })
  if (!response.ok) {
    throw new Error(`Query failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}
