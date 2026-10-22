"""Metadata-only checks: no searches, generation, or raw account/key output."""
from app.core.config import value
from app.services import providers


def check_connections(live=False):
    result = {"mode": "read_only" if live else "local", "analysis_performed": False, "checks": {}}
    for name, variable in (("tavily", "TAVILY_API_KEY"), ("groq", "GROQ_API_KEY"), ("urlhaus", "URLHAUS_AUTH_KEY")):
        key = value(variable)
        if not key:
            check = {"status": "not_configured"}
        elif not live or name == "urlhaus":
            check = {"status": "configured_not_validated"}
        else:
            try:
                headers = {"Authorization": "Bearer " + key}
                if name == "tavily":
                    data = providers.json_request("GET", "https://api.tavily.com/usage", headers=headers)
                    account = data.get("account")
                    if not isinstance(account, dict):
                        raise ValueError("Invalid metadata")
                    plan = str(account.get("current_plan", "")).lower()
                    check = {"status": "authenticated", "free_plan_confirmed": plan in {"free", "researcher"} and account.get("paygo_limit") == 0}
                else:
                    data = providers.json_request("GET", "https://api.groq.com/openai/v1/models", headers=headers)
                    models = data.get("data")
                    if not isinstance(models, list):
                        raise ValueError("Invalid metadata")
                    available = any(isinstance(m, dict) and m.get("id") == value("GROQ_MODEL", "qwen/qwen3.8-27b") for m in models)
                    check = {"status": "authenticated", "model_available": available, "free_plan_confirmed": None}
            except providers.SourceError as exc:
                check = {"status": exc.status}
            except Exception:
                check = {"status": "error"}
        result["checks"][name] = check
    return result
