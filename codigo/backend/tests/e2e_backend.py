"""Test-only ASGI entry point. Refuse external provider calls even if keys exist."""
import os
import secrets
os.environ["APP_ENV"] = "local"
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))
for key in ("URLHAUS_AUTH_KEY", "TAVILY_API_KEY", "GROQ_API_KEY", "PHISHTANK_API_KEY", "HIBP_API_KEY"):
    os.environ[key] = ""
from app.services import providers

def offline(*args, **kwargs):
    raise AssertionError("External provider blocked by the browser test")

providers.json_request = offline
providers.kev_catalog = lambda: ({"vulnerabilities": []}, False, "2026-10-22T00:00:00+00:00")
from app.main import app
