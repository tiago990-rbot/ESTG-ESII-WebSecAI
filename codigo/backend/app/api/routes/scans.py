from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanComparison, ScanCreate, ScanCreated, ScanDetail, ScanListItem, ScanStats
from app.services.report_service import generate_scan_pdf
from app.services.scan_service import create_scan, scan_to_detail

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def _get_user_scan_or_404(db: Session, user: User, scan_id: int) -> Scan:
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan não encontrado")
    return scan


@router.post("", response_model=ScanCreated)
@router.post("/", response_model=ScanCreated)
def create_new_scan(data: ScanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not data.authorized:
        raise HTTPException(422, "Confirme que o website é seu ou que tem autorização para a análise técnica.")
    try:
        scan = create_scan(db, current_user, data.url)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return ScanCreated(message="Scan guardado com sucesso", scan_id=scan.id)


@router.get("", response_model=list[ScanListItem])
@router.get("/", response_model=list[ScanListItem])
def list_scans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scans = db.query(Scan).filter(Scan.user_id == current_user.id).order_by(Scan.created_at.desc()).all()
    return [
        ScanListItem(
            id=scan.id,
            url=scan.url,
            domain=scan.domain,
            created_at=scan.created_at,
            score=scan.score,
            risk_level=scan.risk_level,
            summary=scan.summary,
            findings_count=len(scan.findings),
        )
        for scan in scans
    ]


@router.get("/stats/overview", response_model=ScanStats)
def stats_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scans = db.query(Scan).filter(Scan.user_id == current_user.id).order_by(Scan.created_at.desc()).all()
    if not scans:
        return ScanStats(total_scans=0, average_score=0, best_score=None, worst_score=None, last_scan_date=None, top_domains=[])
    scores = [scan.score for scan in scans]
    counter = Counter(scan.domain for scan in scans)
    return ScanStats(
        total_scans=len(scans),
        average_score=round(sum(scores) / len(scores), 1),
        best_score=max(scores),
        worst_score=min(scores),
        last_scan_date=scans[0].created_at,
        top_domains=[{"domain": domain, "count": count} for domain, count in counter.most_common(5)],
    )


@router.get("/{scan_id}", response_model=ScanDetail)
def get_scan(scan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scan = _get_user_scan_or_404(db, current_user, scan_id)
    return scan_to_detail(scan)


@router.get("/{scan_id}/comparison", response_model=ScanComparison)
def compare_scan(scan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current = _get_user_scan_or_404(db, current_user, scan_id)
    previous = (
        db.query(Scan)
        .filter(Scan.user_id == current_user.id, Scan.domain == current.domain, Scan.created_at < current.created_at)
        .order_by(Scan.created_at.desc())
        .first()
    )
    current_findings = db.query(Finding).filter(Finding.scan_id == current.id).count()
    if not previous:
        return ScanComparison(
            current_scan_id=current.id,
            previous_scan_id=None,
            current_score=current.score,
            previous_score=None,
            score_delta=None,
            current_findings_count=current_findings,
            previous_findings_count=None,
            findings_delta=None,
            message="Ainda não existe uma análise anterior deste domínio para comparar.",
        )
    previous_findings = db.query(Finding).filter(Finding.scan_id == previous.id).count()
    return ScanComparison(
        current_scan_id=current.id,
        previous_scan_id=previous.id,
        current_score=current.score,
        previous_score=previous.score,
        score_delta=current.score - previous.score,
        current_findings_count=current_findings,
        previous_findings_count=previous_findings,
        findings_delta=current_findings - previous_findings,
        message="Comparação calculada com a análise anterior do mesmo domínio.",
    )


@router.get("/{scan_id}/report")
def report(scan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scan = _get_user_scan_or_404(db, current_user, scan_id)
    pdf = generate_scan_pdf(scan, scan.findings)
    headers = {"Content-Disposition": f'attachment; filename="websec-check-{scan.domain}-{scan.id}.pdf"'}
    return Response(content=pdf, media_type="application/pdf", headers=headers)
