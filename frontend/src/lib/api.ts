export interface QueryResponse {
  answer: string
  citations: unknown[]
  confidence: number
}

// TODO(#24): replace this mock with a real POST to `${API_BASE_URL}/query`
// once the backend endpoint (#19) exists. Keeping the same return shape
// here means ChatPanel won't need to change when it's wired up for real.
export async function queryKnowledgeBase(question: string): Promise<QueryResponse> {
  await new Promise((resolve) => setTimeout(resolve, 700))
  return {
    answer: `(mock response — backend not wired yet) You asked: "${question}"`,
    citations: [],
    confidence: 0,
  }
}
