import { API_BASE_URL } from './config'

export interface QueryResponse {
  answer: string
  citations: unknown[]
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
