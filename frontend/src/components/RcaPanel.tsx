import { useState } from 'react'
import { fetchRca, type RcaResponse } from '../lib/api'
import { EQUIPMENT } from '../lib/plant'
import { CitationCard } from './CitationCard'

export function RcaPanel() {
  const [tag, setTag] = useState(EQUIPMENT[0].tag)
  const [data, setData] = useState<RcaResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchRca(tag))
    } catch {
      setError("Couldn't reach the knowledge base. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 p-4 sm:p-6">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Root-Cause Analysis — fuses the knowledge graph's failure history for an
        asset with retrieved evidence, then reasons about likely causes.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          {EQUIPMENT.map((e) => (
            <option key={e.tag} value={e.tag}>
              {e.tag} — {e.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="min-h-11 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-1 flex items-center justify-between">
              <h2 className="font-semibold">Root cause — {data.equipment_tag}</h2>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {Math.round(data.confidence * 100)}% confidence
              </span>
            </div>
            <p className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">
              {data.root_cause_summary}
            </p>
          </div>

          {data.history.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Linked history
              </h3>
              <ul className="space-y-1 text-sm">
                {data.history.map((h) => (
                  <li key={h.doc_id} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] uppercase dark:bg-slate-800">
                      {h.doc_type}
                    </span>
                    <span className="truncate">{h.title}</span>
                    {h.date && <span className="text-slate-400">{h.date}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.citations.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {data.citations.map((c) => (
                <CitationCard key={c.chunk_id} citation={c} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
