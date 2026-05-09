"""Compatibility module exposing the ASGI `app` object at
`smm_site.app.main:app` by importing it from the existing `app.main`.
"""
from app.main import app  # re-export the FastAPI/ASGI app

__all__ = ["app"]
