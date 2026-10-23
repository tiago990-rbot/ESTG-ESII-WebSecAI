"""Private GUI handoff through stdin; never accept a credential in command arguments."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.local_setup import save_provider_keys


def main():
    try:
        payload = sys.stdin.read(8193)
        if len(payload) > 8192:
            raise ValueError("Pedido de configuração demasiado grande.")
        save_provider_keys(ROOT / ".env", json.loads(payload))
        print(json.dumps({"saved": True}))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError):
        print(json.dumps({"saved": False, "message": "Não foi possível guardar. Confirma as chaves, fecha outras edições e tenta novamente."}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
