from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import secrets
import jwt
from sqlalchemy import inspect, select, text
from app.core.config import token_secret
from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal, engine
from app.db.migrate import upgrade_schema
from app.models.account_action import AccountAction
from app.models.user import User
from app.services.account_access import issue_account_link, digest_token

OLD = "synthetic-old-password-only"
NEW = "synthetic-new-password-only"
OTHER = "synthetic-other-password-only"


def create_user(client, name="owner"):
    assert client.post("/api/v1/auth/register", json={"username": name, "email": name + "@example.com", "password": OLD}).status_code == 200
    return client.post("/api/v1/auth/login", json={"username_or_email": name, "password": OLD}).json()["access_token"]


def link_for(email, purpose="reset", name=""):
    with SessionLocal() as db:
        return issue_account_link(db, email, purpose, name)


def payload(token, password=NEW):
    return {"token": token, "new_password": password, "confirmation": password}


def test_invite_defines_private_password_and_requires_normal_login(client):
    token = link_for("new@example.com", "invite", "new-member")
    with SessionLocal() as db:
        account = db.scalar(select(User).where(User.email == "new@example.com"))
        identifier = account.id
        assert not account.password_ready
        action = db.get(AccountAction, digest_token(token))
        assert action.token_hash != token and action.purpose == "invite"
    assert client.post("/api/v1/auth/login", json={"username_or_email": "new-member", "password": NEW}).status_code == 401
    result = client.post("/api/v1/auth/password/reset", json=payload(token))
    assert result.status_code == 204 and not result.content
    assert result.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/users/me").status_code == 401
    session = client.post("/api/v1/auth/login", json={"username_or_email": "new@example.com", "password": NEW})
    assert session.status_code == 200
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + session.json()["access_token"]}).json()["id"] == identifier
    assert client.post("/api/v1/auth/password/reset", json=payload(token, OTHER)).status_code == 400


def test_change_revokes_all_old_sessions_preserves_dossiers_and_other_users(client):
    token = create_user(client)
    other = create_user(client, "second")
    headers = {"Authorization": "Bearer " + token}
    dossier = client.post("/api/v1/investigations", json={"target": "loja-exemplo.example", "demo": True}, headers=headers)
    assert dossier.status_code == 202, dossier.text
    dossier_id = dossier.json()["id"]
    link = link_for("owner@example.com")
    response = client.post("/api/v1/auth/password/change", json={"current_password": OLD, "new_password": NEW, "confirmation": NEW}, headers=headers)
    assert response.status_code == 204, response.text
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + other}).status_code == 200
    assert client.post("/api/v1/auth/password/reset", json=payload(link, OTHER)).status_code == 400
    assert client.post("/api/v1/auth/login", json={"username_or_email": "owner", "password": OLD}).status_code == 401
    session = client.post("/api/v1/auth/login", json={"username_or_email": "owner", "password": NEW}).json()["access_token"]
    assert client.get("/api/v1/investigations/" + dossier_id, headers={"Authorization": "Bearer " + session}).status_code == 200
    assert client.get("/api/v1/investigations/" + dossier_id, headers={"Authorization": "Bearer " + other}).status_code == 404


def test_change_wrong_current_mismatch_reuse_and_unauthenticated(client):
    token = create_user(client)
    headers = {"Authorization": "Bearer " + token}
    base = {"current_password": OLD, "new_password": NEW, "confirmation": NEW}
    assert client.post("/api/v1/auth/password/change", json=base).status_code == 401
    for altered in [{"current_password": "incorrect-password"}, {"confirmation": OTHER}, {"new_password": OLD, "confirmation": OLD}]:
        assert client.post("/api/v1/auth/password/change", json=base | altered, headers=headers).status_code == 400
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


def test_reset_link_expires_and_reissuing_does_not_lock_out_user(client):
    token = create_user(client)
    first = link_for("owner@example.com")
    latest = link_for("owner@example.com")
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + token}).status_code == 200
    assert client.post("/api/v1/auth/password/reset", json=payload(first)).status_code == 400
    with SessionLocal() as db:
        db.get(AccountAction, digest_token(latest)).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.post("/api/v1/auth/password/reset", json=payload(latest)).status_code == 400
    assert client.post("/api/v1/auth/login", json={"username_or_email": "owner", "password": OLD}).status_code == 200


