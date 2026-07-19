#!/usr/bin/env python3
"""Smoke test for the LLM client: `python backend/scripts/llm_smoke_test.py "your prompt"`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.llm_client import GROQ_API_KEY, complete


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "Say hello in one short sentence."
    provider = "Groq" if GROQ_API_KEY else "Ollama"
    print(f"Provider: {provider}")
    print(f"Prompt:   {prompt}")
    response = complete(prompt)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
