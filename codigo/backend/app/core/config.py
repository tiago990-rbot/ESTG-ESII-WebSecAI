import os
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)

def value(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

def number(name: str, default: int) -> int:
    return max(0, int(value(name, str(default))))

def token_secret() -> str:
    secret = value("JWT_SECRET")
    if len(secret) < 32 or secret.startswith("websec-check-local"):
        raise RuntimeError("JWT_SECRET ausente/inseguro. Execute python scripts/setup_local.py.")
    return secret
