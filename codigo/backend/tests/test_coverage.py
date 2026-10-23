import json
from datetime import datetime, timedelta, timezone
import pytest
from app.services import ai_service, providers
from app.services.coverage import summarize_coverage
from app.services.investigation_service import retryable_sources
from app.models.investigation import Investigation


@pytest.mark.parametrize("case_id", ["no_matches", "homonym"])
def test_unassociated_inputs_explain_coverage_without_model_or_quota(monkeypatch, case_id):
    from evaluations.cases import cases
    case = next(c for c in cases() if c["id"] == case_id)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.setattr(providers, "reserve", lambda *a, **k: pytest.fail("No quota should be reserved"))
    with pytest.raises(providers.SourceError) as exc:
        ai_service.generate(case["evidence"], case["target"], case["runs"])
    assert exc.value.status == "no_results"
    coverage = summarize_coverage(case["evidence"], case["runs"])
    assert coverage["origin"] == "local_rules" and not coverage["has_target_evidence"]
    assert any("Não há evidências" in note for note in coverage["notes"])


def test_empty_evidence_references_are_still_rejected():
    raw = {"summary":"Resumo", "observations":[{"text":"Afirmação", "evidence_ids":[]}], "recommendations":[], "limitations":["Cobertura limitada"]}
    with pytest.raises(ValueError):
        ai_service.validated_report(raw, [{"id":"one"}])


def test_ai_can_be_started_after_new_relevant_evidence_arrives():
    inv = Investigation(id="test", target="https://example.com/", domain="example.com", kind="domain", is_demo=False, status="partial", options={})
    runs = [{"provider":"ai", "status":"no_results"}]
    assert "ai" not in retryable_sources(inv, [{"id":"general", "category":"kev_general"}], runs, [])
    assert "ai" in retryable_sources(inv, [{"id":"direct", "category":"incident_report", "meta":{"relevance":"candidate_match"}}], runs, [])


def test_request_window_caps_requests_atomically_and_cannot_expand_limit(monkeypatch, tmp_path):
    from app.core.request_window import restricted_limit
    period = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = tmp_path / "window.json"
    path.write_text(json.dumps({"deadline_utc":(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(), "limits":{"groq":2}, "baseline":[]}),encoding="utf-8")
    assert restricted_limit(str(path), "groq", period, 1) == 1
    monkeypatch.setenv("WEBSECAI_REQUEST_WINDOW_FILE", str(path))
    providers.reserve("groq", 40, daily=True)
    providers.reserve("groq", 40, daily=True)
    with pytest.raises(providers.SourceError):
        providers.reserve("groq", 40, daily=True)
    path.write_text('{"deadline_utc":"2020-01-01T00:00:00+00:00","limits":{},"baseline":[]}',encoding="utf-8")
    with pytest.raises(providers.SourceError):
        providers.reserve("groq", 40, daily=True)


def test_optional_urlhaus_key_preserves_private_settings(tmp_path):
    from app.core.local_setup import save_provider_keys
    path = tmp_path / ".env"
    path.write_text("JWT_SECRET=preserve\nTAVILY_API_KEY=preserve\nGROQ_API_KEY=preserve\n",encoding="utf-8")
    saved = save_provider_keys(path,{"URLHAUS_AUTH_KEY":"synthetic-urlhaus-123456789"})
    assert saved == ["URLHAUS_AUTH_KEY"]
    assert "JWT_SECRET=preserve" in path.read_text() and "GROQ_API_KEY=preserve" in path.read_text()


@pytest.mark.parametrize("message", [None, "Página de informação: https://example.com/"])
def test_no_match_flow_keeps_evidence_and_pdf_without_llm(client, accounts, monkeypatch, message):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("no_results", "Sem referências nesta consulta"))
    payload = {"target":"example.com"} if message is None else {"kind":"message", "message":message}
    response = client.post("/api/v1/investigations",json=payload,headers=accounts[0])
    assert response.status_code == 202
    path = "/api/v1/investigations/" + response.json()["id"]
    snapshot = client.get(path,headers=accounts[0]).json()
    assert snapshot["evidence"] and not snapshot["reports"]
    assert not snapshot["coverage_summary"]["has_target_evidence"]
    assert next(r for r in snapshot["runs"] if r["provider"] == "ai")["status"] == "no_results"
    assert client.get(path+"/report",headers=accounts[0]).content.startswith(b"%PDF")
    assert client.post(path+"/questions",json={"text":"Isto é seguro?"},headers=accounts[0]).status_code == 409
