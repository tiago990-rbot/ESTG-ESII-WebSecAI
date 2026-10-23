from datetime import timedelta
import hashlib
import secrets
import pytest
from fastapi import HTTPException
from app.core import security

def test_new_and_legacy_hashes():
    password = secrets.token_urlsafe(15)
    current = security.hash_password(password)
    assert security.verify_password(password, current)
    assert not security.verify_password(password + "x", current)
    salt = secrets.token_bytes(16)
    legacy = "$".join(["pbkdf2_sha256", security._b64(salt), security._b64(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000))])
    assert security.verify_password(password, legacy)

def test_tokens_expiry_tamper_and_subject():
    token = security.create_access_token("123")
    assert security.decode_access_token(token)["sub"] == "123"
    for invalid in [token + "x", "not-a-token", security.create_access_token("123", timedelta(seconds=-10)), security.create_access_token("bad-subject")]:
        with pytest.raises(HTTPException):
            security.decode_access_token(invalid)

def test_missing_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "")
    with pytest.raises(RuntimeError):
        security.create_access_token("1")
