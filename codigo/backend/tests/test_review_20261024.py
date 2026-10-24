"""Offline regressions: source intent, quotas, provenance and owner-only audit trail."""
from copy import deepcopy
import json
import pytest
from app.services import providers as p, passive_sources as passive, ai_service
from app.services.investigation_pdf_visuals import balanced_pages
from app.services.source_policy import selected_optional
from app.db.session import SessionLocal
from app.models.investigation import Evidence
real_json_request = p.json_request


def test_optional_intent_preserves_legacy_and_rejects_unlisted_sources():
    assert selected_optional({}) == {'phishtank', 'exposure'}
    assert selected_optional({'optional_sources': []}) == set()
    assert selected_optional({'optional_sources': ['urlscan', 'unknown']}) == {'urlscan'}


def test_unselected_optional_does_not_make_core_result_partial(client, accounts, monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(p, 'urlhaus', lambda *_: p.Result('no_results', 'Fixture'))
    monkeypatch.setattr(p, 'osint', lambda *_: p.Result('no_results', 'Fixture'))
    monkeypatch.setattr(p, 'phishtank', lambda *_: pytest.fail('Unselected provider called'))
    monkeypatch.setattr(p, 'exposure', lambda *_: pytest.fail('Unselected provider called'))
    response = client.post('/api/v1/investigations', headers=accounts[0], json={'target': 'example.com'})
    data = client.get('/api/v1/investigations/' + response.json()['id'], headers=accounts[0]).json()
    assert data['status'] == 'completed'
    states = {run['provider']: run['status'] for run in data['runs']}
    assert all(states[name] == 'not_requested' for name in ['phishtank', 'exposure', 'hibp_catalog', 'urlscan'])
    assert not set(data['retryable_providers']) & {'phishtank', 'exposure', 'hibp_catalog', 'urlscan'}
    assert data['coverage_summary']['counts']['global_context'] == 1
    assert data['coverage_summary']['target_evidence_count'] == 0


def test_requested_optional_failure_remains_partial(client, accounts, monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(p, 'urlhaus', lambda *_: p.Result('no_results', 'Fixture'))
    monkeypatch.setattr(p, 'osint', lambda *_: p.Result('no_results', 'Fixture'))
    response = client.post('/api/v1/investigations', headers=accounts[0], json={'target': 'example.com', 'optional_sources': ['urlscan']})
    data = client.get('/api/v1/investigations/' + response.json()['id'], headers=accounts[0]).json()
    assert data['status'] == 'partial' and 'urlscan' in data['retryable_providers']
    assert 'phishtank' not in data['retryable_providers']


@pytest.mark.parametrize('count,expected', [(0,[0]), (12,[12]), (13,[7,6]), (24,[12,12]), (25,[9,8,8])])
def test_balanced_pdf_map_pages_preserve_every_reference(count, expected):
    entries = list(range(count))
    pages = balanced_pages(entries)
    assert [len(page) for page in pages] == expected
    assert sum(pages, []) == entries


def test_reviews_are_owner_only_append_only_and_invalidate_analysis(client, accounts):
    response = client.post('/api/v1/investigations', headers=accounts[0], json={'demo': True, 'technical': True})
    path = '/api/v1/investigations/' + response.json()['id']
    initial = client.get(path, headers=accounts[0]).json()
    entry = initial['evidence'][0]
    route = path + '/evidence/' + entry['id'] + '/reviews'
    payload = {'status': 'contested', 'identity_status': 'does_not_match', 'note': 'Homónimo fictício; requer outra fonte.'}
    assert client.post(route, headers=accounts[1], json=payload).status_code == 404
    assert client.post(route, json=payload).status_code == 401
    response = client.post(route, headers=accounts[0], json=payload)
    assert response.status_code == 201, response.text
    snapshot = response.json()
    review = next(e for e in snapshot['evidence'] if e['id'] == entry['id'])['review']
    assert review['author'] == 'alice' and review['is_current']
    assert not snapshot['reports'][-1]['is_current']
    assert client.post(route, headers=accounts[0], json=payload).status_code == 409
    payload.update(previous_review_id=review['id'], status='reviewed', identity_status='uncertain')
    response = client.post(route, headers=accounts[0], json=payload)
    current = next(e for e in response.json()['evidence'] if e['id'] == entry['id'])
    assert len(current['reviews']) == 2 and current['reviews'][0]['status'] == 'contested'
    assert client.put(route, headers=accounts[0], json=payload).status_code == 405
    assert client.get(path + '/report', headers=accounts[1]).status_code == 404
    with SessionLocal() as db:
        evidence = db.get(Evidence, entry['id'])
        evidence.description += ' Conteúdo da fonte alterado.'
        db.commit()
    changed = client.get(path, headers=accounts[0]).json()
    assert not next(e for e in changed['evidence'] if e['id'] == entry['id'])['review']['is_current']


def test_phishtank_anonymous_requires_explicit_enable_and_caches(monkeypatch, tmp_path):
    monkeypatch.setattr(passive, 'ROOT', tmp_path)
    assert passive.anonymous_phishtank('https://example.com/').status == 'not_configured'
    monkeypatch.setenv('PHISHTANK_ANONYMOUS_ENABLED', 'true')
    monkeypatch.setenv('PHISHTANK_DAILY_LIMIT', '2')
    calls = []
    monkeypatch.setattr(p, 'reserve', lambda *a, **k: None)
    def respond(method, url, **kwargs):
        assert method == 'POST' and url == 'https://checkurl.phishtank.com/checkurl/'
        assert 'app_key' not in kwargs['data']
        calls.append(True)
        return {'results': {'in_database': False}}
    monkeypatch.setattr(p, 'json_request', respond)
    assert passive.anonymous_phishtank('https://example.com/').status == 'no_results'
    assert passive.anonymous_phishtank('https://example.com/').status == 'no_results'
    assert len(calls) == 1


def test_hibp_public_metadata_not_paid_domain_accounts(monkeypatch, tmp_path):
    monkeypatch.setattr(passive, 'ROOT', tmp_path)
    monkeypatch.setenv('HIBP_CATALOG_DAILY_LIMIT', '2')
    monkeypatch.setattr(p, 'reserve', lambda *a, **k: None)
    def respond(method, url, **kwargs):
        assert method == 'GET' and url.endswith('/api/v3/breaches')
        assert kwargs['params'] == {'Domain': 'example.com'}
        assert 'hibp-api-key' not in kwargs['headers']
        return [{'Domain': 'example.com', 'Name': 'Fixture', 'Title': 'Exemplo', 'BreachDate': '2025-01-02', 'AddedDate': '2026-01-01T00:00:00Z', 'Emails': ['must-not-persist@example.com'], 'Description': '<script>untrusted</script>'}]
    monkeypatch.setattr(p, 'json_request', respond)
    result = passive.hibp_catalog('https://example.com/')
    assert result.evidence[0]['event_at'] == '2025-01-02'
    assert result.evidence[0]['published_at'] is None
    assert 'must-not-persist' not in json.dumps(result.evidence) and '<script>' not in json.dumps(result.evidence)


def test_urlscan_only_reads_public_matching_scans(monkeypatch, tmp_path):
    monkeypatch.setattr(passive, 'ROOT', tmp_path)
    monkeypatch.setenv('URLSCAN_API_KEY', 'synthetic-test-key')
    monkeypatch.setenv('URLSCAN_DAILY_LIMIT', '2')
    monkeypatch.setattr(p, 'reserve', lambda *a, **k: None)
    def respond(method, url, **kwargs):
        assert method == 'GET' and url == 'https://urlscan.io/api/v1/search'
        assert 'task.visibility:public' in kwargs['params']['q']
        row = {'_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'page': {'domain': 'sub.example.com'}, 'task': {'visibility': 'public', 'time': '2026-01-01T00:00:00Z'}}
        private = deepcopy(row); private['task']['visibility'] = 'private'
        return {'results': [row, private, dict(row, page={'domain': 'other.example'})]}
    monkeypatch.setattr(p, 'json_request', respond)
    result = passive.urlscan('https://example.com/')
    assert len(result.evidence) == 1 and result.evidence[0]['published_at'] is None
    assert result.evidence[0]['meta']['scan_at'].startswith('2026-01-01')


def test_provider_cooldown_is_cached_without_retries(monkeypatch, tmp_path):
    monkeypatch.setattr(passive, 'ROOT', tmp_path)
    count = []
    def fail():
        count.append(True)
        raise p.SourceError('rate_limited', 'Safe', {'retry_after_seconds': 120})
    assert passive.cached('fixture', 'example.com', fail).status == 'rate_limited'
    assert passive.cached('fixture', 'example.com', fail).status == 'rate_limited'
    assert len(count) == 1


def test_shared_minute_budget_blocks_second_call():
    p.reserve('groq_minute', 1, minute=True)
    with pytest.raises(p.SourceError) as error:
        p.reserve('groq_minute', 1, minute=True)
    assert error.value.status == 'rate_limited'


@pytest.mark.parametrize('provider', ['tavily', 'groq', 'urlhaus'])
def test_initial_acceptance_is_capped_at_two_across_restarts(monkeypatch, provider):
    monkeypatch.setenv('TI_ACCEPTANCE_ENABLED', 'true')
    monkeypatch.setenv('TI_ACCEPTANCE_ID', '20261024')
    p.reserve_acceptance(provider)
    p.reserve_acceptance(provider)
    with pytest.raises(p.SourceError) as error:
        p.reserve_acceptance(provider)
    assert error.value.status == 'rate_limited'


@pytest.mark.parametrize('count', [0, 12, 13, 25])
def test_pdf_export_edge_cases_offline(count):
    from evaluations.report_fixture import snapshot
    from app.services.investigation_pdf import investigation_pdf
    data = snapshot()
    base = data['evidence'][0]
    data['evidence'] = [dict(base, id='bounded-fixture-' + str(i)) for i in range(count)]
    data['reports'] = []
    assert investigation_pdf(data).startswith(b'%PDF')


@pytest.mark.parametrize('endpoint', ['https://urlhaus-api.abuse.ch/v1/host/', 'https://urlscan.io/api/v1/search'])
def test_http_404_is_not_proof_of_authentication_or_no_matches(monkeypatch, endpoint):
    import httpx
    original_client = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={'error': 'fixture'}))
    monkeypatch.setattr(p.httpx, 'Client', lambda **kwargs: original_client(transport=transport, **kwargs))
    with pytest.raises(p.SourceError) as error:
        real_json_request('GET', endpoint)
    assert error.value.status == 'error'
