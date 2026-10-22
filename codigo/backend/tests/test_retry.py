from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import importlib
import pytest
from app.db.session import SessionLocal
from app.models.investigation import Investigation
from app.services import providers, ai_service
from app.services import investigation_service as service


def start(client, headers, **data):
    response = client.post("/api/v1/investigations", json={"target": "example.com", **data}, headers=headers)
    assert response.status_code == 202, response.text
    return "/api/v1/investigations/" + response.json()["id"]


def get(client, path, headers):
    return client.get(path, headers=headers).json()


def fake_ai(evidence, target, runs, question=""):
    ref = evidence[0]["id"]
    return {"summary": "Resposta controlada, sem modelo real.", "observations": [{"text": "Validar a fonte.", "evidence_ids": [ref]}], "recommendations": [], "limitations": ["Teste controlado."]}, "fixture-model"


def seed_partial_news(monkeypatch):
    entry = providers.item("incident_report", "Notícia anterior", "Fixture, não é incidente real.", "https://news.example.com/old")
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("partial", "Consulta incompleta", [entry]))
    return entry


def test_retry_only_selected_source_and_reject_completed(client, accounts, monkeypatch):
    path = start(client, accounts[0])
    before = get(client, path, accounts[0])
    calls = []
    monkeypatch.setattr(providers, "osint", lambda *args: calls.append(args) or providers.Result("no_results", "Sem referências"))
    def forbidden(*a):
        pytest.fail("Uma nova tentativa não deve repetir outras fontes")
    for name in ("urlhaus", "phishtank", "kev", "exposure"):
        monkeypatch.setattr(providers, name, forbidden)
    monkeypatch.setattr(ai_service, "generate", forbidden)
    response = client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0])
    assert response.status_code == 202, response.text
    after = get(client, path, accounts[0])
    assert calls == [("https://example.com/", "")]
    assert next(r for r in after["runs"] if r["provider"] == "osint")["status"] == "no_results"
    assert next(r for r in after["runs"] if r["provider"] == "kev") == next(r for r in before["runs"] if r["provider"] == "kev")
    assert after["evidence"] == before["evidence"]
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 409


def test_retry_archives_absent_evidence_and_invalidates_then_refreshes_ai(client, accounts, monkeypatch):
    seed_partial_news(monkeypatch)
    monkeypatch.setattr(ai_service, "generate", fake_ai)
    path = start(client, accounts[0])
    before = get(client, path, accounts[0])
    assert before["reports"][-1]["is_current"]
    old = next(e for e in before["evidence"] if e["provider"] == "osint")
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("no_results", "Sem correspondências"))
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    after = get(client, path, accounts[0])
    assert not any(e["provider"] == "osint" for e in after["evidence"])
    assert after["previous_evidence"][0]["id"] == old["id"]
    assert after["previous_evidence"][0]["observed_at"] == old["observed_at"]
    assert not after["reports"][-1]["is_current"] and "ai" in after["retryable_providers"]
    assert client.post(path + "/questions", json={"text": "Que devo fazer?"}, headers=accounts[0]).status_code == 409
    assert client.get(path + "/report", headers=accounts[0]).content.startswith(b"%PDF")
    def refreshed_ai(evidence, *args):
        assert all(e["id"] != old["id"] for e in evidence)
        return fake_ai(evidence, *args)
    monkeypatch.setattr(ai_service, "generate", refreshed_ai)
    assert client.post(path + "/retry", json={"provider": "ai"}, headers=accounts[0]).status_code == 202
    final = get(client, path, accounts[0])
    assert final["reports"][-1]["is_current"] and not final["reports"][0]["is_current"]
    assert final["reports"][-1]["prompt_version"] == ai_service.PROMPT_VERSION
    assert "ai" not in final["retryable_providers"]
    assert client.post(path + "/questions", json={"text": "Que devo fazer?"}, headers=accounts[0]).status_code == 200


@pytest.mark.parametrize("status", ["partial", "error", "rate_limited"])
def test_failed_retry_retains_observations_and_success_reuses_identity(client, accounts, monkeypatch, status):
    entry = seed_partial_news(monkeypatch)
    path = start(client, accounts[0])
    old = next(e for e in get(client, path, accounts[0])["evidence"] if e["provider"] == "osint")
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result(status, "Falha controlada"))
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    after = get(client, path, accounts[0])
    retained = next(e for e in after["evidence"] if e["provider"] == "osint")
    assert retained["id"] == old["id"] and retained["observed_at"] == old["observed_at"]
    assert retained["meta"]["retained_from_earlier_attempt"]
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("success", "Consulta concluída", [entry, entry]))
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    rows = [e for e in get(client, path, accounts[0])["evidence"] if e["provider"] == "osint"]
    assert len(rows) == 1 and rows[0]["id"] == old["id"]
    assert not rows[0]["meta"].get("retained_from_earlier_attempt")


def test_retry_access_input_and_demo_restrictions(client, accounts):
    path = start(client, accounts[0])
    assert client.post(path + "/retry", json={"provider": "osint"}).status_code == 401
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[1]).status_code == 404
    assert client.post(path + "/retry", json={"provider": "system"}, headers=accounts[0]).status_code == 422
    assert client.post(path + "/retry", json={"provider": "technical", "authorized": True}, headers=accounts[0]).status_code == 409
    assert client.post(path + "/retry", json={"provider": "kev"}, headers=accounts[0]).status_code == 409
    demo = start(client, accounts[0], demo=True)
    assert client.post(demo + "/retry", json={"provider": "ai"}, headers=accounts[0]).status_code == 409


