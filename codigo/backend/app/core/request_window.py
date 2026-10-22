"""Optional, restrictive request budget for a human-authorized work window."""
from datetime import datetime, timezone
import json
from pathlib import Path


def restricted_limit(path, provider, period, normal_limit):
    if not path or provider not in {"tavily", "groq"}:
        return normal_limit
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    deadline = datetime.fromisoformat(data["deadline_utc"])
    if deadline.tzinfo is None or datetime.now(timezone.utc) >= deadline:
        raise ValueError("Closed request window")
    allowance = data["limits"][provider]
    baseline = next((row["count"] for row in data["baseline"] if row["provider"] == provider and row["period"] == period), 0)
    if type(allowance) is not int or type(baseline) is not int or allowance < 0 or baseline < 0:
        raise ValueError("Invalid request window")
    # The authorization can only restrict an existing application limit.
    return min(normal_limit, baseline + allowance)
