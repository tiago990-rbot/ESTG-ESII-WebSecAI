from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
import pytest
from fastapi import HTTPException
from app.core import deployment
from app.db.configuration import database_url, migration_url, build_engine
from app.db.session import SessionLocal, engine
from app.models.investigation import Usage, Investigation, Evidence
from app.services import providers


def test_remote_connections_verify_certificate_and_use_psycopg(monkeypatch):
    url = database_url("postgresql://synthetic:synthetic@ep-example.neon.tech/test?sslmode=require&channel_binding=require")
    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "verify-full" and url.query["sslrootcert"]
    assert url.query["channel_binding"] == "require"
    with pytest.raises(RuntimeError):
        database_url("postgresql://synthetic@ep-example.neon.tech/test?sslmode=disable")
    monkeypatch.setenv("DATABASE_URL", "postgresql://synthetic@ep-example-pooler.neon.tech/test")
    monkeypatch.delenv("DATABASE_MIGRATION_URL", raising=False)
    with pytest.raises(RuntimeError):
        migration_url()
    monkeypatch.setenv("DATABASE_MIGRATION_URL", "postgresql://synthetic@ep-example-pooler.neon.tech/test")
    with pytest.raises(RuntimeError):
        migration_url()
    monkeypatch.setenv("DATABASE_MIGRATION_URL", "postgresql://synthetic@ep-example.neon.tech/test")
    assert "-pooler" not in migration_url().host
    monkeypatch.setenv("DATABASE_MIGRATION_URL", "postgresql://synthetic@ep-example.neon.tech/other")
    with pytest.raises(RuntimeError):
        migration_url()


@pytest.mark.parametrize("wrapper", ["{}", "'{}'", '"{}"', "psql '{}'", 'psql "{}"'])
def test_neon_connection_snippets_are_parsed_without_shell_execution(wrapper):
    raw = "postgresql://synthetic:synthetic@ep-example.neon.tech/test?sslmode=require&channel_binding=require"
    url = database_url(wrapper.format(raw))
    assert url.host == "ep-example.neon.tech" and url.database == "test"
    assert url.query["sslmode"] == "verify-full"
    assert url.query["channel_binding"] == "require"


def test_invalid_connection_snippets_do_not_disclose_credentials():
    for raw in ("psql 'postgresql://synthetic:private-value@ep-example.neon.tech/test' --extra", "psql 'private-value"):
        with pytest.raises(RuntimeError) as exc:
            database_url(raw)
        assert "private-value" not in str(exc.value)
        assert "ep-example" not in str(exc.value)


def test_online_requires_postgres_and_one_to_three_authorized_members(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError):
        deployment.validate_deployment()
    monkeypatch.setenv("DATABASE_URL", "postgresql://synthetic@ep-example-pooler.neon.tech/test")
    monkeypatch.setenv("DATABASE_MIGRATION_URL", "postgresql://synthetic@ep-example.neon.tech/test")
    monkeypatch.setenv("CORS_ORIGINS", "https://websecai.example.workers.dev")
    with pytest.raises(RuntimeError):
        deployment.validate_deployment()
    for members in ("alice@example.com", "alice@example.com,bob@example.com", "alice@example.com,bob@example.com,carol@example.com"):
        monkeypatch.setenv("APP_ALLOWED_EMAILS", members)
        deployment.validate_deployment()
    monkeypatch.setenv("APP_ALLOWED_EMAILS", "alice@example.com,bob@example.com,carol@example.com,dave@example.com")
    with pytest.raises(RuntimeError):
        deployment.validate_deployment()


@pytest.mark.parametrize("members", ["bob@example.com", "bob@example.com,carol@example.com,dave@example.com"])
def test_public_registration_closed_and_existing_nonmember_denied(client, accounts, monkeypatch, members):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ALLOWED_EMAILS", members)
    response = client.post("/api/v1/auth/register", json={"username": "carol", "email": "carol@example.com", "password": "synthetic-password"})
    assert response.status_code == 403
    assert client.get("/api/v1/users/me", headers=accounts[0]).status_code == 403
    assert client.get("/api/v1/users/me", headers=accounts[1]).status_code == 200


def test_login_attempt_budget(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(deployment, "_attempts", {})
    for _ in range(10):
        deployment.auth_attempt("local-test", "alice")
    with pytest.raises(HTTPException) as exc:
        deployment.auth_attempt("another-test", "alice")
    assert exc.value.status_code == 429


def test_concurrent_first_budget_reservation_is_atomic():
    barrier = Barrier(6)
    def attempt(_):
        barrier.wait()
        try:
            providers.reserve("deployment-concurrency", 3)
            return True
        except providers.SourceError:
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert sum(pool.map(attempt, range(6))) == 3
    with SessionLocal() as db:
        row = db.query(Usage).filter_by(provider="deployment-concurrency").one()
        assert row.count == 3


def test_postgres_json_utc_ids_and_cascade(client, accounts):
    if engine.dialect.name != "postgresql":
        pytest.skip("Prova de tipos exige PostgreSQL real")
    response = client.post("/api/v1/investigations", headers=accounts[0], json={"demo": True})
    assert response.status_code == 202
    investigation_id = response.json()["id"]
    with SessionLocal() as db:
        inv = db.get(Investigation, investigation_id)
        assert inv.created_at.utcoffset().total_seconds() == 0
        assert isinstance(inv.options, dict) and inv.is_demo is True
        assert inv.runs and all(isinstance(run.id, int) for run in inv.runs)
        assert inv.evidence and isinstance(inv.evidence[0].meta, dict)
    assert client.delete("/api/v1/investigations/" + investigation_id, headers=accounts[0]).status_code == 204
    with SessionLocal() as db:
        assert db.query(Evidence).filter_by(investigation_id=investigation_id).count() == 0
