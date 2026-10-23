import importlib.util
from pathlib import Path
from app.services import providers


def load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validar_urlhaus.py"
    spec = importlib.util.spec_from_file_location("urlhaus_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_isolated_validation_limits_and_authentication(tmp_path, monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "ROOT", tmp_path)
    monkeypatch.setenv("URLHAUS_AUTH_KEY", "synthetic-test-key")
    calls = []
    def official(*args, **kwargs):
        calls.append(args)
        return {"query_status": "no_results"}
    monkeypatch.setattr(providers, "json_request", official)
    for attempt in (1, 2):
        result = script.validate()
        assert result["authenticated"] and result["status"] == "no_results"
        assert result["requests_this_run"] == 1 and result["attempt"] == attempt
        assert "synthetic-test-key" not in str(result)
    assert script.validate()["status"] == "limit_reached"
    assert len(calls) == 2


def test_404_does_not_prove_authenticated_no_results(tmp_path, monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "ROOT", tmp_path)
    monkeypatch.setenv("URLHAUS_AUTH_KEY", "synthetic-test-key")
    def missing(*args, **kwargs):
        raise providers.SourceError("no_results", "HTTP 404 controlado")
    monkeypatch.setattr(providers, "json_request", missing)
    result = script.validate()
    assert result["status"] == "unvalidated_response" and not result["authenticated"]
