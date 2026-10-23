"""One isolated official query. Never display configuration, headers or raw bodies."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import ROOT, value
from app.services import providers


def validate():
    configured = bool(value("URLHAUS_AUTH_KEY"))
    summary = {"utc": datetime.now(timezone.utc).isoformat(), "configured": configured,
               "requests_this_run": 0, "authenticated": False, "results_count": 0}
    if not configured:
        return dict(summary, status="not_configured", message="Chave ausente; nenhuma consulta efetuada.")
    # A private ledger persists across runs; reserve before the request, never retry.
    ledger = ROOT / ".cache" / "urlhaus-validation"
    ledger.mkdir(parents=True, exist_ok=True)
    for slot in (1, 2):
        try:
            with (ledger / f"attempt-{slot}").open("x", encoding="utf-8") as file:
                file.write(summary["utc"])
            break
        except FileExistsError:
            continue
    else:
        return dict(summary, status="limit_reached", message="Duas tentativas já reservadas; não repetir.")
    original = providers.json_request
    accepted = False

    def official_only(method, url, **kwargs):
        nonlocal accepted
        if method != "POST" or url != "https://urlhaus-api.abuse.ch/v1/host/" or summary["requests_this_run"]:
            raise providers.SourceError("error", "Pedido fora do teste isolado bloqueado.")
        summary["requests_this_run"] += 1
        payload = original(method, url, **kwargs)
        accepted = isinstance(payload, dict) and payload.get("query_status") in {"ok", "no_results"}
        return payload

    providers.json_request = official_only
    try:
        result = providers.guarded(providers.urlhaus, "https://example.com/")
    finally:
        providers.json_request = original
    summary.update(status=result.status, message=result.message, results_count=len(result.evidence),
                   authenticated=accepted, query_type="host", indicator="example.com", attempt=slot)
    if result.status == "no_results" and not accepted:
        summary.update(status="unvalidated_response", message="A resposta não comprovou autenticação; não interpretar como ausência de correspondências.")
    (ledger / f"result-{slot}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), ensure_ascii=True))
    except Exception:
        print(json.dumps({"status": "error", "message": "Validação interrompida; reveja a configuração privadamente. Não repetir automaticamente."}))
        sys.exit(1)
