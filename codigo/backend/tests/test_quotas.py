from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from uuid import uuid4
import json
import pytest
from fastapi import HTTPException
from app.services import quotas as q, providers as p
from app.db.session import SessionLocal
from app.models.investigation import Usage
from app.models.quota import QuotaGrant


def test_concurrent_reservations_stop_at_shared_cap():
    def attempt(_):
        try: p.reserve("groq",3,daily=True);return True
        except p.SourceError:return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt,range(18)))==3


def test_grant_role_idempotence_cap_and_period(monkeypatch,client,accounts):
    assert client.get('/api/v1/usage').status_code==401
    overview=client.get('/api/v1/usage',headers=accounts[0]).json()
    assert not overview['admin']
    period=q.window('day')[0]
    payload={'provider':'groq','period':period,'reason':'Validação extra controlada','request_id':str(uuid4())}
    assert client.post('/api/v1/usage/grants',headers=accounts[0],json=payload).status_code==403
    monkeypatch.setenv('QUOTA_ADMIN_USER_IDS','1')
    monkeypatch.setenv('AI_DAILY_LIMIT','1')
    p.reserve('groq',1,daily=True)
    with pytest.raises(p.SourceError):p.reserve('groq',1,daily=True)
    result=client.post('/api/v1/usage/grants',headers=accounts[0],json=payload)
    assert result.status_code==201,result.text
    assert client.post('/api/v1/usage/grants',headers=accounts[0],json=payload).json()['replayed']
    p.reserve('groq',1,daily=True)
    with pytest.raises(p.SourceError):p.reserve('groq',1,daily=True)
    assert client.post('/api/v1/usage/grants',headers=accounts[1],json=dict(payload,request_id=str(uuid4()))).status_code==403
    for _ in range(2):assert client.post('/api/v1/usage/grants',headers=accounts[0],json=dict(payload,request_id=str(uuid4()))).status_code==201
    assert client.post('/api/v1/usage/grants',headers=accounts[0],json=dict(payload,request_id=str(uuid4()))).status_code==409
    future=q.now()+timedelta(days=1)
    monkeypatch.setattr(q,'now',lambda:future)
    assert client.post('/api/v1/usage/grants',headers=accounts[0],json=payload).status_code==409
    p.reserve('groq',1,daily=True)
    with pytest.raises(p.SourceError):p.reserve('groq',1,daily=True)


def test_safe_headers_external_reset_model_scope_and_retry(monkeypatch):
    stamp=datetime(2026,10,30,12,tzinfo=timezone.utc)
    monkeypatch.setattr(q,'now',lambda:stamp)
    model='test-model'
    q.observe('groq',model,{'x-ratelimit-limit-requests':'100','x-ratelimit-remaining-requests':'0','x-ratelimit-reset-requests':'2m3.5s','authorization':'private-synthetic','set-cookie':'private-synthetic'},200)
    data=q.observation('groq',model)
    assert 'private-synthetic' not in json.dumps(data)
    assert data['dimensions'][0]['reset_at']=='2026-10-30T12:02:03.500000+00:00'
    with pytest.raises(p.SourceError):q.check_external('groq',scope=model)
    q.check_external('groq',scope='other-model')
    monkeypatch.setattr(q,'now',lambda:stamp+timedelta(minutes=3))
    q.check_external('groq',scope=model)
    q.observe('tavily','account',{'retry-after':'120'},429)
    with pytest.raises(p.SourceError):q.check_external('tavily')


def test_extra_does_not_bypass_zero_acceptance_or_hard_guard(monkeypatch,client,accounts,tmp_path):
    monkeypatch.setenv('QUOTA_ADMIN_USER_IDS','1')
    monkeypatch.setenv('AI_DAILY_LIMIT','0')
    with pytest.raises(HTTPException):q.grant('groq',q.window('day')[0],'Motivo suficiente',str(uuid4()),SimpleNamespace(id=1))
    monkeypatch.setenv('AI_DAILY_LIMIT','1')
    q.grant('groq',q.window('day')[0],'Motivo suficiente',str(uuid4()),SimpleNamespace(id=1))
    monkeypatch.setenv('TI_ACCEPTANCE_ENABLED','true')
    p.reserve_acceptance('groq');p.reserve_acceptance('groq')
    with pytest.raises(p.SourceError):p.reserve_acceptance('groq')
    p.reserve('groq_minute',1,minute=True)
    with pytest.raises(p.SourceError):p.reserve('groq_minute',1,minute=True)


