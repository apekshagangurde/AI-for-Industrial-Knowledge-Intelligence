"""Single entry point for LLM calls: Groq by default, Ollama fallback.

Every other backend module should call `complete()` instead of talking to
Groq or Ollama directly, so the provider can be swapped (or the demo run
offline) without touching ingestion/RAG code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


def complete(prompt: str, system: str | None = None) -> str:
    """Return a single text completion for `prompt`.

    Uses Groq when GROQ_API_KEY is set, otherwise falls back to a local
    Ollama server. Both paths return a plain string.
    """
    if GROQ_API_KEY:
        return _complete_groq(prompt, system)
    return _complete_ollama(prompt, system)


def _messages(prompt: str, system: str | None) -> list[dict]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _complete_groq(prompt: str, system: str | None) -> str:
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=_messages(prompt, system),
    )
    return response.choices[0].message.content


def _complete_ollama(prompt: str, system: str | None) -> str:
    import ollama

    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.chat(model=OLLAMA_MODEL, messages=_messages(prompt, system))
    return response["message"]["content"]
