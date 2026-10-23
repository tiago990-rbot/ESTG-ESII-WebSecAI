from copy import deepcopy
import json
import pytest
from evaluations.report_fixture import snapshot
from app.services import ai_service, providers, investigation_service
from app.services.intelligence import QUESTIONS, select_evidence, technical_records
from app.services.investigation_pdf import investigation_pdf

def test_enriched_report_and_legacy_are_compatible():
    data = snapshot()
    raw = data["reports"][0]["report"]
    assert len(ai_service.validated_report(raw, data["evidence"])["intelligence"]["questions"]) == 6
    old = {key: raw[key] for key in ["summary", "observations", "recommendations", "limitations"]}
    assert ai_service.validated_report(old, data["evidence"])["intelligence"] is None

@pytest.mark.parametrize("group", ["conclusions", "correlations", "questions", "actions"])
def test_all_intelligence_references_are_validated(group):
    data = snapshot()
    raw = data["reports"][0]["report"]
    raw["intelligence"][group][0]["evidence_ids"].append("invented-reference")
    with pytest.raises(ValueError, match="Referências"):
        ai_service.validated_report(raw, data["evidence"])

def test_six_distinct_questions_and_explicit_unknown_required():
    data = snapshot()
    raw = data["reports"][0]["report"]
    raw["intelligence"]["questions"][0]["key"] = "identity"
    with pytest.raises(ValueError, match="seis perguntas"):
        ai_service.validated_report(raw, data["evidence"])
    data = snapshot()
    raw = data["reports"][0]["report"]
    question = next(item for item in raw["intelligence"]["questions"] if item["key"] == "identity")
    question["assessment"] = "supported"
    with pytest.raises(ValueError, match="sem evidências"):
        ai_service.validated_report(raw, data["evidence"])

@pytest.mark.parametrize("metadata,category", [({"matched_by": "organization_name"}, "public_reference"), ({"relevance": "needs_review"}, "public_reference"), ({}, "kev_general"), ({}, "kev_candidate"), ({"retained_from_earlier_attempt": True}, "incident_report")])
def test_high_confidence_rejected_for_uncertain_inputs(metadata, category):
    data = snapshot()
    data["evidence"][0].update(meta=metadata, category=category)
    raw = data["reports"][0]["report"]
    raw["intelligence"]["conclusions"][0]["confidence"] = "high"
    with pytest.raises(ValueError, match="Confiança"):
        ai_service.validated_report(raw, data["evidence"])

def test_repeated_source_cannot_be_high_confidence_correlation():
    data = snapshot()
    raw = data["reports"][0]["report"]
    raw["intelligence"]["correlations"][0]["confidence"] = "high"
    for entry in data["evidence"]:
        entry["source_url"] = "https://source.example/same-document"
        entry["confirmation"] = "reported"
    with pytest.raises(ValueError, match="Referências repetidas"):
        ai_service.validated_report(raw, data["evidence"])

@pytest.mark.parametrize("confirmation", ["allegation", "unverified"])
def test_high_confidence_is_rejected_for_unverified_claims(confirmation):
    data = snapshot()
    data["evidence"][0]["confirmation"] = confirmation
    raw = data["reports"][0]["report"]
    raw["intelligence"]["conclusions"][0]["confidence"] = "high"
    with pytest.raises(ValueError, match="Confiança"):
        ai_service.validated_report(raw, data["evidence"])

def test_balanced_selection_preserves_public_context_and_input_order():
    data = snapshot()
    technical = [dict(data["evidence"][4], id="tech-" + str(i), category="technical") for i in range(35)]
    evidence = technical + data["evidence"]
    order = [entry["id"] for entry in evidence]
    selected = select_evidence(evidence)
    assert len(selected) == 24
    assert {"osint", "urlhaus", "kev", "technical"} == {entry["provider"] for entry in selected}
    assert any(entry["category"] == "technical_posture" for entry in selected)
    assert [entry["id"] for entry in evidence] == order

def test_technical_summary_excludes_raw_headers_and_cookie_values():
    technical = snapshot()["technical"]
    technical["details"] = {"headers": {"secret": "private-sentinel"}, "cookies": "private-sentinel"}
    records = technical_records(technical, providers.item)
    assert records[0]["category"] == "technical_posture"
    assert records[0]["meta"]["score"] == 72
    assert "private-sentinel" not in json.dumps(records)

