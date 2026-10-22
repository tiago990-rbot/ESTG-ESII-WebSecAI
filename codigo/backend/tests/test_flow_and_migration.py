import json
from types import SimpleNamespace
from sqlalchemy import inspect
from app.db.base import Base
from app.db.migrate import upgrade_schema
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.services import providers
from app.services.investigation_pdf import investigation_pdf

def test_source_to_ai_protocol_and_questions(client, accounts, monkeypatch):
    for key in ("URLHAUS_AUTH_KEY", "PHISHTANK_API_KEY", "TAVILY_API_KEY", "GROQ_API_KEY"):
        monkeypatch.setenv(key, "synthetic-test-key")
    calls = []
    def external(method, url, **kwargs):
        calls.append(url)
        if "urlhaus-api" in url:
            return {"query_status": "ok", "urls": [{"url_status": "offline", "urlhaus_reference": "https://urlhaus.abuse.ch/url/1/"}]}
        if "phishtank" in url:
            return {"results": {"in_database": False}}
        if "tavily" in url:
            return {"results": [{"title": "Invalid reference", "url": "javascript:alert(1)"}, {"title": "example.com alleged incident", "url": "https://news.example.com/article", "content": "Unverified incident report for example.com."}]}
        if "groq" in url:
            prompt = json.loads(kwargs["json"]["messages"][1]["content"])
            ref = prompt["evidence"][0]["id"]
            report = {"summary": "Resumo de teste com referências.", "observations": [{"text": "Uma evidência foi recolhida.", "evidence_ids": [ref]}], "recommendations": [{"text": "Validar a fonte original.", "evidence_ids": [ref]}], "limitations": ["Resposta de teste, sem avaliação de um modelo real."]}
            return {"choices": [{"message": {"content": json.dumps(report)}}]}
        raise AssertionError(url)
    monkeypatch.setattr(providers, "json_request", external)
    response = client.post("/api/v1/investigations", json={"target": "example.com"}, headers=accounts[0])
    id = response.json()["id"]
    d = client.get("/api/v1/investigations/" + id, headers=accounts[0]).json()
    assert d["reports"] and any(r["provider"] == "ai" and r["status"] == "success" for r in d["runs"])
    assert any(e["confirmation"] == "allegation" for e in d["evidence"])
    assert len([url for url in calls if "tavily" in url]) == 2
    answer = client.post("/api/v1/investigations/" + id + "/questions", json={"text": "Que evidências devo validar?"}, headers=accounts[0])
    assert answer.status_code == 200, answer.text
    assert "synthetic-test-key" not in json.dumps(d)

def test_legacy_scan_flows_remain_usable(client, accounts, monkeypatch):
    import app.services.scan_service as service
    monkeypatch.setattr(service, "run_website_analysis", lambda url: {"url": "https://example.com/", "domain": "example.com", "score": 90, "risk_level": "good", "summary": "Dados controlados", "details": {}, "findings": [{"title": "Teste", "category": "test", "severity": "info", "description": "Sintético", "recommendation": "Sem ação"}]})
    response = client.post("/api/v1/scans", json={"url": "example.com", "authorized": True}, headers=accounts[0])
    assert response.status_code == 200, response.text
    id = response.json()["scan_id"]
    assert client.get(f"/api/v1/scans/{id}", headers=accounts[0]).json()["findings_count"] == 1
    assert client.get(f"/api/v1/scans/{id}", headers=accounts[1]).status_code == 404
    assert client.get(f"/api/v1/scans/{id}/report", headers=accounts[0]).content.startswith(b"%PDF")

def test_migration_preserves_user_and_is_repeatable():
    with SessionLocal() as db:
        db.add(User(username="legacy", email="legacy@example.com", password_hash="synthetic"))
        db.commit()
    upgrade_schema()
    upgrade_schema()
    with SessionLocal() as db:
        assert db.query(User).filter(User.username == "legacy").one().email == "legacy@example.com"
    assert {"investigations", "evidence", "ai_reports", "alembic_version"}.issubset(set(inspect(engine).get_table_names()))

def test_pdf_escapes_external_markup():
    snapshot = {"is_demo": False, "target": "<img src='/private'>", "created_at": "2026-10-21", "status": "partial", "runs": [], "reports": [], "evidence": [{"id": "fixture", "title": "<bad>", "provider": "test", "confirmation": "unverified", "description": "<img src='missing-file'> & text", "published_at": None, "event_at": None, "observed_at": "2026-10-21", "source_url": ""}]}
    assert investigation_pdf(snapshot).startswith(b"%PDF")
