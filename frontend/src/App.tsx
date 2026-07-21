import { useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { RcaPanel } from './components/RcaPanel'
import { CompliancePanel } from './components/CompliancePanel'
import { LessonsPanel } from './components/LessonsPanel'
import { GraphPanel } from './components/GraphPanel'

const TABS = [
  { id: 'copilot', label: 'Copilot' },
  { id: 'rca', label: 'RCA' },
  { id: 'compliance', label: 'Compliance' },
  { id: 'lessons', label: 'Lessons' },
  { id: 'graph', label: 'Graph' },
] as const

type TabId = (typeof TABS)[number]['id']

function App() {
  const [tab, setTab] = useState<TabId>('copilot')

  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 px-4 py-3 sm:px-6 dark:border-slate-800">
        <h1 className="text-base font-semibold sm:text-lg">Industrial Knowledge Intelligence</h1>
        <p className="text-xs text-slate-500 sm:text-sm dark:text-slate-400">
          Expert Knowledge Copilot
        </p>
        <nav className="mt-2 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`min-h-9 shrink-0 rounded-full px-3 py-1 text-sm font-medium transition ${
                tab === t.id
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                  : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        {tab === 'copilot' ? (
          <div className="flex min-h-0 flex-1 justify-center overflow-hidden">
            <ChatPanel />
          </div>
        ) : (
          <div className="min-h-0 flex-1 overflow-y-auto">
            {tab === 'rca' && <RcaPanel />}
            {tab === 'compliance' && <CompliancePanel />}
            {tab === 'lessons' && <LessonsPanel />}
            {tab === 'graph' && <GraphPanel />}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
