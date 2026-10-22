"""Create configuration without printing or overwriting credentials."""
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
target = root / ".env"
if not target.exists():
    example = (root / ".env.example").read_text(encoding="utf-8")
    target.write_text(example.replace("JWT_SECRET=\n", "JWT_SECRET=" + secrets.token_urlsafe(48) + "\n", 1), encoding="utf-8")
    print("Configuração local criada. As chaves externas podem ser editadas em backend/.env.")
else:
    print("Configuração existente preservada.")
