import json
from app.db.session import SessionLocal
from app.models.investigation import Investigation, Evidence, AIReport
from app.services import providers
from app.services.investigation_service import recover_interrupted, persist_result

def create_demo(client, header):
    response = client.post("/api/v1/investigations", json={"demo": True}, headers=header)
    assert response.status_code == 202, response.text
    return response.json()["id"]

def test_full_demo_and_pdf(client, accounts):
    id = create_demo(client, accounts[0])
    data = client.get("/api/v1/investigations/" + id, headers=accounts[0]).json()
    assert data["status"] == "completed" and data["is_demo"]
    assert len(data["evidence"]) == 4
    assert data["reports"][0]["model"] == "demonstracao-sem-LLM"
    assert client.get("/api/v1/investigations/" + id + "/report", headers=accounts[0]).content.startswith(b"%PDF")
    assert client.get("/api/v1/investigations/" + id + "/comparison", headers=accounts[0]).status_code == 200

def test_owner_isolation_all_resources(client, accounts):
    id = create_demo(client, accounts[0])
    path = "/api/v1/investigations/" + id
    for suffix in ["", "/report", "/comparison"]:
        assert client.get(path + suffix, headers=accounts[1]).status_code == 404
    assert client.post(path + "/questions", json={"text": "Explica estes dados"}, headers=accounts[1]).status_code == 404
    assert client.delete(path, headers=accounts[1]).status_code == 404
    assert client.get("/api/v1/investigations", headers=accounts[1]).json() == []

def test_removal_cascades(client, accounts):
    id = create_demo(client, accounts[0])
    assert client.delete("/api/v1/investigations/" + id, headers=accounts[0]).status_code == 204
    with SessionLocal() as db:
        assert not db.query(Evidence).filter(Evidence.investigation_id == id).count()
        assert not db.query(AIReport).filter(AIReport.investigation_id == id).count()

def test_real_partial_without_keys(client, accounts):
    r = client.post("/api/v1/investigations", json={"target": "https://example.com?token=private"}, headers=accounts[0])
    assert r.status_code == 202, r.text
    d = client.get("/api/v1/investigations/" + r.json()["id"], headers=accounts[0]).json()
    assert not d["is_demo"] and d["status"] == "partial"
    assert "private" not in json.dumps(d)
    assert any(run["provider"] == "kev" and run["status"] == "success" for run in d["runs"])
    assert any(run["provider"] == "ai" and run["status"] == "not_configured" for run in d["runs"])


def test_evidence_batch_deduplication_and_distinct_cves(client, accounts):
    id = create_demo(client, accounts[0])
    first = providers.item("kev_general", "Mesmo nome de vulnerabilidade", "Fixture", cve="CVE-2026-96655")
    second = providers.item("kev_general", "Mesmo nome de vulnerabilidade", "Fixture", cve="CVE-2026-96652")
    result = providers.Result("success", "Fixture", [first, first, second])
    persist_result(id, "test-catalog", result)
    persist_result(id, "test-catalog", result)
    d = client.get("/api/v1/investigations/" + id, headers=accounts[0]).json()
    rows = [e for e in d["evidence"] if e["provider"] == "test-catalog"]
    assert len(rows) == 2
    assert next(r for r in d["runs"] if r["provider"] == "test-catalog")["results_count"] == 2

def test_validation_and_authorization(client, accounts):
    assert client.get("/api/v1/investigations").status_code == 401
    assert client.post("/api/v1/investigations", json={"target": "http://127.0.0.1"}, headers=accounts[0]).status_code == 422
    assert client.post("/api/v1/investigations", json={"target": "example.com", "technical": True}, headers=accounts[0]).status_code == 422
    assert client.post("/api/v1/scans", json={"url": "example.com"}, headers=accounts[0]).status_code == 422

def test_message_analysis_avoids_storing_raw_text(client, accounts):
    raw = "Urgente: confirma a password=private-value alice@example.com https://example.com/login?token=private"
    response = client.post("/api/v1/investigations", json={"kind": "message", "message": raw}, headers=accounts[0])
    assert response.status_code == 202
    d = client.get("/api/v1/investigations/" + response.json()["id"], headers=accounts[0]).json()
    assert d["message_analysis"]["signals"]
    assert "private-value" not in json.dumps(d) and "alice@" not in json.dumps(d)

def test_recover_and_compare(client, accounts):
    first = create_demo(client, accounts[0])
    second = create_demo(client, accounts[0])
    compare = client.get("/api/v1/investigations/" + second + "/comparison", headers=accounts[0]).json()
    assert compare["previous_id"] == first
    assert compare["added"] == [] and compare["removed"] == []
    with SessionLocal() as db:
        inv = db.get(Investigation, second)
        inv.status = "running"
        db.commit()
    recover_interrupted()
    d = client.get("/api/v1/investigations/" + second, headers=accounts[0]).json()
    assert d["status"] == "interrupted"

def test_configuration_does_not_expose_keys(client, accounts, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-secret-value")
    d = client.get("/api/v1/investigations/providers", headers=accounts[0])
    assert d.status_code == 200
    assert "test-secret-value" not in d.text
    assert any(x["id"] == "ai" and x["configured"] for x in d.json()["providers"])
