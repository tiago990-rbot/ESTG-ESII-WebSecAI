import os
from pathlib import Path
import secrets
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
cache = ROOT / ".cache" / "tests"
cache.mkdir(parents=True, exist_ok=True)
DB = cache / ("suite-" + secrets.token_hex(6) + ".db")
assert DB.resolve().is_relative_to(ROOT.resolve())
postgres_test = os.environ.get("TEST_DATABASE_URL", "")
if postgres_test:
    from sqlalchemy.engine import make_url
    test_url = make_url(postgres_test)
    if test_url.host not in {"127.0.0.1", "localhost"} or not (test_url.database or "").startswith("websecai_test_"):
        raise RuntimeError("A suite destrutiva só aceita PostgreSQL local com nome websecai_test_*.")
    os.environ["DATABASE_URL"] = postgres_test
    os.environ["DATABASE_MIGRATION_URL"] = postgres_test
else:
    os.environ["DATABASE_URL"] = "sqlite:///" + DB.as_posix()
    os.environ["DATABASE_MIGRATION_URL"] = ""
os.environ["APP_ENV"] = "local"
os.environ["JWT_SECRET"] = secrets.token_urlsafe(48)
for key in ("TAVILY_API_KEY", "GROQ_API_KEY", "URLHAUS_AUTH_KEY", "PHISHTANK_API_KEY", "HIBP_API_KEY", "HIBP_VERIFIED_DOMAINS", "URLSCAN_API_KEY", "PHISHTANK_ANONYMOUS_ENABLED", "TI_ACCEPTANCE_ENABLED"):
    os.environ[key] = ""
for key in ("PHISHTANK_DAILY_LIMIT", "HIBP_CATALOG_DAILY_LIMIT", "URLSCAN_DAILY_LIMIT"):
    os.environ[key] = "0"
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.services import providers

@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    if postgres_test:
        assert engine.url.host in {"127.0.0.1", "localhost"} and engine.url.database.startswith("websecai_test_")
    else:
        assert Path(engine.url.database).resolve() == DB.resolve()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected external request in offline test")
    monkeypatch.setattr(providers, "json_request", no_network)
    monkeypatch.setattr(providers, "kev_catalog", lambda: ({"vulnerabilities": [{"cveID": "CVE-2024-0001", "vendorProject": "TestVendor", "product": "TestProduct", "vulnerabilityName": "Fixture only", "dateAdded": "2026-01-01", "shortDescription": "Synthetic test fixture", "requiredAction": "Update"}]}, False, "2026-10-21T00:00:00+00:00"))
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def accounts(client):
    headers = []
    for name in ["alice", "bob"]:
        password = secrets.token_urlsafe(20)
        r = client.post("/api/v1/auth/register", json={"username": name, "email": name + "@example.com", "password": password})
        assert r.status_code == 200, r.text
        r = client.post("/api/v1/auth/login", json={"username_or_email": name, "password": password})
        assert r.status_code == 200
        headers.append({"Authorization": "Bearer " + r.json()["access_token"]})
    return headers
