"""Validate public destinations and pin network connections to vetted IPs."""
from dataclasses import dataclass
import http.client
import ipaddress
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit, urlunsplit, quote

@dataclass(frozen=True)
class Target:
    url: str
    host: str
    port: int
    scheme: str

def public_ip(raw: str) -> bool:
    ip = ipaddress.ip_address(raw)
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            return public_ip(str(ip.ipv4_mapped))
        # Transition mechanisms may route to IPv4 destinations hidden in IPv6.
        if ip.sixtofour or ip.teredo or ip in ipaddress.ip_network("64:ff9b::/96") or ip in ipaddress.ip_network("64:ff9b:1::/48"):
            return False
    return ip.is_global and not ip.is_multicast and not ip.is_reserved

def parse_target(raw: str) -> Target:
    raw = raw.strip()
    if not raw or len(raw) > 2000 or re.search(r"[\s\\\x00-\x1f\x7f]", raw):
        raise ValueError("Introduza um domínio ou URL HTTP/HTTPS válido.")
    if "://" not in raw:
        raw = "https://" + raw
    p = urlsplit(raw)
    if p.scheme.lower() not in {"http", "https"} or not p.hostname or p.username is not None or p.password is not None:
        raise ValueError("Apenas HTTP/HTTPS sem credenciais no URL.")
    host = p.hostname.rstrip(".").lower()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        if not public_ip(host):
            raise ValueError("Destinos locais, privados ou reservados não são permitidos.")
    else:
        if ":" in host or re.fullmatch(r"[\d.]+", host):
            raise ValueError("Endereço IP inválido.")
        host = host.encode("idna").decode("ascii")
        labels = host.split(".")
        if len(labels) < 2 or len(host) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in labels):
            raise ValueError("Nome de domínio inválido.")
        if host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
            raise ValueError("Destinos locais ou reservados não são permitidos.")
    port = p.port if p.port is not None else (443 if p.scheme == "https" else 80)
    if port != (443 if p.scheme == "https" else 80):
        raise ValueError("Apenas portas HTTP/HTTPS padrão.")
    authority = f"[{host}]" if ":" in host else host
    path = quote(p.path or "/", safe="/:@!$&'()*+,;=-._~%")
    return Target(urlunsplit((p.scheme, authority, path, "", "")), host, port, p.scheme)

def resolve_public(host: str, port: int) -> list[str]:
    try:
        ips = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
    except socket.gaierror as exc:
        raise ValueError("Não foi possível resolver o domínio.") from exc
    if not ips or any(not public_ip(ip) for ip in ips):
        raise ValueError("O domínio resolve para um destino não público.")
    return ips

def connect_public(host: str, port: int, timeout: float = 6):
    ips = resolve_public(host, port)
    last_error = None
    for ip in ips:
        try:
            return socket.create_connection((ip, port), timeout=timeout)
        except OSError as exc:
            last_error = exc
    raise OSError("Destino indisponível.") from last_error

@dataclass
class PublicResponse:
    url: str
    status_code: int
    headers: dict
    cookie_headers: list[str]

def public_get(url: str, max_redirects: int = 4) -> PublicResponse:
    for hop in range(max_redirects + 1):
        target = parse_target(url)
        connection = http.client.HTTPConnection(target.host, target.port, timeout=6)
        raw_socket = connect_public(target.host, target.port)
        try:
            connection.sock = ssl.create_default_context().wrap_socket(raw_socket, server_hostname=target.host) if target.scheme == "https" else raw_socket
            connection.request("GET", urlsplit(target.url).path or "/", headers={"Host": urlsplit(target.url).netloc, "User-Agent": "WebSecAI/0.1 Academic", "Accept": "*/*", "Connection": "close"})
            response = connection.getresponse()
            headers = {k.lower(): v for k, v in response.getheaders()}
            cookies = response.headers.get_all("Set-Cookie") or []
            if response.status in {301, 302, 303, 307, 308} and headers.get("location"):
                if hop == max_redirects:
                    raise ValueError("Limite de redirecionamentos atingido.")
                url = urljoin(target.url, headers["location"])
                continue
            return PublicResponse(target.url, response.status, headers, cookies)
        finally:
            connection.close()
            raw_socket.close()
    raise ValueError("Redirecionamento inválido.")