def test_technical_retry_reauthorizes_and_requires_original_scope(client, accounts, monkeypatch):
    def fail(*a): raise ValueError("Fixture")
    monkeypatch.setattr(service, "run_website_analysis", fail)
    path = start(client, accounts[0], technical=True, authorized=True)
    assert client.post(path + "/retry", json={"provider": "technical"}, headers=accounts[0]).status_code == 422
    calls = []
    monkeypatch.setattr(service, "run_website_analysis", lambda target: calls.append(target) or {"score": 90, "summary": "Fixture", "findings": []})
    assert client.post(path + "/retry", json={"provider": "technical", "authorized": True}, headers=accounts[0]).status_code == 202
    assert calls == ["https://example.com/"]
    assert get(client, path, accounts[0])["technical"]["score"] == 90


def test_message_retry_uses_only_stored_normalized_links(client, accounts, monkeypatch):
    path = start(client, accounts[0], kind="message", message="Urgente password=private-value alice@example.com https://example.com/login?token=private")
    calls = []
    monkeypatch.setattr(providers, "urlhaus", lambda link: calls.append(link) or providers.Result("no_results", "Fixture"))
    assert client.post(path + "/retry", json={"provider": "urlhaus"}, headers=accounts[0]).status_code == 202
    assert calls == ["https://example.com/login"]
    assert "private-value" not in client.get(path, headers=accounts[0]).text


def test_retry_local_rate_limit_and_provider_budget(client, accounts, monkeypatch):
    path = start(client, accounts[0])
    for _ in range(6):
        assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 429
    another = start(client, accounts[0])
    monkeypatch.setenv("TAVILY_API_KEY", "synthetic")
    monkeypatch.setenv("SEARCH_MONTHLY_LIMIT", "0")
    assert client.post(another + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    run = next(r for r in get(client, another, accounts[0])["runs"] if r["provider"] == "osint")
    assert run["status"] == "rate_limited"  # quota denied before any network call (autouse guard)


def test_comparison_excludes_archived_evidence_on_both_sides(client, accounts, monkeypatch):
    seed_partial_news(monkeypatch)
    first = start(client, accounts[0])
    second = start(client, accounts[0])
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("no_results", "Fixture"))
    assert client.post(second + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    assert client.get(second + "/comparison", headers=accounts[0]).json()["removed"] == ["Notícia anterior"]
    assert client.post(first + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202
    comparison = client.get(second + "/comparison", headers=accounts[0]).json()
    assert comparison["removed"] == [] and comparison["added"] == []


def test_retry_atomic_claim_rejects_concurrent_requests(client, accounts, monkeypatch):
    path = start(client, accounts[0])
    routes = importlib.import_module("app.api.routes.investigations")
    owned = routes.owned
    gate = Barrier(2)
    queued = []
    def synchronized(*args):
        inv = owned(*args)
        gate.wait(timeout=10)
        return inv
    monkeypatch.setattr(routes, "owned", synchronized)
    monkeypatch.setattr(routes, "run_retry", lambda *args: queued.append(args))
    def send():
        return client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: send(), range(2)))
    assert sorted(results) == [202, 409]
    assert len(queued) == 1


def test_restart_marks_provider_and_allows_missing_module(client, accounts, monkeypatch):
    path = start(client, accounts[0])
    with SessionLocal() as db:
        inv = db.get(Investigation, path.rsplit("/", 1)[-1])
        inv.status, inv.finished_at = "running", None
        for row in list(inv.runs):
            if row.provider == "osint": db.delete(row)
            if row.provider == "kev": row.status = "running"
        db.commit()
    service.recover_interrupted()
    before = get(client, path, accounts[0])
    assert next(r for r in before["runs"] if r["provider"] == "kev")["status"] == "interrupted"
    assert "osint" in before["retryable_providers"]
    monkeypatch.setattr(providers, "osint", lambda *a: providers.Result("no_results", "Fixture"))
    assert client.post(path + "/retry", json={"provider": "osint"}, headers=accounts[0]).status_code == 202


def test_question_discards_answer_if_sources_changed_during_call(client, accounts, monkeypatch):
    monkeypatch.setattr(ai_service, "generate", fake_ai)
    path = start(client, accounts[0])
    inv_id = path.rsplit("/", 1)[-1]
    def race(evidence, target, runs, question=""):
        service.persist_result(inv_id, "osint", providers.Result("error", "Alteração durante resposta"))
        return fake_ai(evidence, target, runs, question)
    monkeypatch.setattr(ai_service, "generate", race)
    assert client.post(path + "/questions", json={"text": "O que devo verificar?"}, headers=accounts[0]).status_code == 409
    assert len(get(client, path, accounts[0])["reports"]) == 1


def test_pdf_labels_stale_summaries_and_previous_observations(monkeypatch):
    module = importlib.import_module("app.services.investigation_pdf")
    original = module.Paragraph
    labels = []
    def capture(text, style):
        labels.append(text)
        return original(text, style)
    monkeypatch.setattr(module, "Paragraph", capture)
    evidence = {"id": "test", "title": "Fixture", "provider": "osint", "confirmation": "reported", "description": "Fixture", "published_at": None, "event_at": None, "observed_at": "2026-10-21", "source_url": "", "meta": {"not_returned_in_latest_success": True}}
    report, _ = fake_ai([evidence], "example.com", [])
    snapshot = {"is_demo": False, "target": "example.com", "created_at": "2026-10-21", "status": "partial", "runs": [], "reports": [{"model": "fixture", "is_current": False, "report": report}], "evidence": [], "previous_evidence": [evidence]}
    assert module.investigation_pdf(snapshot).startswith(b"%PDF")
    assert any("SÍNTESE ANTERIOR DESATUALIZADA" in text for text in labels)
    assert any("RECOLHA ANTERIOR" in text for text in labels)
