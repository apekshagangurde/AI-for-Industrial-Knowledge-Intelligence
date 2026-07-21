"""Single entry point for LLM calls: LiteLLM gateway by default, with the raw
Groq/Ollama SDKs as a fallback when LiteLLM isn't installed or is disabled.

Every other backend module calls `complete()` (and, new here, `complete_json()`
/ `vision_complete()`), so the provider, fallback chain, retries, and tracing
are all configured in one place. Behavior is backward compatible: with
`USE_LITELLM` unset it behaves exactly like the original groq-or-ollama client.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from common.observability import observe

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

USE_LITELLM = os.getenv("USE_LITELLM", "").strip().lower() in ("1", "true", "yes")
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")
LITELLM_FALLBACK_MODEL = os.getenv("LITELLM_FALLBACK_MODEL", "ollama/llama3.1:8b")


def _messages(prompt: str, system: str | None) -> list[dict]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


@observe(name="llm.complete")
def complete(prompt: str, system: str | None = None) -> str:
    """Return a single text completion for `prompt`.

    Routes through LiteLLM (with a primary->fallback chain + retries) when
    USE_LITELLM is set and the package is importable; otherwise uses the
    original direct Groq-or-Ollama path.
    """
    if USE_LITELLM:
        try:
            return _complete_litellm(_messages(prompt, system))
        except ImportError:
            pass  # litellm not installed -> fall through to the raw SDK path
    if GROQ_API_KEY:
        return _complete_groq(prompt, system)
    return _complete_ollama(prompt, system)


@observe(name="llm.complete_json")
def complete_json(prompt: str, system: str | None = None) -> str:
    """Same as complete(), but asks the provider for JSON output when supported.

    Falls back to a plain completion if the provider/model doesn't support a
    JSON response format. Callers must still defensively parse the result.
    """
    if USE_LITELLM:
        try:
            return _complete_litellm(
                _messages(prompt, system),
                response_format={"type": "json_object"},
            )
        except ImportError:
            pass
        except Exception:
            # Model rejected response_format — retry without it rather than fail.
            return complete(prompt, system)
    return complete(prompt, system)


@observe(name="llm.vision_complete")
def vision_complete(prompt: str, image_data_url: str, system: str | None = None) -> str:
    """Multimodal completion: send `prompt` plus an image (data: URL or http URL).

    Used by the P&ID extractor (#11). Requires a vision-capable model configured
    via LITELLM_MODEL (e.g. a Groq/Ollama Qwen2-VL or a Claude vision model).
    """
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": image_data_url}},
    ]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    return _complete_litellm(messages)


def _complete_litellm(messages: list[dict], **kwargs) -> str:
    """Primary path: LiteLLM with a declarative fallback chain and retries.

    Raises ImportError if litellm isn't installed so complete() can degrade to
    the raw SDK path.
    """
    import litellm  # raises ImportError -> caller degrades to raw SDK path

    # Quiet, predictable behavior for a demo/server: no telemetry, drop unknown
    # params rather than error on provider quirks.
    litellm.drop_params = True
    litellm.telemetry = False

    response = litellm.completion(
        model=LITELLM_MODEL,
        messages=messages,
        num_retries=2,
        fallbacks=[LITELLM_FALLBACK_MODEL] if LITELLM_FALLBACK_MODEL else None,
        **kwargs,
    )
    return response["choices"][0]["message"]["content"]


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
