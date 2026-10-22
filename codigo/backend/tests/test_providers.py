import json
import pytest
from app.services import providers, ai_service
from app.services.privacy import redact, extract_links, message_signals


@pytest.mark.parametrize("raw,expected", [
    ("2026-10-01", "2026-10-01"),
    ("2026-10-01 13:20:30 UTC", "2026-10-01T13:20:30+00:00"),
    ("2026-10-01T13:20:30Z", "2026-10-01T13:20:30+00:00"),
    ("2026", None), ("2026-02-30", None), ("yesterday", None),
    ("2026-10-01T13:20:30", None), (None, None),
])
def test_publication_dates_preserve_only_known_precision(raw, expected):
    assert providers.item("public_reference", "Title", "Description", published=raw)["published_at"] == expected

def test_urlhaus_results_and_no_match(monkeypatch):
    monkeypatch.setenv("URLHAUS_AUTH_KEY", "test-key")
    calls = []
    monkeypatch.setattr(providers, "json_request", lambda *a, **k: calls.append((a, k)) or {"query_status": "ok", "urls": [{"url": "https://example.com/a?token=hidden", "url_status": "offline", "urlhaus_reference": "https://urlhaus.abuse.ch/url/1/"}]})
    result = providers.urlhaus("https://example.com/")
    assert result.status == "success"
    assert result.evidence[0]["meta"]["indicator"] == "https://example.com/a"
    assert "hidden" not in json.dumps(result.evidence)
    monkeypatch.setattr(providers, "json_request", lambda *a, **k: {"query_status": "no_results"})
    assert providers.urlhaus("https://example.com/").status == "no_results"

def test_missing_keys_are_not_clean_results():
    assert providers.urlhaus("https://example.com/").status == "not_configured"
    assert providers.phishtank("https://example.com/").status == "not_configured"
    assert providers.exposure("example.com").status == "not_configured"
    assert providers.osint("https://example.com/", "").status == "not_configured"

def test_osint_deduplicates_and_does_not_confirm_breach(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(providers, "json_request", lambda *a, **k: {"results": [{"title": "Example.com alleged breach", "url": "https://news.example.com/article", "content": "Unverified incident concerning example.com."}]})
    result = providers.osint("https://example.com/", "")
    assert len(result.evidence) == 1
    assert result.evidence[0]["confirmation"] != "confirmed"
    assert result.evidence[0]["event_at"] is None

def test_budget_exhaustion_and_safe_error(monkeypatch):
    with pytest.raises(providers.SourceError):
        providers.reserve("test", 0)
    def quota(*a): raise providers.SourceError("rate_limited", "quota")
    assert providers.guarded(quota).status == "rate_limited"
    def bad(*a): raise ValueError("secret-must-not-escape")
    result = providers.guarded(bad)
    assert "secret" not in result.message
    assert result.status == "error"


def test_osint_partial_quota_keeps_first_query_evidence(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "synthetic")
    monkeypatch.setenv("SEARCH_MONTHLY_LIMIT", "1")
    calls = []
    monkeypatch.setattr(providers, "json_request", lambda *a, **k: calls.append(a) or {"results": [{"title": "example.com incident", "url": "https://news.example.com/one", "content": "Fixture"}]})
    result = providers.osint("https://example.com/", "")
    assert result.status == "partial" and len(result.evidence) == 1
    assert len(calls) == 1 and "Limite local" in result.message

def test_kev_general_not_target_associated():
    result = providers.kev()
    entry = result.evidence[0]
    assert entry["category"] == "kev_general"
    assert entry["published_at"] is None and entry["event_at"] is None
    assert entry["meta"]["catalog_added_at"] == "2026-01-01"
    assert "not_associated" in entry["meta"]["relevance"]

def test_message_minimization():
    assert redact("CVE-2026-106931 e CVE-2026-96655") == "CVE-2026-106931 e CVE-2026-96655"
    raw = "Urgente: verificar password=private-value para alice@example.com https://example.com/login?token=secret"
    redacted = redact(raw)
    assert "alice@" not in redacted and "private-value" not in redacted
    assert extract_links(raw) == ["https://example.com/login"]
    assert message_signals(raw)["signals"]

def test_invalid_ai_evidence_rejected():
    evidence = [{"id": "valid"}]
    payload = {"summary": "Resumo", "observations": [{"text": "Fonte inventada", "evidence_ids": ["invented"]}], "recommendations": [], "limitations": ["Dados limitados"]}
    with pytest.raises(ValueError):
        ai_service.validated_report(payload, evidence)

def test_ai_schema_valid_report():
    report = {"summary": "Resumo", "observations": [{"text": "Observação", "evidence_ids": ["valid"]}], "recommendations": [], "limitations": ["Dados limitados"]}
    assert ai_service.validated_report(report, [{"id": "valid"}])["summary"] == "Resumo"
