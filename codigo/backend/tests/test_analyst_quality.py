import json
import pytest
from app.services import providers, ai_service


@pytest.mark.parametrize("title,content,url,expected", [
    ("Incidente em Atlas Labs", "Atlas Labs sofreu um ataque", "https://news.example/story", "needs_review"),
    ("Outro domínio", "Ataque em notatlas.example, não no alvo", "https://notatlas.example/", "needs_review"),
    ("Incidente", "Foi reportado um cyber-attack em atlas.example", "https://news.example/story", "candidate_match"),
])
def test_osint_identity_requires_domain_not_only_similar_name(monkeypatch, title, content, url, expected):
    monkeypatch.setenv("TAVILY_API_KEY", "synthetic")
    monkeypatch.setattr(providers, "json_request", lambda *a, **k: {"results": [{"title": title, "content": content, "url": url}]})
    result = providers.osint("https://atlas.example/", "Atlas Labs")
    assert result.evidence[0]["meta"]["relevance"] == expected
    if expected == "candidate_match":
        assert result.evidence[0]["category"] == "incident_report"


def test_no_evidence_blocks_generation_before_quota_or_network(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.setattr(providers, "reserve", lambda *a, **k: pytest.fail("Must not consume quota"))
    with pytest.raises(providers.SourceError) as error:
        ai_service.generate([], "https://atlas.example/", [])
    assert error.value.status == "no_results"


def test_missing_sources_are_explained_without_secrets(client, accounts):
    rows = client.get("/api/v1/investigations/providers", headers=accounts[0]).json()["providers"]
    index = {row["id"]: row for row in rows}
    assert index["intelx"]["implemented"] is False
    assert index["urlhaus"]["access_requirement"] == "account_key"
    assert index["exposure"]["access_requirement"] == "subscription_verified_domain"
    assert all(row["setup_note"] for row in rows)
    assert "synthetic" not in json.dumps(rows)


def test_format_fallback_is_bounded_and_keeps_reference_validation(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    from evaluations.cases import cases
    case = cases()[0]
    formats, reservations = [], []
    monkeypatch.setattr(providers, "reserve", lambda *a, **k: reservations.append(True))
    report = {"summary": "Alegação", "observations": [{"text": "Não confirmada", "evidence_ids": ["invented"]}], "recommendations": [], "limitations": ["Fonte limitada"]}
    def respond(*args, **kwargs):
        formats.append(kwargs["json"]["response_format"]["type"])
        if len(formats) == 1:
            raise providers.SourceError("error", "safe", {"reason": "json_validation"})
        return {"choices": [{"message": {"content": json.dumps(report)}}]}
    monkeypatch.setattr(providers, "json_request", respond)
    with pytest.raises(ValueError, match="referências inexistentes"):
        ai_service.generate(case["evidence"], case["target"], case["runs"])
    assert formats == ["json_schema", "json_object"]
    assert len(reservations) == 2


def test_quota_failure_never_triggers_format_fallback(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    from evaluations.cases import cases
    case = cases()[0]
    calls = []
    monkeypatch.setattr(providers, "reserve", lambda *a, **k: None)
    def respond(*args, **kwargs):
        calls.append(True)
        raise providers.SourceError("rate_limited", "safe")
    monkeypatch.setattr(providers, "json_request", respond)
    with pytest.raises(providers.SourceError):
        ai_service.generate(case["evidence"], case["target"], case["runs"])
    assert len(calls) == 1