def test_unknown_provider_quota_is_not_invented(client,accounts):
    result=client.get('/api/v1/usage',headers=accounts[0])
    assert result.status_code==200,result.text
    assert all(p['external'] is None for p in result.json()['providers'])


def test_token_budget_blocked_until_provider_reset(monkeypatch):
    model='test'
    q.observe('groq',model,{'x-ratelimit-limit-tokens':'8000','x-ratelimit-remaining-tokens':'100','x-ratelimit-reset-tokens':'1m'},200)
    with pytest.raises(p.SourceError):q.check_external('groq',tokens=101,scope=model)
    q.check_external('groq',tokens=99,scope=model)


def test_concurrent_grants_stop_at_three_and_disabled_does_not_show_extra(monkeypatch,client,accounts):
    monkeypatch.setenv('QUOTA_ADMIN_USER_IDS','1')
    monkeypatch.setenv('AI_DAILY_LIMIT','1')
    user=SimpleNamespace(id=1)
    def grant(_):
        try:q.grant('groq',q.window('day')[0],'Motivo de teste concorrente',str(uuid4()),user);return True
        except HTTPException as exc:
            assert exc.status_code==409
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:assert sum(pool.map(grant,range(9)))==3
    monkeypatch.setenv('AI_DAILY_LIMIT','0')
    provider=next(p for p in q.dashboard(user)['providers'] if p['provider']=='groq')
    assert provider['internal'][0]['effective_limit']==0
    with pytest.raises(p.SourceError):p.reserve('groq',0,daily=True)


def test_grant_cannot_override_private_work_window(monkeypatch,client,accounts,tmp_path):
    monkeypatch.setenv('QUOTA_ADMIN_USER_IDS','1');monkeypatch.setenv('AI_DAILY_LIMIT','1')
    q.grant('groq',q.window('day')[0],'Motivo suficiente',str(uuid4()),SimpleNamespace(id=1))
    path=tmp_path/'window.json'
    path.write_text(json.dumps({'deadline_utc':(q.now()+timedelta(hours=1)).isoformat(),'limits':{'groq':1},'baseline':[]}))
    monkeypatch.setenv('WEBSECAI_REQUEST_WINDOW_FILE',str(path))
    p.reserve('groq',1,daily=True)
    with pytest.raises(p.SourceError):p.reserve('groq',1,daily=True)


def test_calendar_resets_are_utc_and_month_rollover():
    stamp=datetime(2026,12,31,23,59,45,tzinfo=timezone.utc)
    assert q.window('month',stamp)==('2026-12',datetime(2027,1,1,tzinfo=timezone.utc))
    assert q.window('minute',stamp)[1]==datetime(2027,1,1,tzinfo=timezone.utc)


def test_tavily_sync_is_explicit_bounded_redacted_and_does_not_guess_reset(monkeypatch,client,accounts):
    route='/api/v1/usage/tavily/sync'
    assert client.post(route,headers=accounts[0]).status_code==403
    monkeypatch.setenv('QUOTA_ADMIN_USER_IDS','1')
    assert client.post(route,headers=accounts[0]).status_code==409
    monkeypatch.setenv('PROVIDER_USAGE_SYNC_ENABLED','true');monkeypatch.setenv('TAVILY_API_KEY','synthetic')
    calls=[]
    def fake(method,url,**kwargs):
        calls.append((method,url))
        return {'account':{'plan_usage':975,'plan_limit':1000,'private':'MUST_NOT_PERSIST'},'key':{'usage':200,'limit':None,'private':'MUST_NOT_PERSIST'}}
    monkeypatch.setattr(p,'json_request',fake)
    response=client.post(route,headers=accounts[0])
    assert response.status_code==200,response.text
    data=response.json()['observation']
    assert 'MUST_NOT_PERSIST' not in response.text
    account=next(d for d in data['dimensions'] if d['unit']=='credits_account')
    assert account['remaining']==25 and account['reset_at'] is None
    assert next(d for d in data['dimensions'] if d['unit']=='credits_key')['remaining'] is None
    assert client.post(route,headers=accounts[0]).status_code==429
    assert calls==[('GET','https://api.tavily.com/usage')]


def test_quota_postgresql_ddl_uses_timezone_aware_columns():
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql
    from app.models.quota import QuotaGrant,ProviderObservation
    for model,columns in {QuotaGrant:['created_at'],ProviderObservation:['observed_at','last_success_at','blocked_until']}.items():
        ddl=str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
        for column in columns:assert column+' TIMESTAMP WITH TIME ZONE' in ddl
