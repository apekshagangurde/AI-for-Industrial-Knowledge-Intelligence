import { useState } from 'react'
import type { FormEvent } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 border-t border-slate-200 p-3 dark:border-slate-800"
    >
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask about equipment, procedures, incidents…"
        disabled={disabled}
        className="min-h-11 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 outline-none focus:border-blue-500 disabled:opacity-50 sm:text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="min-h-11 min-w-11 shrink-0 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        Send
      </button>
    </form>
  )
}
