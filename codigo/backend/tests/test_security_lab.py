import base64
from io import BytesIO
import json
import stat
import zipfile
from copy import deepcopy
import pytest
from app.schemas.lab import ProjectCreate
from app.services import lab_input, lab_scanners, lab_ai, providers

VULNERABLE="import sqlite3\ndef lookup(name):\n    db=sqlite3.connect(':memory:')\n    return db.execute(\"SELECT name FROM users WHERE name='\" + name + \"'\").fetchall()\n"
FIXED="import sqlite3\ndef lookup(name):\n    db=sqlite3.connect(':memory:')\n    return db.execute('SELECT name FROM users WHERE name=?', (name,)).fetchall()\n"

def payload(code=VULNERABLE):return {'name':'Laboratório fictício','revision':'fixture-01','authorized':True,'files':[{'path':'app.py','content':code}]}

@pytest.fixture
def project(client,accounts,monkeypatch):
    monkeypatch.setenv('SECURITY_LAB_ENABLED','true')
    response=client.post('/api/v1/lab',headers=accounts[0],json=payload())
    assert response.status_code==201,response.text
    return response.json()

def semgrep(line=4):return {'results':[{'check_id':'test.sql-concat','path':'app.py','start':{'line':line},'end':{'line':line},'extra':{'message':'Construção SQL concatenada exige validação.','severity':'ERROR'}}]}

def import_payload(project,tool='semgrep',report=None):return {'tool':tool,'version':'synthetic-fixture','source_digest':project['source_digest'],'report_json':json.dumps(report if report is not None else semgrep())}

def test_default_disabled_and_authentication(client,accounts):
    assert client.get('/api/v1/lab').status_code==401
    assert client.get('/api/v1/lab',headers=accounts[0]).status_code==503
    assert client.get('/api/v1/lab/configuration',headers=accounts[0]).json()['runner']=='import_only'

@pytest.mark.parametrize('path',['../app.py','/app.py','C:/app.py','a\\app.py','.env','nested/.env.local','node_modules/app.js','folder/../app.py','app.exe','app.py.'])
def test_unsafe_paths_are_rejected(path):
    with pytest.raises(ValueError):lab_input.prepare(ProjectCreate.model_validate(dict(payload(),files=[{'path':path,'content':'test'}])))

def test_zip_traversal_symlink_bomb_and_unicode():
    for path,mode,content in [('../app.py',0,'print(1)'),('link.py',stat.S_IFLNK|0o777,'target'),('huge.py',0,'A'*40000)]:
        buf=BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            info=zipfile.ZipInfo(path);info.external_attr=mode<<16;z.writestr(info,content)
        data=ProjectCreate.model_validate(dict(payload(),files=[],zip_base64=base64.b64encode(buf.getvalue()).decode()))
        with pytest.raises(ValueError):lab_input.prepare(data)

def test_redaction_before_storage_prompt_and_errors(client,accounts,monkeypatch):
    monkeypatch.setenv('SECURITY_LAB_ENABLED','true')
    secret='SYNTHETIC_DO_NOT_PERSIST_ABC123'
    data=payload('API_KEY = "'+secret+'"\nprint("ok")\n')
    response=client.post('/api/v1/lab',headers=accounts[0],json=data)
    assert response.status_code==201
    assert secret not in response.text and response.json()['files'][0]['redacted']
    assert secret not in json.dumps(lab_ai.select_code(response.json()['files']))
    data['files'][0]['content']=secret*2000
    error=client.post('/api/v1/lab',headers=accounts[0],json=data)
    assert error.status_code==422 and secret not in error.text

def test_isolation_history_import_references_and_cas(client,accounts,project):
    path='/api/v1/lab/'+project['id']
    assert client.get(path,headers=accounts[1]).status_code==404
    assert client.get(path+'/report',headers=accounts[1]).status_code==404
    assert client.post(path+'/imports',headers=accounts[1],json=import_payload(project)).status_code==404
    wrong=client.post(path+'/imports',headers=accounts[0],json=dict(import_payload(project),source_digest='0'*64))
    assert wrong.status_code==409
    bad=semgrep(999)
    assert client.post(path+'/imports',headers=accounts[0],json=import_payload(project,report=bad)).status_code==422
    response=client.post(path+'/imports',headers=accounts[0],json=import_payload(project))
    assert response.status_code==201,response.text
    finding=response.json()['findings'][0]
    assert finding['origin']=='scanner_import' and finding['severity']=='high'
    review={'status':'false_positive','note':'Teste de revisão humana, requer contexto.','previous_sequence':0}
    review_path=path+'/findings/'+finding['id']+'/reviews'
    assert client.post(review_path,headers=accounts[0],json=review).status_code==201
    assert client.post(review_path,headers=accounts[0],json=review).status_code==409
    assert client.delete(path,headers=accounts[1]).status_code==404
    assert client.get(path,headers=accounts[0]).json()['findings'][0]['review']['sequence']==1

