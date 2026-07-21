"""Optional Langfuse tracing, wrapped so the rest of the code never has to care
whether it's enabled.

`@observe(...)` decorates any function to record a trace span (latency, inputs,
outputs, token usage where the provider reports it). When Langfuse isn't
installed or `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` aren't set, `observe`
returns the function unchanged — zero overhead, no crash, no config required.
"""
from __future__ import annotations

import os
from functools import wraps

_LANGFUSE_ENABLED = bool(
    os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    and os.getenv("LANGFUSE_SECRET_KEY", "").strip()
)

_langfuse_observe = None
if _LANGFUSE_ENABLED:
    try:
        from langfuse.decorators import observe as _langfuse_observe  # type: ignore
    except Exception:  # package missing or import error -> silently disable
        _langfuse_observe = None


def observe(name: str | None = None, **decorator_kwargs):
    """Decorator factory. Delegates to Langfuse's @observe when tracing is on,
    otherwise returns the function untouched."""

    def decorator(func):
        if _langfuse_observe is not None:
            return _langfuse_observe(name=name, **decorator_kwargs)(func)

        @wraps(func)
        def passthrough(*args, **kwargs):
            return func(*args, **kwargs)

        return passthrough

    return decorator


def tracing_enabled() -> bool:
    return _langfuse_observe is not None
