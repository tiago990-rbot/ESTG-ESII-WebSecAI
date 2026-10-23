from datetime import datetime, timezone
import hashlib
import json
import threading
import uuid
from sqlalchemy import update
from app.db.session import SessionLocal
from app.models.investigation import Investigation, ProviderRun, Evidence, AIReport
from app.services import providers, ai_service
from app.services.privacy import extract_links, message_signals
from app.services.scan_service import run_website_analysis
from app.core.targets import parse_target
from app.services.coverage import summarize_coverage, target_evidence
from app.services.incident_groups import candidate_groups
from app.services.intelligence import technical_records
from app.services.demo_report import demo_analysis

_worker_slots = threading.Semaphore(2)
RETRY_STATUSES = {"error", "partial", "not_configured", "access_denied", "rate_limited", "interrupted", "stale"}
RETRY_SOURCES = {"technical", "urlhaus", "phishtank", "osint", "exposure", "kev", "ai"}

def iso(date):
    return date.replace(tzinfo=date.tzinfo or timezone.utc).isoformat() if date else None

def evidence_dict(e):
    return {k: getattr(e, k) for k in ("id", "provider", "category", "title", "description", "source_url", "confirmation", "published_at", "event_at", "meta")} | {"observed_at": iso(e.observed_at)}

def detail(inv):
    evidence = [evidence_dict(e) for e in inv.evidence if not e.meta.get("not_returned_in_latest_success")]
    previous = [evidence_dict(e) for e in inv.evidence if e.meta.get("not_returned_in_latest_success")]
    runs = [{"provider": r.provider, "status": r.status, "message": r.message, "results_count": r.results_count, "observed_at": iso(r.observed_at)} for r in inv.runs]
    digest = ai_service.context_hash(evidence, runs)
    reports = [{"id": r.id, "model": r.model, "prompt_version": r.prompt_version, "report": r.report, "created_at": iso(r.created_at), "is_current": r.evidence_hash == digest} for r in sorted(inv.reports, key=lambda r: r.id)]
    grouping = candidate_groups(evidence, inv.domain)
    return {"id": inv.id, "target": inv.target, "domain": inv.domain, "kind": inv.kind, "organization": inv.organization, "status": inv.status, "is_demo": inv.is_demo, "created_at": iso(inv.created_at), "finished_at": iso(inv.finished_at), "technical": inv.technical, "message_analysis": inv.message_analysis, "runs": runs, "evidence": evidence, "previous_evidence": previous, "reports": reports, "coverage_summary": summarize_coverage(evidence, runs), "incident_grouping": grouping, "retryable_providers": retryable_sources(inv, evidence, runs, reports)}


def source_links(inv):
    raw = [inv.target] if inv.kind == "domain" else (inv.message_analysis or {}).get("links", [])
    links = []
    for link in raw[:3]:
        try:
            clean = parse_target(link).url
            if clean not in links:
                links.append(clean)
        except ValueError:
            continue
    return links


def applicable_sources(inv):
    names = {"kev", "ai"}
    if source_links(inv):
        names.update({"urlhaus", "phishtank", "osint", "exposure"})
    if inv.kind == "domain" and inv.options.get("technical"):
        names.add("technical")
    return names


def retryable_sources(inv, evidence, runs, reports):
    if inv.is_demo or inv.status in {"queued", "running"}:
        return []
    statuses = {r["provider"]: r["status"] for r in runs}
    eligible = []
    for name in applicable_sources(inv):
        if name == "ai" and not evidence:
            continue
        missing = name not in statuses and inv.status in {"interrupted", "error", "partial"}
        stale_ai = name == "ai" and bool(reports) and not reports[-1]["is_current"]
        newly_supported_ai = name == "ai" and statuses.get(name) == "no_results" and bool(target_evidence(evidence))
        if missing or stale_ai or newly_supported_ai or statuses.get(name) in RETRY_STATUSES:
            eligible.append(name)
    return sorted(eligible)

