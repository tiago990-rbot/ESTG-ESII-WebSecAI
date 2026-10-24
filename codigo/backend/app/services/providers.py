"""Read-only source adapters. Never visit a suspicious target or return provider secrets."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import threading
from urllib.parse import quote, urlsplit
import httpx
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from app.core.config import ROOT, value, number
from app.core.targets import parse_target
from app.db.session import SessionLocal
from app.models.investigation import Usage
from app.services.privacy import redact
from app.core.request_window import restricted_limit

@dataclass
class Result:
    status: str
    message: str
    evidence: list[dict] = field(default_factory=list)

class SourceError(Exception):
    def __init__(self, status="error", message="A fonte não respondeu corretamente.", diagnostics=None):
        self.status, self.message = status, message
        self.diagnostics = diagnostics or {}

def json_request(method: str, url: str, **kwargs):
    # All caller URLs are fixed provider endpoints, never user-selected hosts.
    with httpx.Client(timeout=httpx.Timeout(12, connect=5), follow_redirects=False, trust_env=False) as client:
        with client.stream(method, url, **kwargs) as response:
            if response.status_code in {429, 509}:
                raw_wait = response.headers.get("Retry-After", "60")
                wait = min(int(raw_wait), 86400) if raw_wait.isdigit() else 60
                raise SourceError("rate_limited", "Quota ou frequência da fonte atingida.", {"retry_after_seconds": max(1, wait)})
            if response.status_code == 509:
                raise SourceError("rate_limited", "Frequência da fonte atingida. Aguarde antes de repetir.")
            if response.status_code in {401, 403}:
                raise SourceError("access_denied", "Acesso recusado pela fonte; confirme chave, plano e permissões.")
            if response.status_code == 404:
                if url.startswith("https://haveibeenpwned.com/api/v3/breachedDomain/"):
                    raise SourceError("no_results", "A fonte não devolveu correspondências para esta consulta de domínio verificado.")
                raise SourceError("error", "O fornecedor devolveu HTTP 404. Não comprova autenticação nem uma consulta válida sem correspondências.")
            if response.status_code != 200:
                # Never relay an error body: it can contain prompts, generated text or credentials.
                reason = ""
                diagnostics = {"http_status": response.status_code}
                if response.status_code == 400 and url == "https://api.groq.com/openai/v1/chat/completions":
                    bounded = bytearray()
                    for chunk in response.iter_bytes():
                        bounded.extend(chunk)
                        if len(bounded) > 32_000:
                            break
                    try:
                        error = json.loads(bounded).get("error", {})
                        code = error.get("code")
                        if code in {"json_validate_failed", "json_schema_validation_failed"}:
                            reason = " O modelo não produziu o JSON exigido."
                            diagnostics["reason"] = "json_validation"
                            failed = error.get("failed_generation")
                            if isinstance(failed, str):
                                try:
                                    candidate = json.loads(failed)
                                    diagnostics["generated_json"] = True
                                    if isinstance(candidate, dict):
                                        from app.schemas.investigation import AnalystReport
                                        from pydantic import ValidationError
                                        try:
                                            AnalystReport.model_validate(candidate)
                                            diagnostics["local_schema_valid"] = True
                                        except ValidationError as exc:
                                            # Only fixed schema names and error categories, never input values.
                                            diagnostics["local_schema_valid"] = False
                                            fields = {"summary", "observations", "recommendations", "limitations", "text", "evidence_ids"}
                                            diagnostics["schema_errors"] = [{"type": entry["type"], "fields": [part for part in entry["loc"] if part in fields]} for entry in exc.errors()[:8]]
                                except json.JSONDecodeError as exc:
                                    diagnostics["generated_json"] = False
                                    diagnostics["json_error"] = exc.msg
                                    diagnostics["error_position"] = exc.pos
                                    diagnostics["characters"] = len(failed)
                                    diagnostics["starts_object"] = failed.lstrip().startswith("{")
                                    diagnostics["ends_object"] = failed.rstrip().endswith("}")
                                    diagnostics["has_code_fence"] = failed.lstrip().startswith("```")
                        elif code in {"context_length_exceeded", "model_not_found", "model_decommissioned"}:
                            reason = " Verifique a configuração do modelo e os limites de contexto."
                    except (ValueError, TypeError, AttributeError):
                        pass
                raise SourceError("error", "A fonte devolveu HTTP " + str(response.status_code) + "." + reason + " As evidências continuam disponíveis.", diagnostics)
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 6_000_000:
                    raise SourceError("error", "Resposta da fonte excedeu o limite de tamanho.")
            return json.loads(body)

def reserve(provider: str, limit: int, daily=False, minute=False):
    period = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M" if minute else "%Y-%m-%d" if daily else "%Y-%m")
    try:
        limit = restricted_limit(value("WEBSECAI_REQUEST_WINDOW_FILE"), provider, period, limit)
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        raise SourceError("rate_limited", "Janela autorizada terminada ou orçamento inválido. Não foi efetuada nova chamada.") from None
    with SessionLocal() as db:
        if db.get(Usage, (provider, period)) is None:
            db.add(Usage(provider=provider, period=period, count=0))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
        changed = db.execute(update(Usage).where(Usage.provider == provider, Usage.period == period, Usage.count < limit).values(count=Usage.count + 1)).rowcount
        db.commit()
        if not changed:
            raise SourceError("rate_limited", "Limite local de pedidos atingido; não foi efetuada nova chamada.")

def reserve_acceptance(provider):
    """Optional initial acceptance gate, durable in PostgreSQL, at most two reservations."""
    if value("TI_ACCEPTANCE_ENABLED", "false").lower() != "true":
        return
    period = value("TI_ACCEPTANCE_ID", "20261024")
    if not re.fullmatch(r"[0-9]{8}", period) or provider not in {"tavily", "groq", "urlhaus"}:
        raise SourceError("rate_limited", "Janela inicial de validação inválida. Não foi feita chamada.")
    name = "acceptance_" + provider
    with SessionLocal() as db:
        if db.get(Usage, (name, period)) is None:
            db.add(Usage(provider=name, period=period, count=0))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
        changed = db.execute(update(Usage).where(Usage.provider == name, Usage.period == period, Usage.count < 2).values(count=Usage.count + 1)).rowcount
        db.commit()
        if not changed:
            raise SourceError("rate_limited", "Orçamento inicial de duas consultas atingido. Não foi feita nova chamada; não reiniciar a janela automaticamente.")


def source_link(raw: str) -> str:
    try:
        target = parse_target(raw)
        query = urlsplit(raw).query
        if query and not re.search(r"(?i)(token|password|secret|auth|key|email|session)", query):
            return target.url + "?" + query[:500]
        return target.url
    except (ValueError, UnicodeError):
        return ""

def publication_date(raw):
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", raw):
            return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc).isoformat()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", raw):
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    return None


def item(category, title, description, url="", confirmation="unverified", published=None, **meta):
    return {"category": category, "title": redact(str(title))[:300], "description": redact(str(description))[:1600], "source_url": source_link(url) if url else "", "confirmation": confirmation, "published_at": publication_date(published), "event_at": None, "meta": meta}

def guarded(function, *args):
    try:
        return function(*args)
    except SourceError as exc:
        return Result(exc.status, exc.message)
    except (httpx.HTTPError, OSError, ValueError, KeyError, TypeError, AttributeError):
        return Result("error", "Fonte indisponível ou resposta inválida. Não se conclui ausência de ameaças.")

def urlhaus(target: str) -> Result:
    key = value("URLHAUS_AUTH_KEY")
    if not key:
        return Result("not_configured", "Fonte opcional sem chave de acesso. A consulta URLhaus requer uma conta e uma Auth-Key próprias.")
    parsed = parse_target(target)
    host_mode = urlsplit(target).path in {"", "/"}
    endpoint = "host" if host_mode else "url"
    data = {"host": parsed.host} if host_mode else {"url": parsed.url}
    reserve_acceptance("urlhaus")
    payload = json_request("POST", f"https://urlhaus-api.abuse.ch/v1/{endpoint}/", data=data, headers={"Auth-Key": key, "User-Agent": "WebSecAI/0.1"})
    status = payload.get("query_status")
    if status in {"no_results", "no_result"}:
        return Result("no_results", "Sem correspondências no URLhaus para esta consulta e cobertura.")
    if status != "ok":
        raise SourceError()
    entries = payload.get("urls", []) if host_mode else [payload]
    evidence = []
    for entry in entries[:5]:
        if not isinstance(entry, dict):
            continue
        evidence.append(item("malware", "URL associado a distribuição de malware", "Registo URLhaus. Estado na fonte: " + str(entry.get("url_status", "desconhecido")) + ". Não demonstra como o website foi comprometido.", entry.get("urlhaus_reference", ""), "reported", entry.get("date_added"), indicator=source_link(entry.get("url", target)), scope="hostname" if host_mode else "exact_url"))
    return Result("success" if evidence else "no_results", "Consulta URLhaus concluída; resultados limitados a cinco registos.", evidence)

def phishtank(target: str) -> Result:
    key = value("PHISHTANK_API_KEY")
    if not key:
        from app.services.passive_sources import anonymous_phishtank
        return anonymous_phishtank(target)
    data = json_request("POST", "https://checkurl.phishtank.com/checkurl/", data={"url": target, "format": "json", "app_key": key}, headers={"User-Agent": "phishtank/websecai"})
    result = data.get("results", {})
    if not result.get("in_database"):
        return Result("no_results", "URL exato sem correspondência no PhishTank. Não significa que seja legítimo.")
    return Result("success", "Registo encontrado no PhishTank.", [item("phishing", "URL presente no PhishTank", "Verificado pela comunidade: " + str(bool(result.get("verified"))) + ". Válido na fonte: " + str(bool(result.get("valid"))) + ".", result.get("phish_detail_page", ""), "reported", scope="exact_url")])

def osint(target: str, organization: str) -> Result:
    key = value("TAVILY_API_KEY")
    if not key:
        return Result("not_configured", "Pesquisa pública sem chave de acesso nesta instalação. É necessária uma conta Tavily.")
    domain = parse_target(target).host
    name = re.sub(r"[^\w .-]", " ", organization)[:100].strip()
    queries = [f'"{domain}" (breach OR ransomware OR phishing OR ataque OR fuga)']
    queries.append(f'"{name or domain}" (incident OR hack OR leak OR incidente)')
    evidence, seen = [], set()
    failure = None
    for query in queries:
        try:
            reserve("tavily", number("SEARCH_MONTHLY_LIMIT", 200))
            reserve_acceptance("tavily")
            data = json_request("POST", "https://api.tavily.com/search", headers={"Authorization": "Bearer " + key}, json={"query": query, "search_depth": "basic", "max_results": 5, "include_answer": False, "include_raw_content": False})
            for result in data.get("results", [])[:5]:
                url = source_link(result.get("url", ""))
                title = str(result.get("title", ""))[:300]
                if not url:
                    continue
                identity = (parse_target(url).url, re.sub(r"\W+", " ", title.lower()).strip())
                if identity in seen:
                    continue
                seen.add(identity)
                content = str(result.get("content", ""))[:900]
                text = (title + " " + content + " " + url).lower()
                # A shared name or a substring in a different hostname does not identify the target.
                domain_match = bool(re.search(r"(?<![\w-])" + re.escape(domain) + r"(?![\w-]|\.[\w-])", text))
                name_match = bool(name) and name.lower() in (title + " " + content).lower()
                relevant = domain_match
                incident = bool(re.search(r"(?i)breach|ransomware|hack|attack|ataque|fuga|incident|leak|phishing", title + " " + content))
                allegation = bool(re.search(r"(?i)alleged|unverified|claim|alega|fórum|forum|dados à venda", title + " " + content + " " + url))
                confirmation = "allegation" if allegation else ("reported" if incident and relevant else "unverified")
                evidence.append(item("incident_report" if incident and relevant else "public_reference", title or "Referência pública", content, url, confirmation, result.get("published_date"), relevance="candidate_match" if relevant else "needs_review", queried_domain=domain, matched_by="domain" if domain_match else ("organization_name" if name_match else "none"), identity_status="candidate" if domain_match else "unverified", event_date_known=False, note="Excerto de pesquisa: requer leitura e validação da fonte. Um nome semelhante não identifica a organização e a menção do domínio não confirma uma intrusão."))
        except SourceError as exc:
            return Result("partial" if evidence else exc.status, exc.message + " As referências já obtidas foram preservadas.", evidence)
        except (httpx.HTTPError, ValueError, TypeError):
            failure = True
            break
    if failure:
        return Result("partial" if evidence else "error", "Pesquisa incompleta; confirme quota, acesso e disponibilidade. As referências obtidas foram preservadas.", evidence)
    return Result("success" if evidence else "no_results", "Pesquisa pública limitada a duas consultas; confirmação e datas do incidente exigem validação.", evidence)

_kev_lock = threading.Lock()

def kev_catalog():
    cache = ROOT / ".cache" / "kev.json"
    with _kev_lock:
        age = (datetime.now(timezone.utc).timestamp() - cache.stat().st_mtime) if cache.exists() else None
        if age is not None and age < 86400:
            return json.loads(cache.read_text(encoding="utf-8")), True, datetime.fromtimestamp(cache.stat().st_mtime, timezone.utc).isoformat()
        try:
            data = json_request("GET", "https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json")
            if not isinstance(data.get("vulnerabilities"), list):
                raise SourceError()
            cache.parent.mkdir(parents=True, exist_ok=True)
            temp = cache.with_suffix(".tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            temp.replace(cache)
            return data, False, datetime.now(timezone.utc).isoformat()
        except (SourceError, httpx.HTTPError, OSError, ValueError):
            if cache.exists():
                return json.loads(cache.read_text(encoding="utf-8")), True, datetime.fromtimestamp(cache.stat().st_mtime, timezone.utc).isoformat()
            raise

def kev(product: str = "") -> Result:
    data, cached, fetched_at = kev_catalog()
    entries = data["vulnerabilities"]
    term = product.strip().lower()
    if term:
        entries = [entry for entry in entries if term in (str(entry.get("vendorProject", "")) + " " + str(entry.get("product", ""))).lower()]
    entries = sorted(entries, key=lambda x: x.get("dateAdded", ""), reverse=True)[:5]
    evidence = [item("kev_candidate" if term else "kev_general", entry.get("cveID", "") + " — " + entry.get("vulnerabilityName", ""), str(entry.get("shortDescription", "")) + " Ação indicada: " + str(entry.get("requiredAction", "")), "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "known_exploited", cve=entry.get("cveID"), product=entry.get("product"), catalog_added_at=entry.get("dateAdded"), fetched_at=fetched_at, cached=cached, relevance="product_candidate_version_unconfirmed" if term else "general_alert_not_associated_with_target") for entry in entries]
    return Result("success" if evidence else "no_results", ("KEV: candidatos por produto, sem confirmar versão afetada ou ataque ao alvo." if term else "Catálogo KEV: alertas gerais, sem prova de ataque ao alvo.") + " A data de entrada não é a data do último ataque." + (" Cópia em cache: " + fetched_at if cached else ""), evidence)

def exposure(domain: str) -> Result:
    allowed = {name.strip().lower() for name in value("HIBP_VERIFIED_DOMAINS").split(",") if name.strip()}
    if not value("HIBP_API_KEY") or domain not in allowed:
        return Result("not_configured", "Fonte opcional condicionada: consultar contas expostas exige subscrição HIBP e comprovar o controlo do domínio. Notícias públicas continuam disponíveis pela pesquisa.")
    data = json_request("GET", "https://haveibeenpwned.com/api/v3/breachedDomain/" + quote(domain, safe=""), headers={"hibp-api-key": value("HIBP_API_KEY"), "User-Agent": "WebSecAI/0.1"})
    breaches = {}
    for names in data.values():
        for name in names:
            breaches[name] = breaches.get(name, 0) + 1
    evidence = [item("exposure", "Contas presentes na fuga: " + str(name), f"{count} conta(s) do domínio associadas a esta fuga. Não prova comprometimento do servidor do domínio. Emails e passwords não foram guardados.", "https://haveibeenpwned.com/", "reported", breach=str(name), accounts_count=count) for name, count in list(breaches.items())[:10]]
    return Result("success" if evidence else "no_results", "Consulta de domínio verificado concluída; apenas contagens e metadados.", evidence)

def configuration():
    rows = [
        {"id": "urlhaus", "name": "URLhaus", "configured": bool(value("URLHAUS_AUTH_KEY")), "purpose": "URLs associadas a malware"},
        {"id": "phishtank", "name": "PhishTank", "configured": bool(value("PHISHTANK_API_KEY")) or (value("PHISHTANK_ANONYMOUS_ENABLED", "false").lower() == "true" and number("PHISHTANK_DAILY_LIMIT", 0) > 0), "purpose": "Consulta de phishing por URL exato"},
        {"id": "osint", "name": "Pesquisa pública", "configured": bool(value("TAVILY_API_KEY")), "purpose": "Notícias, fóruns e relatórios via Tavily"},
        {"id": "kev", "name": "CISA KEV", "configured": True, "purpose": "Alertas gerais de exploração conhecida; sem chave"},
        {"id": "ai", "name": "Assistente IA", "configured": bool(value("GROQ_API_KEY")), "purpose": "Síntese por Groq com referências"},
        {"id": "exposure", "name": "Exposição de dados", "configured": bool(value("HIBP_API_KEY") and value("HIBP_VERIFIED_DOMAINS")), "purpose": "HIBP para domínios verificados; acesso condicionado"},
        {"id": "intelx", "name": "Intelligence X", "configured": False, "purpose": "Extensão condicionada a licença; sem integração ativa"},
    ]
    requirements = {
        "urlhaus": ("account_key", "Requer conta e Auth-Key no URLhaus. Existe acesso gratuito sujeito às condições do fornecedor.", "https://urlhaus-api.abuse.ch/"),
        "phishtank": ("account_key", "Opcional: chave existente ou modo anónimo explicitamente ativado, limitado e sujeito a cache. Sem ativação não há consultas.", "https://phishtank.org/api_info.php"),
        "osint": ("account_key", "Conta Tavily e chave privada. Pesquisas limitadas pela quota local e pelo plano escolhido.", "https://docs.tavily.com/documentation/api-credits"),
        "kev": ("none", "Catálogo público, sem conta. Os alertas gerais não comprovam um ataque ao domínio.", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"),
        "ai": ("account_key", "Conta Groq e chave privada. A existência da configuração não comprova a qualidade das respostas.", "https://console.groq.com/docs/quickstart"),
        "exposure": ("subscription_verified_domain", "Opcional: subscrição HIBP e domínio verificado. Abrange contas desse domínio; não pesquisa passwords em texto.", "https://haveibeenpwned.com/API/v3"),
        "intelx": ("not_implemented", "Extensão futura sem integração ativa. Adicionar uma chave não ativa este módulo; a utilização num produto depende de licença adequada.", "https://intelx.io/product"),
    }
    for row in rows:
        requirement, note, documentation = requirements[row["id"]]
        group = {"urlhaus": "essential", "osint": "essential", "ai": "analysis", "kev": "context", "intelx": "future"}.get(row["id"], "optional")
        limit = number("SEARCH_MONTHLY_LIMIT", 200) if row["id"] == "osint" else number("AI_DAILY_LIMIT", 10) if row["id"] == "ai" else 1
        row.update(implemented=row["id"] != "intelx", group=group, ready=row["configured"] and limit > 0, access_requirement=requirement, setup_note=note, documentation_url=documentation)
        if row["id"] in {"ai", "osint"}:
            row.update(local_limit=limit, limit_period="day_utc" if row["id"] == "ai" else "month_utc", shared_limit=True)
    for name, label, configured, note, docs in [
        ("hibp_catalog", "HIBP — metadados públicos", number("HIBP_CATALOG_DAILY_LIMIT", 0) > 0, "Catálogo público de fugas por website, sem emails nem passwords. Distinto da API paga de contas de domínios verificados. Limite local obrigatório.", "https://haveibeenpwned.com/API/v3"),
        ("urlscan", "urlscan — pesquisa passiva", bool(value("URLSCAN_API_KEY")) and number("URLSCAN_DAILY_LIMIT", 0) > 0, "Apenas scans públicos existentes; nunca submete um novo scan. Chave e quotas Free a confirmar antes de ativar.", "https://docs.urlscan.io/pages/search-api-reference"),
    ]:
        rows.append(dict(id=name, name=label, configured=configured, ready=configured, purpose=note, group="optional", implemented=True, access_requirement="key_and_free_quota" if name == "urlscan" else "public_catalogue_opt_in", setup_note=note, documentation_url=docs))
    return rows
