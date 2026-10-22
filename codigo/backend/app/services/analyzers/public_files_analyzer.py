from app.core.targets import public_get


def _check_url(url: str) -> tuple[bool, int | None, str | None]:
    try:
        response = public_get(url)
        return response.status_code == 200, response.status_code, None
    except Exception as exc:
        return False, None, str(exc)


def analyze_public_files(domain: str) -> dict:
    robots_url = f"https://{domain}/robots.txt"
    sitemap_url = f"https://{domain}/sitemap.xml"
    robots_found, robots_status, robots_error = _check_url(robots_url)
    sitemap_found, sitemap_status, sitemap_error = _check_url(sitemap_url)
    return {
        "robots_txt_found": robots_found,
        "robots_status_code": robots_status,
        "robots_url": robots_url,
        "robots_error": robots_error,
        "sitemap_xml_found": sitemap_found,
        "sitemap_status_code": sitemap_status,
        "sitemap_url": sitemap_url,
        "sitemap_error": sitemap_error,
    }
