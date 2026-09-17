"""Browser front-end for py2048. The engine stays authoritative."""

from .app import app, create_app

__all__ = ["app", "create_app"]
