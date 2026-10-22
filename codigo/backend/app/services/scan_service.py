import json
from urllib.parse import urlparse
from app.core.targets import parse_target, resolve_public
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.scan import Scan
from app.models.user import User
from app.services.analyzers.dns_analyzer import analyze_dns
from app.services.analyzers.http_analyzer import analyze_http
from app.services.analyzers.public_files_analyzer import analyze_public_files
from app.services.analyzers.score_service import calculate_score
from app.services.analyzers.tls_analyzer import analyze_tls


def normalize_target(url: str) -> tuple[str, str]:
    target = parse_target(url)
    return target.url, target.host


def run_website_analysis(url: str) -> dict:
    normalized_url, domain = normalize_target(url)
    resolve_public(domain, 443)
    details = {
        "input_url": url,
        "normalized_url": normalized_url,
        "domain": domain,
        "dns": analyze_dns(domain),
        "tls": analyze_tls(domain),
        "http": analyze_http(domain),
        "public_files": analyze_public_files(domain),
    }
    score_result = calculate_score(details)
    return {**score_result, "url": normalized_url, "domain": domain, "details": details}


def create_scan(db: Session, user: User, url: str) -> Scan:
    result = run_website_analysis(url)
    scan = Scan(
        user_id=user.id,
        url=result["url"],
        domain=result["domain"],
        score=result["score"],
        risk_level=result["risk_level"],
        summary=result["summary"],
        details_json=json.dumps(result["details"], ensure_ascii=False),
    )
    db.add(scan)
    db.flush()
    for item in result["findings"]:
        db.add(Finding(scan_id=scan.id, **item))
    db.commit()
    db.refresh(scan)
    return scan


def scan_to_detail(scan: Scan) -> dict:
    try:
        details = json.loads(scan.details_json or "{}")
    except json.JSONDecodeError:
        details = {}
    return {
        "id": scan.id,
        "url": scan.url,
        "domain": scan.domain,
        "created_at": scan.created_at,
        "score": scan.score,
        "risk_level": scan.risk_level,
        "summary": scan.summary,
        "details": details,
        "findings": scan.findings,
        "findings_count": len(scan.findings),
    }
