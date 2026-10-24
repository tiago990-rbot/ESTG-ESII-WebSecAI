"""Opt-in passive sources. No target visits, scan submissions, email or password data."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import re
import threading
import time
import uuid
from app.core.config import ROOT, number, value
from app.core.targets import parse_target
from app.services import providers as p
from app.db.session import SessionLocal
from app.models.investigation import Usage
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

_lock = threading.Lock()

def cached(name, query, call, ttl=3600):
    # Only minimised provider results are cached; neither keys nor raw responses.
    path = ROOT / '.cache' / 'passive-sources' / (hashlib.sha256((name + ':' + query).encode()).hexdigest() + '.json')
    with _lock:
        try:
            saved = json.loads(path.read_text(encoding='utf-8'))
            if saved['expires'] > time.time():
                result = p.Result(**saved['result'])
                if result.status != 'rate_limited':
                    result.message = 'Resultado em cache; não foi feita nova consulta ao fornecedor. ' + result.message
                return result
        except (OSError, ValueError, TypeError, KeyError):
            pass
        with SessionLocal() as db:
            cooldown = db.get(Usage, (name + '_cooldown', 'until'))
            if cooldown and cooldown.count > time.time():
                return p.Result('rate_limited', 'Fornecedor em pausa após limite de frequência. Não foi feita nova consulta.')
        try:
            result = call()
            stamp = datetime.now(timezone.utc).isoformat()
            for entry in result.evidence:
                entry.setdefault('meta', {})['provider_queried_at'] = stamp
        except p.SourceError as exc:
            if exc.status != 'rate_limited':
                raise
            wait = exc.diagnostics.get('retry_after_seconds', 60)
            result = p.Result('rate_limited', 'Limite do fornecedor atingido; consulta bloqueada temporariamente. Não foram feitas novas tentativas.')
            ttl = max(60, min(int(wait), 86400))
            until = int(time.time()) + ttl
            with SessionLocal() as db:
                key = (name + '_cooldown', 'until')
                if db.get(Usage, key) is None:
                    db.add(Usage(provider=key[0], period=key[1], count=until))
                    try:
                        db.commit()
                    except IntegrityError:
                        db.rollback()
                db.execute(update(Usage).where(Usage.provider == key[0], Usage.period == key[1], Usage.count < until).values(count=until))
                db.commit()
        if result.status in {'success', 'no_results', 'rate_limited'}:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps({'expires': time.time() + ttl, 'result': asdict(result)}, ensure_ascii=False), encoding='utf-8')
            temp.replace(path)
        return result


def anonymous_phishtank(target):
    if value('PHISHTANK_ANONYMOUS_ENABLED', 'false').lower() != 'true':
        return p.Result('not_configured', 'Modo PhishTank sem chave não ativado. Exige opção explícita e limites locais.')
    limit = number('PHISHTANK_DAILY_LIMIT', 0)
    if limit == 0:
        return p.Result('not_configured', 'Defina um limite gratuito PhishTank antes de ativar consultas anónimas.')
    clean = parse_target(target).url
    def request():
        p.reserve('phishtank', limit, daily=True)
        p.reserve('phishtank_minute', 1, minute=True)
        result = p.json_request('POST', 'https://checkurl.phishtank.com/checkurl/', data={'url': clean, 'format': 'json'}, headers={'User-Agent': 'phishtank/websecai-academic'})
        row = result.get('results')
        if not isinstance(row, dict) or not isinstance(row.get('in_database'), bool):
            raise p.SourceError()
        if not row['in_database']:
            return p.Result('no_results', 'URL exato sem correspondência PhishTank; não comprova legitimidade.')
        evidence = p.item('phishing', 'URL presente no PhishTank', 'Registo comunitário; não comprova compromisso atual do website.', row.get('phish_detail_page', ''), 'reported', scope='exact_url', verified=bool(row.get('verified')), valid=bool(row.get('valid')))
        return p.Result('success', 'Consulta anónima PhishTank concluída; dados sujeitos a cache de uma hora.', [evidence])
    return cached('phishtank-anonymous', clean, request)


def hibp_catalog(target):
    limit = number('HIBP_CATALOG_DAILY_LIMIT', 0)
    if limit == 0:
        return p.Result('not_configured', 'Catálogo público HIBP desativado; requer limite local explicitamente configurado. Não necessita de chave nem pesquisa contas.')
    domain = parse_target(target).host
    def request():
        p.reserve('hibp_catalog', limit, daily=True)
        p.reserve('hibp_catalog_minute', 1, minute=True)
        rows = p.json_request('GET', 'https://haveibeenpwned.com/api/v3/breaches', params={'Domain': domain}, headers={'User-Agent': 'WebSecAI-academic/0.1'})
        if not isinstance(rows, list):
            raise p.SourceError()
        evidence = []
        for row in rows[:20]:
            if not isinstance(row, dict) or str(row.get('Domain', '')).lower().rstrip('.') != domain:
                continue
            # Publication/added-to-catalogue dates are NOT inferred as incident dates.
            entry = p.item('public_breach_metadata', 'Fuga catalogada: ' + str(row.get('Title', row.get('Name', 'Registo'))), 'Metadados públicos HIBP do website indicado na fonte. Não identifica contas deste domínio nem demonstra intrusão atual.', 'https://haveibeenpwned.com/', 'reported', scope='public_website_metadata', identity_status='candidate', relevance='candidate_match', catalogue_added_at=p.publication_date(row.get('AddedDate')), verified=bool(row.get('IsVerified')), fabricated=bool(row.get('IsFabricated')), breach_name=str(row.get('Name', ''))[:150], breach_domain=domain, data_classes=[str(item)[:100] for item in row.get('DataClasses', [])[:30]] if isinstance(row.get('DataClasses'), list) else [], catalogue_modified_at=p.publication_date(row.get('ModifiedDate')))
            entry['event_at'] = p.publication_date(row.get('BreachDate'))
            evidence.append(entry)
        return p.Result('success' if evidence else 'no_results', 'Consulta de metadados públicos HIBP concluída. Não foi usado /breachedDomain nem pesquisado qualquer email.', evidence)
    return cached('hibp-catalog', domain, request, ttl=86400)


def urlscan(target):
    key, limit = value('URLSCAN_API_KEY'), number('URLSCAN_DAILY_LIMIT', 0)
    if not key or limit == 0:
        return p.Result('not_configured', 'Pesquisa passiva urlscan desativada; requer chave própria e limite gratuito confirmado. Não submete scans.')
    domain = parse_target(target).host
    if not re.fullmatch(r'[a-z0-9.-]+', domain):
        raise p.SourceError('error', 'Pesquisa urlscan aceita apenas um nome DNS normalizado.')
    escaped = domain.replace('-', '\\-')
    def request():
        p.reserve('urlscan', limit, daily=True)
        p.reserve('urlscan_minute', 1, minute=True)
        data = p.json_request('GET', 'https://urlscan.io/api/v1/search', params={'q': 'page.domain:' + escaped + ' AND task.visibility:public', 'size': 10}, headers={'API-Key': key, 'User-Agent': 'WebSecAI-academic/0.1'})
        rows = data.get('results')
        if not isinstance(rows, list):
            raise p.SourceError()
        evidence = []
        for row in rows[:10]:
            task, page = row.get('task', {}), row.get('page', {})
            host = str(page.get('domain', '')).lower().rstrip('.')
            if task.get('visibility') != 'public' or not (host == domain or host.endswith('.' + domain)):
                continue
            try:
                scan_id = str(uuid.UUID(str(row.get('_id', task.get('uuid', '')))))
            except ValueError:
                continue
            evidence.append(p.item('passive_scan', 'Scan público anterior: ' + host, 'Observação histórica de um scan de terceiros. Não foi submetido um novo scan nem visitado o alvo; não demonstra o estado atual.', 'https://urlscan.io/result/' + scan_id + '/', 'reported', scope='existing_public_scans', scan_at=p.publication_date(task.get('time')), relevance='candidate_match'))
        return p.Result('success' if evidence else 'no_results', 'Pesquisa passiva de até dez scans públicos. Ausência de scans não comprova segurança.', evidence)
    return cached('urlscan-public-search', domain, request)
