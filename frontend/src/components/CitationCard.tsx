import { useState } from 'react'
import type { Citation } from '../types/chat'

function confidenceColor(score: number): string {
  if (score >= 0.75) return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
  if (score >= 0.5) return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
  return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
}

export function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <button
      type="button"
      onClick={() => setExpanded((prev) => !prev)}
      className="w-full max-w-xs rounded-lg border border-slate-200 bg-white p-2 text-left text-xs shadow-sm transition hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate font-medium text-slate-700 dark:text-slate-200">
          {citation.doc_name}
        </span>
        <span
          className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${confidenceColor(citation.score)}`}
        >
          {Math.round(citation.score * 100)}%
        </span>
      </div>
      <div className="mt-0.5 text-slate-400 dark:text-slate-500">page {citation.page}</div>
      <p className={`mt-1 text-slate-500 dark:text-slate-400 ${expanded ? '' : 'line-clamp-2'}`}>
        {citation.snippet}
      </p>
    </button>
  )
}
