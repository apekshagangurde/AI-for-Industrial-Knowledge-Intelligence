"""Turn retrieved chunks (retriever.retrieve output) into a grounded, cited answer."""
from __future__ import annotations

import re

from common.llm_client import complete

SYSTEM_PROMPT = (
    "You are an industrial knowledge assistant. Answer only using the numbered context "
    "entries provided. If the context doesn't contain the answer, say so plainly instead "
    "of guessing. Cite every claim inline using the matching [n] marker from the context."
)


def _build_context(chunks: list[dict]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.get("title", chunk["doc_id"])
        blocks.append(f"[{i}] ({title}, page {chunk['page']}):\n{chunk['text']}")
    return "\n\n".join(blocks)


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """Returns {"answer": str, "citations": list[dict]}."""
    if not chunks:
        answer = complete(
            f"No matching internal documents were found for this question: {question!r}. "
            "Say plainly that nothing relevant was found in the knowledge base, without "
            "inventing an answer."
        )
        return {"answer": answer, "citations": []}

    context = _build_context(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = complete(prompt, system=SYSTEM_PROMPT)

    cited_indices = sorted(
        {n for n in (int(m) for m in re.findall(r"\[(\d+)\]", answer)) if 1 <= n <= len(chunks)}
    )
    if not cited_indices:
        # Model didn't cite explicitly — fall back to everything it was shown.
        cited_indices = list(range(1, len(chunks) + 1))

    citations = [
        {
            "doc_name": chunks[i - 1].get("title", chunks[i - 1]["doc_id"]),
            "page": chunks[i - 1]["page"],
            "snippet": chunks[i - 1]["text"][:280],
            "chunk_id": chunks[i - 1]["chunk_id"],
            "score": chunks[i - 1].get("score", 0.0),
        }
        for i in cited_indices
    ]
    return {"answer": answer, "citations": citations}