def test_gitleaks_values_never_leave_import(client,accounts,project):
    secret='SYNTHETIC_ONLY_NOT_A_REAL_SECRET'
    raw=[{'RuleID':'test-key','File':'app.py','StartLine':2,'EndLine':2,'Secret':secret,'Match':secret,'Line':secret,'Author':secret,'Email':secret,'Description':secret}]
    response=client.post('/api/v1/lab/'+project['id']+'/imports',headers=accounts[0],json=import_payload(project,'gitleaks',raw))
    assert response.status_code==201,response.text
    assert secret not in response.text
    finding=response.json()['findings'][0]
    assert finding['snippet']=='[Conteúdo omitido: potencial segredo]'

def test_sarif_adapter_checks_tool_paths_and_empty_report(project):
    raw={'version':'2.1.0','runs':[{'tool':{'driver':{'name':'Semgrep'}},'results':[{'ruleId':'test.sql','level':'error','message':{'text':'Possível SQL concatenado.'},'locations':[{'physicalLocation':{'artifactLocation':{'uri':'app.py'},'region':{'startLine':4,'endLine':4}}}]}]}]}
    assert len(lab_scanners.normalize('semgrep',json.dumps(raw),project['files'])['findings'])==1
    with pytest.raises(ValueError):lab_scanners.normalize('gitleaks',json.dumps(raw),project['files'])
    raw['runs'][0]['results']=[]
    empty=lab_scanners.normalize('semgrep',json.dumps(raw),project['files'])
    assert empty['findings']==[] and 'não comprova' in empty['summary']

def test_osv_dependency_is_not_given_an_invented_line():
    files,_=lab_input.prepare(ProjectCreate.model_validate(dict(payload(),files=[{'path':'requirements.txt','content':'flask==1.0\n'}])))
    raw={'results':[{'source':{'path':'requirements.txt','type':'lockfile'},'packages':[{'package':{'name':'flask','version':'1.0'},'vulnerabilities':[{'id':'TEST-2026-0001','summary':'Fixture: versão afetada, sem prova de exploração.'}]}]}]}
    f=lab_scanners.normalize('osv',json.dumps(raw),files)['findings'][0]
    assert f['line_known'] is False and f['path']=='requirements.txt'

def test_independent_ai_receives_code_without_scanner_findings(monkeypatch,project):
    captured=[]
    def fake(data,schema):
        captured.append(data)
        return {'summary':'Hipótese de concatenação SQL para validação.','findings':[{'title':'Concatenação SQL','severity':'high','confidence':'medium','path':'app.py','line':4,'end_line':4,'reasoning':'A entrada chega à consulta por concatenação. O contexto real deve ser validado.','recommendation':'Usar parâmetros na consulta.','regression_test':'Verificar tratamento literal de entrada inesperada.','related_paths':[]}],'limitations':['Exemplo controlado, modelo simulado.']},'mock-contract'
    monkeypatch.setattr(lab_ai,'call_model',fake)
    report,model=lab_ai.review(project['files'],project['source_digest'])
    assert 'code' in captured[0]['files'][0] and 'findings' not in captured[0]
    assert report['findings'][0]['origin']=='ai_hypothesis'
    project['files'][0]['lines']=1
    # Validation uses precisely the lines sent, not the declared total.
    def nonexistent(data,schema):
        result,_=fake(data,schema);result['findings'][0]['path']='missing.py';return result,'mock'
    monkeypatch.setattr(lab_ai,'call_model',nonexistent)
    with pytest.raises(providers.SourceError):lab_ai.review(project['files'],project['source_digest'])

def test_code_selection_is_bounded_and_references_only_visible_lines():
    data=ProjectCreate.model_validate(dict(payload(),files=[{'path':'a.py','content':'print(1)\n'*2000},{'path':'b.ts','content':'export const n = 1;\n'*1000}]))
    files,_=lab_input.prepare(data);selection=lab_ai.select_code(files)
    assert len(selection)==2
    assert all(s['included_lines']<s['total_lines'] for s in selection)

def test_ai_errors_keep_case_and_do_not_retry(client,accounts,project,monkeypatch):
    path='/api/v1/lab/'+project['id']
    assert client.post(path+'/ai/review',headers=accounts[0],json={'consent_external_ai':False}).status_code==422
    assert client.post(path+'/ai/review',headers=accounts[0],json={'consent_external_ai':True}).status_code==409
    monkeypatch.setenv('GROQ_API_KEY','synthetic-test-key')
    calls=[]
    def fail(*a,**k):calls.append(True);raise providers.SourceError('rate_limited','Quota fictícia atingida.')
    monkeypatch.setattr(providers,'json_request',fail)
    assert client.post(path+'/ai/review',headers=accounts[0],json={'consent_external_ai':True}).status_code==202
    result=client.get(path,headers=accounts[0]).json()
    assert len(calls)==1 and result['runs'][-1]['status']=='rate_limited'
    assert result['files'] and not result['findings']

