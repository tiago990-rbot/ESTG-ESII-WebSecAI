import socket
import ssl
from datetime import datetime, timezone
from app.core.targets import connect_public


def analyze_tls(domain: str) -> dict:
    result = {
        "https_supported": False,
        "tls_ok": False,
        "issuer": None,
        "subject": None,
        "valid_from": None,
        "valid_to": None,
        "days_remaining": None,
        "expired": None,
        "hostname_match": None,
        "error": None,
    }
    try:
        context = ssl.create_default_context()
        with connect_public(domain, 443) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        result["https_supported"] = True
        result["tls_ok"] = True
        issuer_parts = cert.get("issuer", [])
        subject_parts = cert.get("subject", [])
        issuer = ", ".join("=".join(item) for part in issuer_parts for item in part)
        subject = ", ".join("=".join(item) for part in subject_parts for item in part)
        not_before = cert.get("notBefore")
        not_after = cert.get("notAfter")
        valid_from = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc) if not_before else None
        valid_to = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc) if not_after else None
        days_remaining = (valid_to - datetime.now(timezone.utc)).days if valid_to else None
        result.update({
            "issuer": issuer or None,
            "subject": subject or None,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "valid_to": valid_to.isoformat() if valid_to else None,
            "days_remaining": days_remaining,
            "expired": days_remaining is not None and days_remaining < 0,
            "hostname_match": True,
        })
    except ssl.SSLCertVerificationError as exc:
        result.update({"https_supported": True, "tls_ok": False, "hostname_match": False if exc.verify_code == 62 else None, "expired": True if exc.verify_code == 10 else None, "error": str(exc)[:200]})
    except Exception as exc:
        result["error"] = str(exc)
    return result
