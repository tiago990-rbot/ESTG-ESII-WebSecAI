"""Conservative shared reservations; observations are not billing or account totals."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import re
from sqlalchemy import select, func, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.core.config import value, number
from app.core.request_window import restricted_limit
from app.db.session import SessionLocal
from app.models.investigation import Usage
from app.models.quota import QuotaGrant, ProviderObservation


def now():
    return datetime.now(timezone.utc)


def window(kind="month", stamp=None):
    stamp = stamp or now()
    if kind == "minute":
        return stamp.strftime("%Y-%m-%dT%H:%M"), stamp.replace(second=0, microsecond=0) + timedelta(minutes=1)
    if kind == "day":
        return stamp.strftime("%Y-%m-%d"), stamp.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = stamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(year=end.year+1, month=1) if end.month == 12 else end.replace(month=end.month+1)
    return stamp.strftime("%Y-%m"), end


def specs():
    return {"tavily": (number("SEARCH_MONTHLY_LIMIT", 200), "month", 1000),
            "urlhaus": (number("URLHAUS_DAILY_LIMIT",20),"day",100),
            "kev": (number("KEV_DAILY_LIMIT",5),"day",20),
            "exposure": (number("HIBP_VERIFIED_DAILY_LIMIT",0),"day",20),
            "groq": (number("AI_DAILY_LIMIT", 10), "day", 100),
            "groq_minute": (1, "minute", 1),
            "phishtank": (number("PHISHTANK_DAILY_LIMIT", 0), "day", 100),
            "phishtank_minute": (1, "minute", 1),
            "hibp_catalog": (number("HIBP_CATALOG_DAILY_LIMIT", 0), "day", 100),
            "hibp_catalog_minute": (1, "minute", 1),
            "urlscan": (number("URLSCAN_DAILY_LIMIT", 0), "day", 100),
            "urlscan_minute": (1, "minute", 1)}


def admin(user):
    # Explicit immutable database IDs, empty by default. Usernames/emails are not roles.
    ids = {int(x) for x in value("QUOTA_ADMIN_USER_IDS").split(",") if x.strip().isdigit()}
    return user.id in ids


def ensure_usage(db, provider, period):
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(Usage).values(provider=provider, period=period, count=0).on_conflict_do_nothing())


def allowance(provider, period):
    return select(func.coalesce(func.sum(QuotaGrant.amount), 0)).where(QuotaGrant.provider == provider, QuotaGrant.period == period).scalar_subquery()


def reserve(provider, limit, daily=False, minute=False):
    from app.services.providers import SourceError
    kind = "minute" if minute else "day" if daily else "month"
    period, reset = window(kind)
    base, hard = limit, specs().get(provider, (limit, kind, limit))[2]
    if provider in specs():
        limit = min(limit, hard)
    extra = allowance(provider, period) if provider in {"groq", "tavily"} and base > 0 else 0
    effective = limit + extra
    # Hard ceiling and a private request-window restriction are independent of grants.
    try:
        guard = restricted_limit(value("WEBSECAI_REQUEST_WINDOW_FILE"), provider, period, hard)
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        raise SourceError("rate_limited", "Janela autorizada terminada ou orçamento inválido. Não foi efetuada nova chamada.") from None
    guard = min(guard, hard)
    check_external(provider.replace("_minute", ""))
    with SessionLocal.begin() as db:
        ensure_usage(db, provider, period)
        changed = db.execute(update(Usage).where(Usage.provider == provider, Usage.period == period, Usage.count < effective, Usage.count < guard).values(count=Usage.count + 1)).rowcount
        if not changed:
            raise SourceError("rate_limited", "Limite local de pedidos atingido; não foi efetuada nova chamada.", {"retry_after_seconds": max(1, int((reset-now()).total_seconds()))})


def grant(provider, expected_period, reason, request_id, user):
    from fastapi import HTTPException
    if not admin(user):
        raise HTTPException(403, "Apenas o administrador de limites pode autorizar exceções.")
    if provider not in {"groq", "tavily"}:
        raise HTTPException(422, "Esta proteção não admite exceções.")
    base, kind, hard = specs()[provider]
    period, _ = window(kind)
    if expected_period != period or base <= 0:
        raise HTTPException(409, "Período alterado ou integração desativada. Atualize o painel.")
    with SessionLocal.begin() as db:
        existing = db.get(QuotaGrant, request_id)
        if existing:
            if (existing.actor_id, existing.provider, existing.period, existing.reason) != (user.id, provider, period, reason):
                raise HTTPException(409, "Identificador da autorização já utilizado.")
            return {"id": existing.id, "period": period, "amount": 1, "replayed": True}
        ensure_usage(db, provider, period)
        # A no-op write serializes grants with reservations on SQLite and PostgreSQL.
        db.execute(update(Usage).where(Usage.provider == provider, Usage.period == period).values(count=Usage.count))
        existing = db.get(QuotaGrant, request_id)
        if existing:
            if (existing.actor_id,existing.provider,existing.period,existing.reason)!=(user.id,provider,period,reason):
                raise HTTPException(409,"Identificador da autorização já utilizado.")
            return {"id":existing.id,"period":period,"amount":1,"replayed":True}
        total = db.scalar(select(allowance(provider, period)))
        if total >= 3 or base + total >= hard:
            raise HTTPException(409, "Teto de três exceções por período ou teto de segurança atingido.")
        db.add(QuotaGrant(id=request_id, provider=provider, period=period, actor_id=user.id, reason=reason, amount=1))
    return {"id": request_id, "period": period, "amount": 1, "replayed": False}


def _seconds(raw):
    if not raw or len(raw) > 60:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return min(float(raw), 31_536_000)
    parts = re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h|d)", raw)
    if parts and "".join(a+b for a,b in parts) == raw:
        return min(sum(float(a)*{"ms": .001,"s":1,"m":60,"h":3600,"d":86400}[b] for a,b in parts),31_536_000)
    return None


def observe(provider, scope, headers, status):
    """Only numeric documented rate headers; never persist response bodies/auth headers."""
    stamp, dims = now(), []
    if provider == "groq":
        for unit, period in (("requests", "day"), ("tokens", "minute")):
            def integer(name):
                text = headers.get("x-ratelimit-" + name + "-" + unit, "")
                return int(text) if re.fullmatch(r"\d{1,12}", text) else None
            seconds = _seconds(headers.get("x-ratelimit-reset-" + unit))
            limit, remaining = integer("limit"), integer("remaining")
            if limit is not None or remaining is not None:
                dims.append({"unit": unit, "window": period, "limit": limit, "remaining": remaining,
                             "observed_at":stamp.isoformat(),
                             "reset_at": (stamp+timedelta(seconds=seconds)).isoformat() if seconds is not None else None,
                             "source": "response_headers"})
    blocked = None
    if status in {429,509}:
        raw = headers.get("retry-after", "")
        seconds = _seconds(raw)
        if seconds is None:
            try:
                parsed = parsedate_to_datetime(raw)
                seconds = max(1, (parsed-stamp).total_seconds())
            except (ValueError, TypeError, OverflowError):
                seconds = 60
        blocked = stamp+timedelta(seconds=min(max(1,seconds),31_536_000))
    with SessionLocal.begin() as db:
        insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
        stmt = insert(ProviderObservation).values(provider=provider, scope=scope, observed_at=stamp,
                    last_success_at=stamp if status == 200 else None, status=status, blocked_until=blocked, dimensions=dims)
        db.execute(stmt.on_conflict_do_update(index_elements=["provider","scope"], set_={
            "observed_at":stamp, "status":status,"blocked_until":blocked,"dimensions":dims if dims else ProviderObservation.dimensions,
            "last_success_at":stamp if status == 200 else ProviderObservation.last_success_at}))


def observation(provider, scope=None):
    scope = scope or (value("GROQ_MODEL", "qwen/qwen3.8-27b") if provider == "groq" else "account")
    with SessionLocal() as db:
        row = db.get(ProviderObservation,(provider,scope))
        if not row:
            return None
        return {"scope":scope,"observed_at":row.observed_at.isoformat(),"last_success_at":row.last_success_at.isoformat() if row.last_success_at else None,
                "http_status":row.status,"blocked_until":row.blocked_until.isoformat() if row.blocked_until else None,
                "dimensions":row.dimensions,"stale":(now()-row.observed_at).total_seconds()>300 or any(d.get('observed_at') and (now()-datetime.fromisoformat(d['observed_at'])).total_seconds()>300 for d in row.dimensions)}


def check_external(provider, tokens=0, scope=None, metadata=False):
    from app.services.providers import SourceError
    info = observation(provider, scope)
    if not info:
        return
    stamp = now()
    if info["http_status"] in {401,403} and (stamp-datetime.fromisoformat(info['observed_at'])).total_seconds()<300:
        raise SourceError("access_denied","O fornecedor recusou o acesso observado. Confirme a configuração privada antes de repetir.")
    if info["blocked_until"] and datetime.fromisoformat(info["blocked_until"]) > stamp:
        raise SourceError("rate_limited", "Aguarde pelo Retry-After comunicado pelo fornecedor.")
    if metadata:return
    for dim in info["dimensions"]:
        if dim["reset_at"] and datetime.fromisoformat(dim["reset_at"]) <= stamp:
            continue
        if dim["remaining"] is not None and dim["remaining"] < (tokens if dim["unit"] == "tokens" else 1):
            raise SourceError("rate_limited", "Saldo observado do fornecedor insuficiente. A exceção local não ultrapassa este bloqueio.")


def sync_tavily(user):
    from fastapi import HTTPException
    from app.services import providers
    if not admin(user):raise HTTPException(403,'Apenas o administrador pode consultar metadados da conta.')
    if value('PROVIDER_USAGE_SYNC_ENABLED','false').lower()!='true' or not value('TAVILY_API_KEY'):
        raise HTTPException(409,'Sincronização externa desativada ou acesso Tavily não configurado.')
    stamp=now();period=str(int(stamp.timestamp())//300)
    # Metadata reads have their own bounded budget and never consume search exceptions.
    with SessionLocal.begin() as db:
        ensure_usage(db,'tavily_usage_sync',period)
        changed=db.execute(update(Usage).where(Usage.provider=='tavily_usage_sync',Usage.period==period,Usage.count<1).values(count=Usage.count+1)).rowcount
        if not changed:raise HTTPException(429,'Já foi feita uma tentativa de sincronização nesta janela de cinco minutos.')
    reserve('tavily_usage_daily',10,daily=True)
    try:raw=providers.json_request('GET','https://api.tavily.com/usage',headers={'Authorization':'Bearer '+value('TAVILY_API_KEY')})
    except providers.SourceError as exc:raise HTTPException(429 if exc.status=='rate_limited' else 502,exc.message) from None
    except Exception:raise HTTPException(502,'Não foi possível obter os metadados de utilização. Sem repetição automática.') from None
    def numeric(x):return x if type(x) in {int,float} and 0<=x<=1_000_000_000_000 else None
    dims=[]
    try:
        for key,unit,used_name,limit_name in [('account','credits_account','plan_usage','plan_limit'),('key','credits_key','usage','limit')]:
            section=raw.get(key,{})
            limit,used=numeric(section.get(limit_name)),numeric(section.get(used_name))
            if limit is not None or used is not None:
                dims.append({'unit':unit,'window':'billing_cycle','limit':limit,'used':used,'remaining':max(0,limit-used) if limit is not None and used is not None else None,'reset_at':None,'source':'usage_endpoint','observed_at':now().isoformat()})
    except (AttributeError,TypeError):raise HTTPException(502,'Metadados de utilização inválidos; nenhum valor bruto foi guardado.') from None
    if not dims:raise HTTPException(502,'Fornecedor não devolveu os campos numéricos esperados.')
    with SessionLocal.begin() as db:
        # Real json_request creates the observation; contract tests can replace that boundary.
        insert=pg_insert if db.bind.dialect.name=='postgresql' else sqlite_insert
        stmt=insert(ProviderObservation).values(provider='tavily',scope='account',observed_at=now(),last_success_at=now(),status=200,blocked_until=None,dimensions=dims)
        db.execute(stmt.on_conflict_do_update(index_elements=['provider','scope'],set_={'observed_at':now(),'last_success_at':now(),'status':200,'blocked_until':None,'dimensions':dims}))
    return {'status':'updated','observation':observation('tavily')}


def dashboard(user):
    from app.services.providers import configuration
    mapping = {"osint":"tavily","ai":"groq"}
    stamp, rows = now(), []
    with SessionLocal() as db:
        for config in configuration():
            provider = mapping.get(config["id"],config["id"])
            limits = []
            for key in (provider, provider+"_minute"):
                if key not in specs():
                    continue
                base,kind,hard = specs()[key]
                period,reset = window(kind,stamp)
                used = db.get(Usage,(key,period))
                extra = db.scalar(select(allowance(key,period)))
                grants = db.query(QuotaGrant).filter_by(provider=key,period=period).order_by(QuotaGrant.created_at.desc()).all()
                effective=min(base+extra,hard) if base>0 else 0
                limits.append({"provider":key,"period":period,"window":kind,"base_limit":base,"extra":extra,
                    "hard_limit":hard,"effective_limit":effective,"reserved":used.count if used else 0,
                    "remaining":max(0,effective-(used.count if used else 0)),"reset_at":reset.isoformat(),
                    "can_grant":admin(user) and key in {"groq","tavily"} and base>0 and extra<3 and base+extra<hard,
                    "grants":[{"id":g.id,"actor_id":g.actor_id,"reason":g.reason,"created_at":g.created_at.isoformat()} for g in grants]})
            gate = None
            if provider in {"groq","tavily","urlhaus"} and value("TI_ACCEPTANCE_ENABLED","false").lower()=="true":
                period = value("TI_ACCEPTANCE_ID","20261024")
                usage = db.get(Usage,("acceptance_"+provider,period))
                gate = {"id":period,"limit":2,"reserved":usage.count if usage else 0,"reset_at":None}
            external = observation(provider)
            reasons = []
            if not config["ready"]: reasons.append("Integração desativada, sem acesso ou futura.")
            if any(x["remaining"]<=0 for x in limits): reasons.append("Limite interno atingido.")
            if gate and gate["reserved"]>=2: reasons.append("Janela de aceitação esgotada; sem renovação automática.")
            try: check_external(provider)
            except Exception as exc:
                from app.services.providers import SourceError
                if not isinstance(exc,SourceError): raise
                reasons.append(exc.message)
            rows.append({**config,"provider":provider,"internal":limits,"external":external,"acceptance":gate,
                         "ready":config["ready"] and not reasons,"blocked_reasons":reasons})
    infrastructure=[{'id':key,'name':label,'usage':None,'limit':None,'reset_at':None,'source':'not_connected','console_url':url} for key,label,url in (
        ('render','Render · backend','https://dashboard.render.com/'),('neon','Neon · base de dados','https://console.neon.tech/'),('cloudflare','Cloudflare · interface','https://dash.cloudflare.com/'))]
    with SessionLocal() as db:
        day,day_reset=window('day',stamp)
        daily_usage=db.get(Usage,('tavily_usage_daily',day))
        sync_usage=db.get(Usage,('tavily_usage_sync',str(int(stamp.timestamp())//300)))
        metadata_usage={'reserved_today':daily_usage.count if daily_usage else 0,'daily_limit':10,'daily_reset_at':day_reset.isoformat(),'reserved_this_window':sync_usage.count if sync_usage else 0,'window_limit':1,'window_reset_at':datetime.fromtimestamp((int(stamp.timestamp())//300+1)*300,timezone.utc).isoformat()}
    return {"observed_at":stamp.isoformat(),"admin":admin(user),"metadata_usage":metadata_usage,"tavily_sync_enabled":admin(user) and value('PROVIDER_USAGE_SYNC_ENABLED','false').lower()=='true' and bool(value('TAVILY_API_KEY')),"providers":rows,"infrastructure":infrastructure,
            "note":"Reservas partilhadas pelo grupo, não uma fatura. O saldo externo é uma observação; outras aplicações podem consumir a mesma conta. Dados ausentes não são estimados."}
