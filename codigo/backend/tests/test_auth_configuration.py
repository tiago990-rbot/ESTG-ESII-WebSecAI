from app.core import deployment


def test_public_auth_configuration_matches_registration_policy_without_exposing_members(client, monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_EMAILS", "private-member@example.com")
    local = client.get("/api/v1/auth/configuration")
    assert local.status_code == 200
    assert local.json() == {"public_registration_enabled": True}

    monkeypatch.setenv("APP_ENV", "production")
    hosted = client.get("/api/v1/auth/configuration")
    assert hosted.status_code == 200
    assert hosted.json() == {"public_registration_enabled": False}
    assert "private-member" not in hosted.text
    assert deployment.production()
