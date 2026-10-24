import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.core.config import value
from app.core.security import get_current_user
from app.core.targets import parse_target
from app.db.session import get_db
from app.models.user import User
from app.models.investigation import Investigation, ProviderRun, AIReport, EvidenceReview
from app.schemas.investigation import InvestigationCreate, Question, RetryRequest, EvidenceReviewCreate
from app.services import providers, ai_service
from app.services.investigation_service import detail, run_investigation, run_retry
from app.services.privacy import redact
from app.services.investigation_pdf import investigation_pdf

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])

def owned(db, user, investigation_id):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id, Investigation.user_id == user.id).first()
    if inv is None:
        raise HTTPException(404, "Investigação não encontrada")
    return inv

@router.get("/providers")
def provider_status(current_user: User = Depends(get_current_user)):
    return {"providers": providers.configuration(), "demo_enabled": value("ALLOW_DEMO", "true").lower() == "true"}

@router.post("", status_code=202)
def create(data: InvestigationCreate, tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    active = db.query(Investigation).filter(Investigation.user_id == user.id, Investigation.status.in_(["queued", "running"])).count()
    recent = db.query(Investigation).filter(Investigation.user_id == user.id, Investigation.created_at > datetime.now(timezone.utc) - timedelta(minutes=1)).count()
    if active >= 2 or recent >= 6:
        raise HTTPException(429, "Limite de investigações em curso ou frequência atingido. Aguarde.")
    if data.demo and value("ALLOW_DEMO", "true").lower() != "true":
        raise HTTPException(403, "Demonstrações desativadas nesta instalação.")
    if data.demo:
        target, domain = "https://loja-exemplo.example/", "loja-exemplo.example"
    elif data.kind == "domain":
        try:
            parsed = parse_target(data.target)
            target, domain = parsed.url, parsed.host
        except (ValueError, UnicodeError) as exc:
            raise HTTPException(422, str(exc)) from exc
    else:
        target, domain = "Mensagem suspeita", ""
    inv = Investigation(id=str(uuid.uuid4()), user_id=user.id, target=target, domain=domain, kind=data.kind, organization=redact(data.organization), options={"technical": data.technical, "product": data.product.strip(), "optional_sources": sorted(set(data.optional_sources))}, is_demo=data.demo, status="queued")
    db.add(inv)
    db.commit()
    tasks.add_task(run_investigation, inv.id, redact(data.message))
    return {"id": inv.id, "status": inv.status}

@router.get("")
def list_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Investigation).filter(Investigation.user_id == user.id).order_by(Investigation.created_at.desc()).limit(100).all()
    return [{k: detail(row)[k] for k in ("id", "target", "domain", "kind", "status", "is_demo", "created_at")} for row in rows]

