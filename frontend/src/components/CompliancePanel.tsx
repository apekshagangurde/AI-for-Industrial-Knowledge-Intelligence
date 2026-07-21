import { useState } from 'react'
import { checkCompliance, type ComplianceResponse } from '../lib/api'

const SEVERITY_COLOR: Record<string, string> = {
  high: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  low: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
}

export function CompliancePanel() {
  const [procedureId, setProcedureId] = useState('')
  const [regulationId, setRegulationId] = useState('')
  const [data, setData] = useState<ComplianceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!procedureId.trim() || !regulationId.trim()) return
    setLoading(true)
    setError(null)
    try {
      setData(await checkCompliance(procedureId.trim(), regulationId.trim()))
    } catch {
      setError("Couldn't reach the knowledge base. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 p-4 sm:p-6">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Compliance check — compares a procedure against a regulation and flags
        gaps. Enter the document IDs (the filename without extension).
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        <input
          value={procedureId}
          onChange={(e) => setProcedureId(e.target.value)}
          placeholder="procedure_id e.g. 2023-02-15_centrifugal-pump-operation"
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
        <input
          value={regulationId}
          onChange={(e) => setRegulationId(e.target.value)}
          placeholder="regulation_id e.g. osha_process_safety_management"
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
      </div>
      <button
        type="button"
        onClick={run}
        disabled={loading || !procedureId.trim() || !regulationId.trim()}
        className="min-h-11 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
      >
        {loading ? 'Checking…' : 'Check compliance'}
      </button>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                data.compliant === true
                  ? 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
                  : data.compliant === false
                    ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {data.compliant === true ? 'Compliant' : data.compliant === false ? 'Gaps found' : 'Inconclusive'}
            </span>
            <span className="text-xs text-slate-400">
              {data.gaps.length} gap{data.gaps.length === 1 ? '' : 's'}
            </span>
          </div>

          {data.summary && (
            <p className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{data.summary}</p>
          )}

          <ul className="space-y-2">
            {data.gaps.map((g, i) => (
              <li
                key={i}
                className="rounded-lg border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${SEVERITY_COLOR[g.severity] ?? SEVERITY_COLOR.low}`}>
                    {g.severity}
                  </span>
                  <span className="font-medium text-slate-700 dark:text-slate-200">{g.requirement}</span>
                </div>
                <p className="text-slate-500 dark:text-slate-400">{g.finding}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