def test_new_generation_uses_full_contract_and_bounded_context(monkeypatch):
    data = snapshot()
    raw = data["reports"][0]["report"]
    data["evidence"][0]["meta"]["private_sentinel"] = "do-not-send"
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.setenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    reservations, requests = [], []
    monkeypatch.setattr(providers, "reserve", lambda *a, **kw: reservations.append(True))
    def respond(*args, **kwargs):
        requests.append(kwargs["json"])
        return {"choices": [{"message": {"content": json.dumps(raw)}}]}
    monkeypatch.setattr(providers, "json_request", respond)
    report, model = ai_service.generate(data["evidence"], data["target"], data["runs"])
    assert report["intelligence"] and len(requests) == len(reservations) == 1
    request = requests[0]
    assert request["response_format"]["json_schema"]["strict"]
    context = json.loads(request["messages"][1]["content"])
    assert context["standard_questions"] == QUESTIONS
    assert "do-not-send" not in json.dumps(context)
    assert context["selection"]["included"] <= 24
    assert request["max_completion_tokens"] == 4600
    def assert_closed(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert set(node["required"]) == set(node["properties"])
                assert node["additionalProperties"] is False
            for value in node.values(): assert_closed(value)
        elif isinstance(node, list):
            for value in node: assert_closed(value)
    assert_closed(request["response_format"]["json_schema"]["schema"])

def test_combined_demo_uses_no_analyzer_or_provider(client, accounts, monkeypatch):
    monkeypatch.setattr(investigation_service, "run_website_analysis", lambda *a: pytest.fail("Demo must not scan"))
    monkeypatch.setattr(ai_service, "generate", lambda *a: pytest.fail("Demo must not call AI"))
    response = client.post("/api/v1/investigations", json={"demo": True, "technical": True}, headers=accounts[0])
    assert response.status_code == 202
    path = "/api/v1/investigations/" + response.json()["id"]
    data = client.get(path, headers=accounts[0]).json()
    assert data["technical"]["score"] == 72 and len(data["evidence"]) == 7
    assert data["reports"][-1]["is_current"]
    assert len(data["reports"][-1]["report"]["intelligence"]["questions"]) == 6
    assert client.get(path + "/report", headers=accounts[0]).content.startswith(b"%PDF")
    assert client.get(path + "/report", headers=accounts[1]).status_code == 404

def test_authorized_combined_pipeline_feeds_technical_and_ti_to_ai(client, accounts, monkeypatch):
    fixture = snapshot()
    scans, generations = [], []
    monkeypatch.setattr(investigation_service, "run_website_analysis", lambda target: scans.append(target) or fixture["technical"])
    def generated(evidence, target, runs, question=""):
        generations.append(evidence)
        assert any(entry["category"] == "technical_posture" for entry in evidence)
        assert any(entry["category"] == "kev_general" for entry in evidence)
        ref = next(entry["id"] for entry in evidence if entry["provider"] == "technical")
        return {"summary": "Resposta controlada.", "observations": [{"text": "Configuração fictícia.", "evidence_ids": [ref]}], "recommendations": [], "limitations": ["Teste sem modelo real."]}, "fixture-only"
    monkeypatch.setattr(ai_service, "generate", generated)
    forbidden = client.post("/api/v1/investigations", json={"target": "example.com", "technical": True}, headers=accounts[0])
    assert forbidden.status_code == 422 and not scans
    response = client.post("/api/v1/investigations", json={"target": "example.com", "technical": True, "authorized": True}, headers=accounts[0])
    assert response.status_code == 202
    path = "/api/v1/investigations/" + response.json()["id"]
    for _ in range(2): assert client.get(path + "/report", headers=accounts[0]).content.startswith(b"%PDF")
    assert len(scans) == len(generations) == 1, "Export must only render persisted data"

def test_pdf_escapes_source_text_and_has_intelligence_sections(monkeypatch):
    import app.services.investigation_pdf as pdf
    data = snapshot()
    data["evidence"][0]["title"] = "<script>untrusted & source</script>"
    captured = []
    original = pdf.Paragraph
    def capture(text, style):
        captured.append(text)
        return original(text, style)
    monkeypatch.setattr(pdf, "Paragraph", capture)
    assert pdf.investigation_pdf(data).startswith(b"%PDF")
    text = " ".join(captured)
    for question in QUESTIONS.values(): assert question in text
    assert "&lt;script&gt;" in text and "<script>" not in text
    assert 'href="#evidence-E1"' in text
    assert "Critério de conclusão" in text and "72/100" in text

def test_pdf_marks_retained_technical_measurements(monkeypatch):
    import app.services.investigation_pdf as pdf
    data = snapshot()
    next(run for run in data["runs"] if run["provider"] == "technical")["status"] = "error"
    captured = []
    original = pdf.Paragraph
    monkeypatch.setattr(pdf, "Paragraph", lambda text, style: captured.append(text) or original(text, style))
    assert pdf.investigation_pdf(data).startswith(b"%PDF")
    assert any("RESULTADOS TÉCNICOS CONSERVADOS" in text for text in captured)
    assert any("72/100 (anterior)" in text for text in captured)
