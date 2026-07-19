import { ChatPanel } from './components/ChatPanel'

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 px-4 py-3 sm:px-6 dark:border-slate-800">
        <h1 className="text-base font-semibold sm:text-lg">Industrial Knowledge Intelligence</h1>
        <p className="text-xs text-slate-500 sm:text-sm dark:text-slate-400">
          Expert Knowledge Copilot
        </p>
      </header>

      <main className="flex min-w-0 flex-1 justify-center overflow-hidden">
        <ChatPanel />
      </main>
    </div>
  )
}

export default App
