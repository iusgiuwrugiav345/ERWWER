"""smm_site.app namespace package that proxies the real `app` package.
This file exists so `import smm_site.app` works alongside the existing `app` package.
"""

from importlib import import_module
import sys

try:
    # If the real `app` package is importable, ensure it's available under
    # the name `smm_site.app` in sys.modules so submodule imports work.
    app_pkg = import_module("app")
    sys.modules.setdefault("smm_site.app", app_pkg)
except Exception:
    # If import fails, don't crash at import time — allow later import errors
    # to show the original cause.
    pass
