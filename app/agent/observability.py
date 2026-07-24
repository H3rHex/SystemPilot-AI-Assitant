from __future__ import annotations

from app.agent.config import USE_LANGFUSE

if USE_LANGFUSE:
    from langfuse import observe
else:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
