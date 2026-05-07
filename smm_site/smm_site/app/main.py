"""Compatibility module exposing the ASGI `app` object at
`smm_site.app.main:app` by importing it from the existing `app.main`.
"""
from smm_site.app.routes.site import router as site_router  # re-export the FastAPI/ASGI app

__all__ = ["app"]
