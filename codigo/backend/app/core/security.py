import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import token_secret
from app.db.session import get_db
from app.models.user import User
security = HTTPBearer(auto_error=False)

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "$".join(["pbkdf2_sha256_v2", "600000", _b64(salt), _b64(digest)])

def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = password_hash.split("$")
        if parts[0] == "pbkdf2_sha256" and len(parts) == 3:
            _, salt, expected = parts
            rounds = 120_000
        elif parts[0] == "pbkdf2_sha256_v2" and len(parts) == 4:
            _, iterations, salt, expected = parts
            rounds = int(iterations)
            if not 120_000 <= rounds <= 1_000_000:
                return False
        else:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), rounds)
        return hmac.compare_digest(actual, _unb64(expected))
    except (ValueError, TypeError):
        return False

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "iat": now, "exp": now + (expires_delta or timedelta(hours=24))}, token_secret(), algorithm="HS256")

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, token_secret(), algorithms=["HS256"], options={"require": ["sub", "exp"]})
        if not str(payload["sub"]).isdigit():
            raise ValueError("Invalid subject")
        return payload
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise HTTPException(401, "Token inválido ou expirado") from exc

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(401, "Autenticação necessária")
    payload = decode_access_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(401, "Utilizador não encontrado")
    from app.core.deployment import check_member
    check_member(user.email)
    return user
