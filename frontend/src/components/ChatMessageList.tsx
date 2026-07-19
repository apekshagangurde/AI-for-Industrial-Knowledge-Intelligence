import type { ChatMessage } from '../types/chat'
import { CitationCard } from './CitationCard'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
}

export function ChatMessageList({ messages, isLoading }: Props) {
  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      {messages.length === 0 && !isLoading && (
        <p className="m-auto text-sm text-slate-400 dark:text-slate-500">
          Ask a question about the document corpus to get started.
        </p>
      )}
      {messages.map((message) => (
        <div key={message.id} className={message.role === 'user' ? 'ml-auto' : 'mr-auto'}>
          <div
            className={`max-w-[85%] break-words rounded-2xl px-4 py-2 text-sm sm:max-w-[75%] ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : message.role === 'error'
                  ? 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
                  : 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
            }`}
          >
            {message.content}
          </div>
          {message.citations && message.citations.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {message.citations.map((citation) => (
                <CitationCard key={citation.chunk_id} citation={citation} />
              ))}
            </div>
          )}
        </div>
      ))}
      {isLoading && (
        <div className="mr-auto max-w-[85%] rounded-2xl bg-slate-100 px-4 py-2 text-sm text-slate-400 sm:max-w-[75%] dark:bg-slate-800 dark:text-slate-500">
          Thinking…
        </div>
      )}
    </div>
  )
}
