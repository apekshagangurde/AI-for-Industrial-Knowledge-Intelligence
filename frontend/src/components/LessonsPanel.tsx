import { useState } from 'react'
import { fetchSimilarIncidents, type LessonsResponse } from '../lib/api'

export function LessonsPanel() {
  const [docId, setDocId] = useState('')
  const [data, setData] = useState<LessonsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!docId.trim()) return
    setLoading(true)
    setError(null)
    try {
      setData(await fetchSimilarIncidents(docId.trim()))
    } catch {
      setError("Couldn't reach the knowledge base. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 p-4 sm:p-6">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Lessons learned — given an incident document, surfaces the most similar
        past incidents so recurring failure patterns don't get rediscovered.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={docId}
          onChange={(e) => setDocId(e.target.value)}
          placeholder="incident doc_id (filename without extension)"
          className="min-h-11 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
        <button
          type="button"
          onClick={run}
          disabled={loading || !docId.trim()}
          className="min-h-11 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {loading ? 'Searching…' : 'Find similar'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {data && data.error && (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          {data.error}
        </div>
      )}

      {data && !data.error && (
        <div className="space-y-2">
          {data.matches.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">No similar past incidents above threshold.</p>
          )}
          {data.matches.map((m) => (
            <div
              key={m.doc_id}
              className="rounded-lg border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="truncate font-medium text-slate-700 dark:text-slate-200">{m.title}</span>
                <span className="shrink-0 rounded-full bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                  {Math.round(m.similarity * 100)}% similar
                </span>
              </div>
              <p className="break-words text-slate-500 dark:text-slate-400">{m.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