def test_reset_revokes_legacy_tokens_and_current_tokens(client):
    token = create_user(client)
    with SessionLocal() as db:
        identifier = db.scalar(select(User.id).where(User.username == "owner"))
    legacy = jwt.encode({"sub": str(identifier), "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, token_secret(), algorithm="HS256")
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + legacy}).status_code == 200
    link = link_for("owner@example.com")
    assert client.post("/api/v1/auth/password/reset", json=payload(link)).status_code == 204
    for old_token in (token, legacy):
        assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + old_token}).status_code == 401


def test_bad_links_are_generic_and_do_not_enumerate_accounts(client):
    response = client.post("/api/v1/auth/password/reset", json=payload(secrets.token_urlsafe(32)))
    assert response.status_code == 400
    assert "Link inválido" in response.json()["detail"]
    assert "@" not in response.text


def test_removed_member_cannot_redeem_or_change(client, monkeypatch):
    token = create_user(client)
    link = link_for("owner@example.com")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ALLOWED_EMAILS", "other@example.com")
    assert client.post("/api/v1/auth/password/reset", json=payload(link)).status_code == 403
    assert client.post("/api/v1/auth/password/change", headers={"Authorization": "Bearer " + token}, json={"current_password": OLD, "new_password": NEW, "confirmation": NEW}).status_code == 403
    monkeypatch.setenv("APP_ENV", "local")
    assert client.post("/api/v1/auth/password/reset", json=payload(link)).status_code == 204


def test_password_validation_does_not_consume_link(client):
    create_user(client)
    link = link_for("owner@example.com")
    assert client.post("/api/v1/auth/password/reset", json=payload(link, "short")).status_code == 422
    assert client.post("/api/v1/auth/password/reset", json=payload(link) | {"confirmation": OTHER}).status_code == 400
    assert client.post("/api/v1/auth/password/reset", json=payload(link)).status_code == 204


def test_latest_invite_only_and_active_account_is_never_overwritten(client):
    first = link_for("new@example.com", "invite", "new-member")
    latest = link_for("new@example.com", "invite", "ignored-new-name")
    assert client.post("/api/v1/auth/password/reset", json=payload(first)).status_code == 400
    assert client.post("/api/v1/auth/password/reset", json=payload(latest)).status_code == 204
    import pytest
    with pytest.raises(ValueError):
        link_for("new@example.com", "invite", "replace-account")
    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.email == "new@example.com")).username == "new-member"


def test_old_schema_upgrade_preserves_existing_user():
    from alembic import command
    from alembic.config import Config
    from app.core.config import ROOT
    # The isolated test DB only. Simulate an actual pre-feature v7 schema.
    with engine.begin() as db:
        AccountAction.__table__.drop(db, checkfirst=True)
        db.execute(text("ALTER TABLE users DROP COLUMN auth_version"))
        db.execute(text("ALTER TABLE users DROP COLUMN password_ready"))
        db.execute(text("INSERT INTO users (id, username, email, password_hash, created_at) VALUES (27, 'legacy-account', 'legacy@example.com', :digest, :stamp)"), {"digest": hash_password(OLD), "stamp": datetime.now(timezone.utc)})
    command.stamp(Config(str(ROOT / "alembic.ini")), "20261021_01")
    upgrade_schema()
    upgrade_schema()
    with SessionLocal() as db:
        user = db.get(User, 27)
        assert user.username == "legacy-account" and user.auth_version == 0 and user.password_ready
        assert verify_password(OLD, user.password_hash)
    assert "account_actions" in inspect(engine).get_table_names()


def test_concurrent_redemption_only_one_succeeds(client):
    create_user(client)
    token = link_for("owner@example.com")
    from app.services.account_access import redeem_account_link
    from fastapi import HTTPException
    def redeem(password):
        with SessionLocal() as db:
            try:
                redeem_account_link(db, token, password, password)
                return True
            except HTTPException:
                return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(redeem, [NEW, OTHER]))
    assert sorted(results) == [False, True]
