"""Print only allowlisted connection metadata. --live never searches or generates."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.integration_check import check_connections

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Valida autenticação por metadados: Tavily /usage e Groq /models.")
    args = parser.parse_args()
    print(json.dumps(check_connections(args.live), ensure_ascii=False, indent=2))
