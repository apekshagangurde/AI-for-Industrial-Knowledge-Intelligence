# Bug Bash + Error-State Checklist (#34)

Goal: nothing visibly breaks on stage. Run this 20-query pass across every tab,
including deliberate edge/error cases. Fix crashes; confirm graceful empty/error
states (no blank screens, no raw stack traces in the UI).

## Setup
- [ ] Backend running (`/health` OK), index built, graph written.
- [ ] Frontend pointed at the right `VITE_API_BASE_URL`.
- [ ] Backend terminal visible to catch `logger.exception` traces.

## Copilot (7)
- [ ] In-corpus: "Why did P-101 fail?" → cited answer, confidence ~0.7-0.8.
- [ ] Exact code: "What does 29 CFR 1910.119 require?" → hybrid finds it.
- [ ] Semantic: "operating procedure for the centrifugal pump" → SOP cited.
- [ ] Low-evidence asset: "maintenance on HX-401" → answers or says little found.
- [ ] Out-of-corpus: "capital of France?" → refuses, low confidence.
- [ ] Empty input → send blocked / clean 422, no crash.
- [ ] 2000+ char input → clean 422, UI shows a friendly message.

## RCA (3)
- [ ] P-101 → summary + history + citations.
- [ ] Asset with no incidents → "no failure history" message, not a spinner hang.
- [ ] Backend down mid-request → red error bubble, not a blank tab.

## Compliance (4)
- [ ] Valid procedure + regulation → gap list or "compliant".
- [ ] Non-existent procedure_id → "document not found" summary.
- [ ] Both fields empty → button disabled.
- [ ] Malformed IDs → clean handling, no 500 leaking internals.

## Lessons (3)
- [ ] Incident with a known similar past incident → it appears in top-3.
- [ ] doc_id that isn't an incident / not found → `error` message shown.
- [ ] Incident with no similar → "none above threshold" message.

## Graph (3)
- [ ] P-101 → nodes render, legend shows types, labels readable.
- [ ] Asset not in graph yet → "no graph found" note, not an empty SVG.
- [ ] Neo4j stopped → empty graph + graceful note (endpoint returns 503-safe).

## Acceptance
- [ ] 20 queries, zero unhandled errors or blank screens.
- [ ] Every failure path shows human text, never a raw exception.
- [ ] Mobile viewport (#25): tabs scroll, panels usable, no horizontal overflow.
