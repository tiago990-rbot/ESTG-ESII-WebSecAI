"""Fail closed for the shared academic installation; no replacement auth system."""
import hashlib
import threading
import time
from collections import deque
from fastapi import HTTPException
from app.core.config import value


def production():
    return value("APP_ENV", "local") == "production"


def allowed_emails():
    return {email.strip().lower() for email in value("APP_ALLOWED_EMAILS").split(",") if email.strip()}


def check_member(email):
    if production() and email.strip().lower() not in allowed_emails():
        raise HTTPException(403, "Acesso restrito aos elementos autorizados do grupo.")


def validate_deployment():
    if not production():
        return
    from app.db.configuration import database_url, migration_url
    from urllib.parse import urlsplit
    if database_url().get_backend_name() != "postgresql":
        raise RuntimeError("A instalação online exige PostgreSQL persistente.")
    migration_url()
    if len(allowed_emails()) != 3:
        raise RuntimeError("Configure os três emails autorizados em APP_ALLOWED_EMAILS.")
    origins = [x.strip() for x in value("CORS_ORIGINS").split(",")]
    if not origins or any(urlsplit(x).scheme != "https" or not urlsplit(x).hostname or urlsplit(x).path not in {"", "/"} or "*" in x for x in origins):
        raise RuntimeError("Configure CORS_ORIGINS com a origem HTTPS exata da interface.")


_lock = threading.Lock()
_attempts = {}


def auth_attempt(ip, identifier):
    if not production():
        return
    now = time.monotonic()
    # One process, bounded memory. Proxy headers are not trusted here.
    keys = [("ip", ip), ("identity", identifier.strip().lower())]
    with _lock:
        for key in list(_attempts):
            if not _attempts[key] or _attempts[key][-1] <= now - 300:
                del _attempts[key]
        digests = [hashlib.sha256(repr(k).encode()).digest() for k in keys]
        if len(_attempts) + 2 > 4096:
            raise HTTPException(429, "Muitas tentativas de acesso. Aguarde.", headers={"Retry-After": "300"})
        for key, limit in zip(digests, [30, 10]):
            entries = _attempts.setdefault(key, deque())
            while entries and entries[0] <= now - 300:
                entries.popleft()
            if len(entries) >= limit:
                raise HTTPException(429, "Muitas tentativas de acesso. Aguarde.", headers={"Retry-After": "300"})
        for key in digests:
            _attempts[key].append(now)