@router.get("/{investigation_id}")
def get_one(investigation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return detail(owned(db, user, investigation_id))


@router.post("/{investigation_id}/retry", status_code=202)
def retry(investigation_id: str, data: RetryRequest, tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = owned(db, user, investigation_id)
    snapshot = detail(inv)
    if inv.is_demo or data.provider not in snapshot["retryable_providers"]:
        raise HTTPException(409, "Este módulo não pode ser repetido agora. Apenas falhas, interrupções e sínteses desatualizadas são elegíveis.")
    if data.provider == "technical" and not data.authorized:
        raise HTTPException(422, "Confirme novamente que este website é próprio ou autorizado.")
    active = db.query(Investigation).filter(Investigation.user_id == user.id, Investigation.status.in_(["queued", "running"])).count()
    stamp = datetime.now(timezone.utc).timestamp()
    history = [t for t in inv.options.get("retry_history", []) if isinstance(t, (int, float)) and t > stamp - 60]
    if active >= 2 or len(history) >= 6:
        raise HTTPException(429, "Limite de novas tentativas atingido. Aguarde antes de repetir.")
    previous_status, previous_finish = inv.status, inv.finished_at
    options = dict(inv.options, retry_history=history + [stamp])
    db.rollback()
    # Compare-and-set rejects a second caller even if it read the same completed snapshot.
    changed = db.execute(update(Investigation).where(Investigation.id == investigation_id, Investigation.user_id == user.id, Investigation.status == previous_status, Investigation.finished_at == previous_finish).values(status="queued", finished_at=None, options=options).execution_options(synchronize_session=False)).rowcount
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "A investigação mudou ou já está a ser repetida. Atualize o painel.")
    run = db.query(ProviderRun).filter(ProviderRun.investigation_id == investigation_id, ProviderRun.provider == data.provider).first()
    if run is None:
        run = ProviderRun(investigation_id=investigation_id, provider=data.provider, status="queued")
        db.add(run)
    run.status, run.message, run.observed_at = "queued", "Nova tentativa em fila apenas para este módulo.", datetime.now(timezone.utc)
    if data.provider != "ai":
        ai_run = db.query(ProviderRun).filter(ProviderRun.investigation_id == investigation_id, ProviderRun.provider == "ai").first()
        if ai_run is not None and ai_run.status == "success":
            ai_run.status, ai_run.message = "stale", "As fontes estão a ser revistas. A síntese anterior requer atualização."
    db.commit()
    tasks.add_task(run_retry, investigation_id, data.provider)
    return {"id": investigation_id, "provider": data.provider, "status": "queued"}

@router.post("/{investigation_id}/evidence/{evidence_id}/reviews", status_code=201)
def review_evidence(investigation_id: str, evidence_id: str, data: EvidenceReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Lock the parent to serialize annotations with retry admission on PostgreSQL.
    inv = db.query(Investigation).filter(Investigation.id == investigation_id, Investigation.user_id == user.id).with_for_update().first()
    if inv is None:
        raise HTTPException(404, "Investigação não encontrada")
    if inv.status in {"queued", "running"}:
        raise HTTPException(409, "Aguarde pelo fim da recolha antes de rever evidências.")
    entry = next((entry for entry in inv.evidence if entry.id == evidence_id), None)
    if entry is None:
        raise HTTPException(404, "Evidência não encontrada")
    previous = entry.reviews[-1].id if entry.reviews else None
    if previous != data.previous_review_id:
        raise HTTPException(409, "A revisão mudou. Atualize o dossiê antes de guardar.")
    from app.services.evidence_reviews import fingerprint
    from app.services.investigation_service import evidence_dict
    snapshot = evidence_dict(entry)
    db.add(EvidenceReview(evidence_id=entry.id, author_id=user.id, status=data.status, identity_status=data.identity_status, note=redact(data.note.strip()), evidence_hash=fingerprint(snapshot)))
    db.commit()
    db.expire_all()
    return detail(owned(db, user, investigation_id))


@router.delete("/{investigation_id}", status_code=204)
def remove(investigation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = owned(db, user, investigation_id)
    if inv.status in {"queued", "running"}:
        raise HTTPException(409, "Aguarde pela conclusão antes de remover.")
    db.delete(inv)
    db.commit()
    return Response(status_code=204)

@router.post("/{investigation_id}/questions")
def ask(investigation_id: str, data: Question, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = owned(db, user, investigation_id)
    if inv.is_demo:
        raise HTTPException(409, "O exemplo demonstrativo não faz chamadas a IA. Use uma investigação real com a integração configurada.")
    if inv.status in {"queued", "running"}:
        raise HTTPException(409, "Aguarde pela conclusão da investigação.")
    snapshot = detail(inv)
    if not snapshot["reports"] or not snapshot["reports"][-1]["is_current"]:
        raise HTTPException(409, "Atualize primeiro a síntese para as evidências e cobertura atuais.")
    if len(inv.reports) >= 6:
        raise HTTPException(429, "Limite de perguntas desta investigação atingido.")
    db.rollback()
    try:
        report, model = ai_service.generate(snapshot["evidence"], snapshot["target"], snapshot["runs"], data.text)
    except providers.SourceError as exc:
        raise HTTPException(503, exc.message) from exc
    except Exception as exc:
        raise HTTPException(502, "A IA não devolveu uma resposta válida; as evidências continuam disponíveis.") from exc
    current = detail(owned(db, user, investigation_id))
    digest = ai_service.context_hash(snapshot["evidence"], snapshot["runs"])
    if current["status"] in {"queued", "running"} or ai_service.context_hash(current["evidence"], current["runs"]) != digest:
        raise HTTPException(409, "As fontes mudaram durante a resposta. A síntese não foi guardada; atualize o painel.")
    db.add(AIReport(investigation_id=investigation_id, model=model, prompt_version=ai_service.PROMPT_VERSION, evidence_hash=digest, report=report))
    db.commit()
    return {"model": model, "report": report}

@router.get("/{investigation_id}/report")
def report(investigation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = owned(db, user, investigation_id)
    return Response(content=investigation_pdf(detail(inv)), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="websecai-{inv.id}.pdf"'})

@router.get("/{investigation_id}/comparison")
def compare(investigation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = owned(db, user, investigation_id)
    previous = db.query(Investigation).filter(Investigation.user_id == user.id, Investigation.domain == inv.domain, Investigation.kind == inv.kind, Investigation.is_demo == inv.is_demo, Investigation.created_at < inv.created_at, Investigation.status.in_(["completed", "partial"])).order_by(Investigation.created_at.desc()).first() if inv.kind == "domain" else None
    if previous is None:
        return {"previous_id": None, "added": [], "removed": [], "message": "Sem investigação anterior comparável."}
    def key(e):
        return (e.provider, e.category, e.source_url, e.title, e.meta.get("cve", ""))
    a, b = {key(e): e for e in previous.evidence if e.category != "kev_general" and not e.meta.get("not_returned_in_latest_success")}, {key(e): e for e in inv.evidence if e.category != "kev_general" and not e.meta.get("not_returned_in_latest_success")}
    return {"previous_id": previous.id, "added": [b[k].title for k in b.keys() - a.keys()], "removed": [a[k].title for k in a.keys() - b.keys()], "message": "Diferenças entre evidências recolhidas. Alterações de cobertura podem explicar os resultados."}
