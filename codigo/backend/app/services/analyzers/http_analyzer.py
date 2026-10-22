from http.cookies import SimpleCookie
from app.core.targets import public_get
SECURITY_HEADERS = {"strict-transport-security": "hsts", "content-security-policy": "csp", "x-content-type-options": "x_content_type_options", "referrer-policy": "referrer_policy", "permissions-policy": "permissions_policy", "x-frame-options": "x_frame_options"}

def analyze_http(domain: str) -> dict:
    authority = f"[{domain}]" if ":" in domain else domain
    result = {"http_ok": False, "https_ok": False, "status_code": None, "final_url": None, "http_to_https_redirect": None, "headers": {}, "cookies": {"has_cookies": False, "total": 0, "all_secure": None, "all_httponly": None, "all_samesite": None}, "error": None}
    response = None
    try:
        response = public_get(f"http://{authority}/")
        result["http_ok"] = True
        result["http_to_https_redirect"] = response.url.startswith("https://")
    except (OSError, ValueError) as exc:
        result["error"] = str(exc)[:200]
    try:
        response = public_get(f"https://{authority}/")
        result["https_ok"] = True
    except (OSError, ValueError) as exc:
        result["error"] = str(exc)[:200]
    if response is None:
        return result
    cookie_list = []
    for raw in response.cookie_headers:
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
            cookie_list.extend(cookie.values())
        except Exception:
            continue
    result.update({"status_code": response.status_code, "final_url": response.url, "headers": {short: name in response.headers for name, short in SECURITY_HEADERS.items()}})
    result["headers"].update({"server_header": response.headers.get("server"), "x_powered_by": response.headers.get("x-powered-by")})
    result["cookies"] = {"has_cookies": bool(cookie_list), "total": len(cookie_list), "all_secure": all(bool(c["secure"]) for c in cookie_list) if cookie_list else None, "all_httponly": all(bool(c["httponly"]) for c in cookie_list) if cookie_list else None, "all_samesite": all(bool(c["samesite"]) for c in cookie_list) if cookie_list else None}
    return result
