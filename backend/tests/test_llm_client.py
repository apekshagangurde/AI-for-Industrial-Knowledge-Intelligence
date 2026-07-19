"""Requires GROQ_API_KEY in .env, or a running Ollama server, to pass."""
from common.llm_client import complete


def test_complete_returns_nonempty_string():
    response = complete("Reply with exactly the word: pong")
    assert isinstance(response, str)
    assert len(response.strip()) > 0


def test_complete_respects_system_prompt():
    response = complete(
        "What is 2+2?",
        system="You only ever answer with a single digit, nothing else.",
    )
    assert isinstance(response, str)
    assert len(response.strip()) > 0