def persist_result(inv_id: str, provider: str, result: providers.Result, refresh=False):
    with SessionLocal() as db:
        inv = db.get(Investigation, inv_id)
        if inv is None:
            return
        run = next((r for r in inv.runs if r.provider == provider), None)
        if run is None:
            run = ProviderRun(investigation_id=inv_id, provider=provider, status="running")
            db.add(run)
        run.status, run.message, run.results_count, run.observed_at = result.status, result.message, len(result.evidence), datetime.now(timezone.utc)
        seen = set()
        old = {e.id: e for e in inv.evidence if e.provider == provider}
        observed = datetime.now(timezone.utc)
        for entry in result.evidence:
            fingerprint = provider + "|" + entry.get("source_url", "") + "|" + entry["title"] + "|" + str(entry.get("meta", {}).get("cve", ""))
            eid = str(uuid.uuid5(uuid.UUID(inv_id), fingerprint))
            if eid in seen:
                continue
            seen.add(eid)
            existing = old.get(eid)
            if existing is None:
                db.add(Evidence(id=eid, investigation_id=inv_id, provider=provider, **entry))
            elif refresh:
                for key, value in entry.items():
                    setattr(existing, key, value)
                existing.observed_at = observed
        if refresh:
            for eid, entry in old.items():
                if eid in seen or entry.meta.get("not_returned_in_latest_success"):
                    continue
                if result.status in {"success", "no_results"}:
                    entry.meta = dict(entry.meta, not_returned_in_latest_success=True, superseded_at=iso(observed))
                else:
                    entry.meta = dict(entry.meta, retained_from_earlier_attempt=True, latest_attempt_status=result.status)
        run.results_count = len(seen)
        db.commit()

