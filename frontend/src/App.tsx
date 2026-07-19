import { ChatPanel } from './components/ChatPanel'

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h1 className="text-lg font-semibold">Industrial Knowledge Intelligence</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Expert Knowledge Copilot
        </p>
      </header>

      <main className="flex flex-1 justify-center overflow-hidden">
        <ChatPanel />
      </main>
    </div>
  )
}

export default App
