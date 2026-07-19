# Frontend

React + TypeScript + Vite + Tailwind CSS. Chat UI for the Expert Knowledge Copilot.

## Dev

```bash
npm install
npm run dev
```

Reads `VITE_API_BASE_URL` from the repo-root `.env` (see `vite.config.ts` `envDir`) — copy
`../.env.example` to `../.env` first if you haven't already.

## Structure

- `src/App.tsx` — top-level layout shell
- `src/lib/config.ts` — env-driven config (API base URL)
- Chat UI, citation cards, and graph viz land in issues #22, #23, #26
