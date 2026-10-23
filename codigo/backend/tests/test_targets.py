from types import SimpleNamespace
import socket
import pytest
from app.core import targets
from app.services.analyzers import http_analyzer

@pytest.mark.parametrize("raw", [
    "https://example.com:0",
    "http://[64:ff9b::7f00:1]", "http://[2002:7f00:0001::1]", "http://[64:ff9b:1::1]",
    "http://localhost", "http://127.0.0.1", "http://10.0.0.1", "http://[::1]", "http://[::ffff:127.0.0.1]",
    "https://user:pass@example.com", "ftp://example.com", "https://example.com:8000",
    "https://example.com\\@localhost", "https://example.com\n/path", "http://999.1.1.1", "http://demo.internal",
])
def test_rejects_invalid_or_private(raw):
    with pytest.raises(ValueError):
        targets.parse_target(raw)

def test_normalization_minimizes_query():
    target = targets.parse_target("https://EXAMPLE.COM:443/a?token=private#fragment")
    assert target.url == "https://example.com/a"
    assert target.host == "example.com"

def test_public_ipv6():
    assert targets.parse_target("https://[2606:4700:4700::1111]/").host == "2606:4700:4700::1111"

def test_dns_mixed_private_rejected_before_connection(monkeypatch):
    monkeypatch.setattr(targets.socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, "", ("93.184.216.34", 443)), (0, 0, 0, "", ("127.0.0.1", 443))])
    def forbidden(*a, **k):
        pytest.fail("Socket must not be opened")
    monkeypatch.setattr(targets.socket, "create_connection", forbidden)
    with pytest.raises(ValueError):
        targets.connect_public("example.com", 443)

def test_socket_is_pinned_to_resolved_public_ip(monkeypatch):
    monkeypatch.setattr(targets, "resolve_public", lambda *a: ["93.184.216.34"])
    calls = []
    monkeypatch.setattr(targets.socket, "create_connection", lambda address, **kwargs: calls.append(address) or object())
    targets.connect_public("example.com", 443)
    assert calls == [("93.184.216.34", 443)]

def test_redirect_is_revalidated(monkeypatch):
    sock = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(targets, "connect_public", lambda *a: sock)
    class Headers:
        def get_all(self, name): return []
    response = SimpleNamespace(status=302, headers=Headers(), getheaders=lambda: [("Location", "http://127.0.0.1/admin")])
    class Connection:
        def __init__(self, *a, **k): self.sock = None
        def request(self, *a, **k): pass
        def getresponse(self): return response
        def close(self): pass
    monkeypatch.setattr(targets.http.client, "HTTPConnection", Connection)
    with pytest.raises(ValueError):
        targets.public_get("http://example.com/")

def test_httponly_case_and_no_cookies(monkeypatch):
    response = targets.PublicResponse("https://example.com/", 200, {}, ["sid=synthetic; Secure; HttpOnly; SameSite=Lax"])
    monkeypatch.setattr(http_analyzer, "public_get", lambda *a: response)
    assert http_analyzer.analyze_http("example.com")["cookies"]["all_httponly"] is True
    response.cookie_headers = []
    cookies = http_analyzer.analyze_http("example.com")["cookies"]
    assert cookies["all_httponly"] is None
