"""Echo service package exports the ASGI `app` for convenience.

This lets you run: `uvicorn echo_service:app`
"""
from echo_service.main import app

__all__ = ["app"]
