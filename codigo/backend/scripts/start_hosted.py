"""Single-process CPython hosting entry point; provider selected by the group."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn

if __name__ == "__main__":
    # No forwarded-header trust: the login budget remains conservative behind a proxy.
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),
                workers=1, proxy_headers=False, access_log=False, timeout_graceful_shutdown=90)