def test_imported_pdf_is_escaped_and_does_not_call_models(client,accounts,project):
    path='/api/v1/lab/'+project['id']
    raw=semgrep();raw['results'][0]['extra']['message']='<script>untrusted & data</script>'
    assert client.post(path+'/imports',headers=accounts[0],json=import_payload(project,report=raw)).status_code==201
    response=client.get(path+'/report',headers=accounts[0])
    assert response.status_code==200,response.text[:200]
    assert response.content.startswith(b'%PDF-')

def test_chunked_and_large_input_rejected_without_echo(client,accounts,monkeypatch):
    monkeypatch.setenv('SECURITY_LAB_ENABLED','true')
    response=client.post('/api/v1/lab',headers={**accounts[0],'Content-Type':'application/json'},content=(b'x'*800000 for _ in range(3)))
    assert response.status_code==413


def test_synthesis_currentness_changes_with_human_review(client,accounts,project,monkeypatch):
    path='/api/v1/lab/'+project['id']
    imported=client.post(path+'/imports',headers=accounts[0],json=import_payload(project)).json()
    finding=imported['findings'][0]
    monkeypatch.setenv('GROQ_API_KEY','synthetic')
    def synthesize(findings):return {'summary':'Simulação contratual de síntese com referências existentes.','priorities':[findings[0]['id']],'correlations':[],'limitations':['Simulação, sem modelo real.']},'mock-contract'
    monkeypatch.setattr(lab_ai,'synthesize',synthesize)
    assert client.post(path+'/ai/synthesis',headers=accounts[0],json={'consent_external_ai':True}).status_code==202
    assert client.get(path,headers=accounts[0]).json()['synthesis']['is_current']
    assert client.post(path+'/findings/'+finding['id']+'/reviews',headers=accounts[0],json={'status':'confirmed','note':'Contexto revisto no laboratório.','previous_sequence':0}).status_code==201
    result=client.get(path,headers=accounts[0])
    assert result.headers['cache-control']=='no-store'
    assert result.json()['synthesis']['is_current'] is False
    assert all('findings' not in run['report'] for run in result.json()['runs'])


def test_synthesis_rejects_fake_or_same_source_correlations(monkeypatch,project):
    f=lab_scanners.normalize('semgrep',json.dumps(semgrep()),project['files'])['findings'][0]
    g=dict(f,id='b'*64)
    def fake(data,schema):return {'summary':'Síntese simulada para verificar validação.','priorities':[f['id']],'correlations':[{'finding_ids':[f['id'],g['id']],'explanation':'Mesma fonte não deve passar como duas origens.','validation':'Confirmar as origens antes de correlacionar.'}],'limitations':['Teste simulado.']},'mock'
    monkeypatch.setattr(lab_ai,'call_model',fake)
    with pytest.raises(providers.SourceError):lab_ai.synthesize([f,g])


def test_cancel_does_not_execute_and_previous_findings_remain_accessible(client,accounts,project,monkeypatch):
    from app.db.session import SessionLocal
    from app.models.lab import LabRun
    from app.services.lab_service import execute_ai
    from uuid import uuid4
    path='/api/v1/lab/'+project['id']
    first=client.post(path+'/imports',headers=accounts[0],json=import_payload(project)).json()
    run_id=first['runs'][0]['id']
    assert client.get(path+'/runs/'+run_id,headers=accounts[1]).status_code==404
    assert client.get(path+'/runs/'+run_id,headers=accounts[0]).json()['report']['findings']
    with SessionLocal.begin() as db:
        current=str(uuid4());db.add(LabRun(id=current,project_id=project['id'],tool='semgrep',version='fixture',status='running',report={}))
    assert client.post(path+'/runs/'+current+'/cancel',headers=accounts[0]).status_code==200
    monkeypatch.setattr(lab_ai,'review',lambda *a:pytest.fail('Cancelled task must not call AI'))
    execute_ai(current)
    detail=client.get(path,headers=accounts[0]).json()
    assert detail['findings'][0]['retained_from_earlier_attempt'] is True
    assert detail['runs'][-1]['status']=='cancelled'


def test_postgresql_ddl_preserves_offsets_for_new_timestamp_columns():
    # Compile the actual migration table metadata, without connecting to PostgreSQL.
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql
    from app.models.quota import QuotaGrant,ProviderObservation
    from app.models.lab import LabProject,LabRun,LabReview
    expected={QuotaGrant:['created_at'],ProviderObservation:['observed_at','last_success_at','blocked_until'],LabProject:['created_at'],LabRun:['created_at'],LabReview:['created_at']}
    for model,columns in expected.items():
        ddl=str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
        for column in columns:assert column+' TIMESTAMP WITH TIME ZONE' in ddl
