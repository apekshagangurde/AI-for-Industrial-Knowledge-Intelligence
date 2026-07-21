import { useState } from 'react'
import { fetchGraph, type GraphResponse } from '../lib/api'
import { EQUIPMENT } from '../lib/plant'

const WIDTH = 720
const HEIGHT = 460

interface Positioned {
  id: string
  name: string
  type: string
  color: string
  x: number
  y: number
}

function layout(data: GraphResponse): Positioned[] {
  const cx = WIDTH / 2
  const cy = HEIGHT / 2
  const others = data.nodes.filter((n) => n.id !== data.center)
  const radius = Math.min(WIDTH, HEIGHT) / 2 - 70
  return data.nodes.map((n) => {
    if (n.id === data.center) return { ...n, x: cx, y: cy }
    const i = others.findIndex((o) => o.id === n.id)
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1)
    return { ...n, x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }
  })
}

export function GraphPanel() {
  const [tag, setTag] = useState(EQUIPMENT[0].tag)
  const [data, setData] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchGraph(tag))
    } catch {
      setError("Couldn't reach the knowledge base. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  const positioned = data ? layout(data) : []
  const posById = new Map(positioned.map((p) => [p.id, p]))
  const types = Array.from(new Set(positioned.map((p) => [p.type, p.color] as const).map((t) => t.join('|'))))

  return (
    <div className="mx-auto w-full max-w-4xl space-y-4 p-4 sm:p-6">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Knowledge graph — the neighborhood of one asset: the documents,
        incidents, regulations and people the platform has linked to it.
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
          {loading ? 'Loading…' : 'Show graph'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {data && positioned.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          No graph found for {data.center}. Has the graph writer been run for this asset?
        </p>
      )}

      {data && positioned.length > 0 && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
            <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full" role="img" aria-label={`Graph for ${data.center}`}>
              {data.links.map((l, i) => {
                const s = posById.get(l.source)
                const t = posById.get(l.target)
                if (!s || !t) return null
                return (
                  <g key={i}>
                    <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#cbd5e1" strokeWidth={1} />
                  </g>
                )
              })}
              {positioned.map((n) => (
                <g key={n.id}>
                  <circle cx={n.x} cy={n.y} r={n.id === data.center ? 22 : 14} fill={n.color}>
                    <title>{`${n.type}: ${n.name}`}</title>
                  </circle>
                  <text
                    x={n.x}
                    y={n.y + (n.id === data.center ? 36 : 26)}
                    textAnchor="middle"
                    className="fill-slate-600 text-[10px] dark:fill-slate-300"
                  >
                    {n.name.length > 22 ? `${n.name.slice(0, 20)}…` : n.name}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
            {types.map((t) => {
              const [type, color] = t.split('|')
              return (
                <span key={t} className="flex items-center gap-1">
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {type}
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