def demo(inv_id: str):
    with SessionLocal() as db:
        inv = db.get(Investigation, inv_id)
        if inv is None:
            return
        combined = inv.options.get("technical", False) and inv.kind == "domain"
        if combined:
            inv.technical = {"score": 72, "risk_level": "medium", "summary": "Postura técnica fictícia, criada para demonstrar a apresentação conjunta com Threat Intelligence.", "details": {}, "findings": [
                {"title": "Content-Security-Policy não observada no exemplo", "description": "Resultado simulado de configuração; não prova vulnerabilidade explorável.", "recommendation": "Num sistema próprio, validar a política aplicável e testar a compatibilidade antes de a alterar.", "severity": "medium", "category": "headers"},
                {"title": "Atributos de cookies a rever no exemplo", "description": "Cenário fictício de atributo Secure por verificar.", "recommendation": "Num sistema autorizado, confirmar os atributos por cookie e o contexto de utilização.", "severity": "medium", "category": "cookies"},
            ]}
            technical = inv.technical
            db.commit()
    records = [
        ("osint", providers.item("incident_report", "Exemplo didático: incidente reportado", "Notícia fictícia para demonstrar a cronologia. Não descreve um incidente real.", published="2026-10-01", demo=True)),
        ("osint", providers.item("public_reference", "Exemplo didático: alegação num fórum", "Alegação fictícia, sem confirmação. Demonstra a distinção entre publicação e facto.", demo=True)),
        ("urlhaus", providers.item("malware", "Exemplo didático: sinalização de malware", "Indicador simulado. Nenhum domínio real foi consultado.", "https://urlhaus.abuse.ch/", "reported", demo=True)),
        ("kev", providers.item("kev_general", "Exemplo didático: alerta geral", "Sem CVE real e sem associação ao alvo. Demonstra a apresentação de alertas.", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", demo=True)),
    ]
    for provider in ("osint", "urlhaus", "kev"):
        persist_result(inv_id, provider, providers.Result("demo", "Dados demonstrativos, sem chamadas à fonte.", [entry for name, entry in records if name == provider]))
    if combined:
        entries = technical_records(technical, providers.item)
        for entry in entries:
            entry["meta"]["demo"] = True
        persist_result(inv_id, "technical", providers.Result("demo", "Configuração fictícia; não foram enviados pedidos ao alvo.", entries))
    with SessionLocal() as db:
        inv = db.get(Investigation, inv_id)
        if inv is None:
            return
        evidence = [evidence_dict(e) for e in inv.evidence]
        report = demo_analysis(evidence)
        snapshot = detail(inv)
        db.add(AIReport(investigation_id=inv_id, model="demonstracao-sem-LLM", prompt_version="demo-v2-intelligence", evidence_hash=ai_service.context_hash(evidence, snapshot["runs"]), report=ai_service.validated_report(report, evidence)))
        inv.status, inv.finished_at = "completed", datetime.now(timezone.utc)
        db.commit()
    persist_result(inv_id, "ai", providers.Result("demo", "Exemplo orientado por regras; não foi consultado um modelo de IA."))

def run_investigation(inv_id: str, message: str = ""):
    with _worker_slots:
        with SessionLocal() as db:
            inv = db.get(Investigation, inv_id)
            if inv is None:
                return
            inv.status = "running"
            db.commit()
            target, organization, kind, options, is_demo = inv.target, inv.organization, inv.kind, inv.options, inv.is_demo
        try:
            if is_demo:
                demo(inv_id)
                return
            if options.get("technical"):
                persist_result(inv_id, "technical", providers.Result("running", "A executar verificações técnicas autorizadas."))
                try:
                    technical = run_website_analysis(target)
                    with SessionLocal() as db:
                        inv = db.get(Investigation, inv_id)
                        if inv:
                            inv.technical = technical
                            db.commit()
                    entries = technical_records(technical, providers.item)
                    persist_result(inv_id, "technical", providers.Result("success", "Verificações técnicas concluídas; score de postura separado da reputação.", entries))
                except (OSError, ValueError):
                    persist_result(inv_id, "technical", providers.Result("error", "Análise técnica indisponível ou destino não permitido."))
            else:
                persist_result(inv_id, "technical", providers.Result("not_requested", "Pedidos técnicos ao alvo não foram solicitados."))
            links = [target] if kind == "domain" else extract_links(message)
            if kind == "message":
                signals = message_signals(message)
                with SessionLocal() as db:
                    inv = db.get(Investigation, inv_id)
                    if inv:
                        inv.message_analysis = signals
                        db.commit()
                persist_result(inv_id, "message", providers.Result("success", signals["limitation"], [providers.item("message_signal", "Sinal linguístico: " + s["code"], s["description"], confirmation="unverified") for s in signals["signals"]]))
            for name, function in [("urlhaus", providers.urlhaus), ("phishtank", providers.phishtank)]:
                if not links:
                    persist_result(inv_id, name, providers.Result("not_requested", "Sem URLs públicos válidos na mensagem."))
                    continue
                # Up to three URLs; no visits to those URLs.
                combined = providers.Result("no_results", "Sem correspondências nas consultas realizadas.")
                for link in links:
                    result = providers.guarded(function, link)
                    combined.evidence.extend(result.evidence)
                    combined.message = result.message
                    combined.status = result.status if result.status != "no_results" else combined.status
                    if result.status in {"not_configured", "access_denied", "rate_limited", "error"}:
                        break
                if combined.evidence and combined.status not in {"success", "demo"}:
                    combined.status = "partial"
                persist_result(inv_id, name, combined)
            if links:
                persist_result(inv_id, "osint", providers.guarded(providers.osint, links[0], organization))
                persist_result(inv_id, "exposure", providers.guarded(providers.exposure, parse_target(links[0]).host))
            else:
                persist_result(inv_id, "osint", providers.Result("not_requested", "Sem alvo público para pesquisa."))
                persist_result(inv_id, "exposure", providers.Result("not_requested", "Sem domínio para consulta."))
            persist_result(inv_id, "kev", providers.guarded(providers.kev, options.get("product", "")))
            with SessionLocal() as db:
                inv = db.get(Investigation, inv_id)
                if inv is None:
                    return
                snapshot = detail(inv)
            try:
                report, model = ai_service.generate(snapshot["evidence"], target, snapshot["runs"])
                with SessionLocal() as db:
                    if db.get(Investigation, inv_id) is not None:
                        db.add(AIReport(investigation_id=inv_id, model=model, prompt_version=ai_service.PROMPT_VERSION, evidence_hash=ai_service.context_hash(snapshot["evidence"], snapshot["runs"]), report=report))
                        db.commit()
                persist_result(inv_id, "ai", providers.Result("success", "Síntese gerada; referências validadas contra as evidências."))
            except providers.SourceError as exc:
                persist_result(inv_id, "ai", providers.Result(exc.status, exc.message))
            except Exception:
                persist_result(inv_id, "ai", providers.Result("error", "Não foi possível obter uma síntese válida. As evidências foram preservadas."))
            with SessionLocal() as db:
                inv = db.get(Investigation, inv_id)
                if inv:
                    incomplete = any(r.status not in {"success", "no_results", "not_requested"} for r in inv.runs)
                    inv.status, inv.finished_at = ("partial" if incomplete else "completed"), datetime.now(timezone.utc)
                    db.commit()
        except Exception:
            # No raw exceptions or provider bodies: they may contain request metadata.
            persist_result(inv_id, "system", providers.Result("error", "Investigação interrompida por erro interno. Os resultados anteriores foram preservados."))
            with SessionLocal() as db:
                inv = db.get(Investigation, inv_id)
                if inv:
                    inv.status, inv.finished_at = "error", datetime.now(timezone.utc)
                    db.commit()

def recover_interrupted():
    with SessionLocal() as db:
        db.execute(update(Investigation).where(Investigation.status.in_(["queued", "running"])).values(status="interrupted"))
        db.execute(update(ProviderRun).where(ProviderRun.status.in_(["queued", "running"])).values(status="interrupted", message="Execução interrompida pelo reinício. Pode repetir este módulo."))
        db.commit()


def retry_source_result(inv_id, provider, inv):
    links = source_links(inv)
    if provider == "technical":
        technical = run_website_analysis(inv.target)
        with SessionLocal() as db:
            current = db.get(Investigation, inv_id)
            current.technical = technical
            db.commit()
        entries = technical_records(technical, providers.item)
        return providers.Result("success", "Verificações técnicas autorizadas repetidas.", entries)
    if provider == "kev":
        return providers.guarded(providers.kev, inv.options.get("product", ""))
    if provider == "osint":
        return providers.guarded(providers.osint, links[0], inv.organization)
    if provider == "exposure":
        return providers.guarded(providers.exposure, parse_target(links[0]).host)
    function = {"urlhaus": providers.urlhaus, "phishtank": providers.phishtank}[provider]
    combined = providers.Result("no_results", "Sem correspondências nas consultas realizadas.")
    for link in links:
        result = providers.guarded(function, link)
        combined.evidence.extend(result.evidence)
        combined.message = result.message
        combined.status = result.status if result.status != "no_results" else combined.status
        if result.status in {"not_configured", "access_denied", "rate_limited", "error"}:
            break
    if combined.evidence and combined.status != "success":
        combined.status = "partial"
    return combined


def run_retry(inv_id: str, provider: str):
    with _worker_slots:
        with SessionLocal() as db:
            inv = db.get(Investigation, inv_id)
            if inv is None or inv.is_demo:
                return
            inv.status = "running"
            db.commit()
            snapshot = detail(inv)
            db.expunge(inv)
        persist_result(inv_id, provider, providers.Result("running", "A repetir apenas este módulo."))
        try:
            if provider == "ai":
                report, model = ai_service.generate(snapshot["evidence"], snapshot["target"], snapshot["runs"])
                with SessionLocal() as db:
                    db.add(AIReport(investigation_id=inv_id, model=model, prompt_version=ai_service.PROMPT_VERSION, evidence_hash=ai_service.context_hash(snapshot["evidence"], snapshot["runs"]), report=report))
                    db.commit()
                result = providers.Result("success", "Síntese atualizada para as evidências e cobertura atuais.")
            else:
                result = retry_source_result(inv_id, provider, inv)
        except providers.SourceError as exc:
            result = providers.Result(exc.status, exc.message)
        except Exception:
            result = providers.Result("error", "Não foi possível repetir este módulo. Os resultados anteriores foram preservados.")
        persist_result(inv_id, provider, result, refresh=True)
        with SessionLocal() as db:
            inv = db.get(Investigation, inv_id)
            states = {r.provider: r.status for r in inv.runs}
            complete = all(states.get(name) in {"success", "no_results", "not_requested"} for name in applicable_sources(inv))
            if inv.kind == "message" and inv.message_analysis is None:
                complete = False
            inv.status, inv.finished_at = ("completed" if complete else "partial"), datetime.now(timezone.utc)
            db.commit()
