import json
from pathlib import Path
import pytest
from dotenv import dotenv_values
from app.core.local_setup import save_provider_keys
from app.services import providers
from app.services.integration_check import check_connections

TAVILY = "tvly-synthetic-test-0123456789"
GROQ = "gsk_synthetic_test_0123456789"


def config(tmp_path, raw=b"JWT_SECRET=synthetic-jwt-preserve\r\nDATABASE_URL=sqlite:///existing.db\r\nTAVILY_API_KEY=\r\nGROQ_API_KEY=old-synthetic-key\r\n"):
    path = tmp_path / ".env"
    path.write_bytes(raw)
    return path


def test_private_setup_preserves_other_settings_and_empty_fields(tmp_path):
    path = config(tmp_path)
    saved = save_provider_keys(path, {"TAVILY_API_KEY": TAVILY, "GROQ_API_KEY": ""})
    data = dotenv_values(path)
    assert saved == ["TAVILY_API_KEY"]
    assert data["JWT_SECRET"] == "synthetic-jwt-preserve" and data["DATABASE_URL"] == "sqlite:///existing.db"
    assert data["TAVILY_API_KEY"] == TAVILY and data["GROQ_API_KEY"] == "old-synthetic-key"
    assert b"\r\n" in path.read_bytes() and not list(tmp_path.glob(".env.*.tmp"))


def test_private_setup_handles_duplicates_and_missing_newline(tmp_path):
    path = config(tmp_path, b"TAVILY_API_KEY=old\nexport TAVILY_API_KEY=duplicate\nJWT_SECRET=preserve")
    save_provider_keys(path, {"TAVILY_API_KEY": TAVILY, "GROQ_API_KEY": GROQ})
    assert path.read_text().count("TAVILY_API_KEY=") == 1
    assert dotenv_values(path)["GROQ_API_KEY"] == GROQ
    assert dotenv_values(path)["JWT_SECRET"] == "preserve"


@pytest.mark.parametrize("updates", [{"JWT_SECRET": "replacement"}, {"TAVILY_API_KEY": "abc\nJWT_SECRET=bad"}, {"TAVILY_API_KEY": ""}, {"GROQ_API_KEY": "'quoted-value'"}])
def test_private_setup_rejects_unsafe_input_without_changing_file(tmp_path, updates):
    path = config(tmp_path)
    original = path.read_bytes()
    with pytest.raises(ValueError):
        save_provider_keys(path, updates)
    assert path.read_bytes() == original


def test_private_setup_atomic_failure_preserves_original_and_cleans_temp(tmp_path, monkeypatch):
    import app.core.local_setup as module
    path = config(tmp_path)
    original = path.read_bytes()
    def fail(*a): raise OSError("synthetic failure")
    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        save_provider_keys(path, {"TAVILY_API_KEY": TAVILY})
    assert path.read_bytes() == original and not list(tmp_path.glob(".env.*.tmp"))


def test_connection_check_missing_keys_does_not_make_requests():
    assert all(c["status"] == "not_configured" for c in check_connections(live=True)["checks"].values())


def test_connection_check_does_not_print_keys_or_unexpected_account_data(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", TAVILY)
    monkeypatch.setenv("GROQ_API_KEY", GROQ)
    calls = []
    def metadata(method, url, **kwargs):
        calls.append((method, url))
        if "tavily" in url:
            return {"account": {"current_plan": "Researcher", "paygo_limit": 0, "private_email": "do-not-print@example.com"}, "key": {"private": TAVILY}}
        return {"data": [{"id": "qwen/qwen3.8-27b", "private": GROQ}]}
    monkeypatch.setattr(providers, "json_request", metadata)
    assert check_connections()["checks"]["tavily"]["status"] == "configured_not_validated" and not calls
    result = check_connections(live=True)
    assert result["checks"]["tavily"]["free_plan_confirmed"] is True
    assert result["checks"]["groq"]["model_available"] is True
    assert result["checks"]["groq"]["free_plan_confirmed"] is None
    assert calls == [("GET", "https://api.tavily.com/usage"), ("GET", "https://api.groq.com/openai/v1/models")]
    assert TAVILY not in json.dumps(result) and GROQ not in json.dumps(result) and "do-not-print" not in json.dumps(result)
    assert not result["analysis_performed"]


def test_connection_check_error_does_not_expose_raw_exception(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", TAVILY)
    def fail(*a, **kw): raise ValueError(TAVILY)
    monkeypatch.setattr(providers, "json_request", fail)
    result = check_connections(live=True)
    assert result["checks"]["tavily"]["status"] == "error" and TAVILY not in json.dumps(result)
