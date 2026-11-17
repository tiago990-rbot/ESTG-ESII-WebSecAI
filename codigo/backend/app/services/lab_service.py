from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy import update
from app.db.session import SessionLocal
from app.models.lab import LabProject, LabRun, LabReview
from app.services import lab_ai, providers
from app.services.lab_input import scrub

def enabled():
    from app.core.config import value
    return value('SECURITY_LAB_ENABLED','false').lower()=='true'

def context_hash(findings):
    return hashlib.sha256(json.dumps(sorted(findings,key=lambda f:f['id']),sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def snapshot(db,project):
    reviews=db.query(LabReview).filter_by(project_id=project.id).order_by(LabReview.id).all()
    latest={}
    for row in reviews:
        latest[row.finding_id]={'sequence':row.sequence,'actor_id':row.actor_id,'status':row.status,'note':row.note,'created_at':row.created_at.isoformat()}
    # Most recent run per tool, including a failed retry; earlier results stay in the history.
    runs=[{'id':r.id,'tool':r.tool,'version':r.version,'status':r.status,'report':r.report,'created_at':r.created_at.isoformat()} for r in project.runs]
    last={r['tool']:r for r in runs}
    findings=[]
    for tool in ('semgrep','osv','gitleaks','ai'):
        run=last.get(tool)
        retained=False
        if run and run['status'] not in {'completed','partial'}:
            run=next((r for r in reversed(runs) if r['tool']==tool and r['status'] in {'completed','partial'}),None)
            retained=run is not None
        if run:
            findings.extend([{**f,'retained_from_earlier_attempt':retained,'review':latest.get(f['id'],{'sequence':0,'status':'pending','note':''})} for f in run['report'].get('findings',[])])
    synthesis=last.get('synthesis')
    if synthesis:
        synthesis={**synthesis,'is_current':synthesis['report'].get('context_hash')==context_hash(findings)}
    return {'id':project.id,'name':project.name,'revision':project.revision,'source_digest':project.digest,'created_at':project.created_at.isoformat(),
            'files':project.files,'runs':[{**r,'report':{k:v for k,v in r['report'].items() if k!='findings'}} for r in runs],'findings':findings,'synthesis':synthesis if synthesis and synthesis['status']=='completed' else None,
            'limitations':['Análise estática de código autorizado. Não foram executados builds, testes de exploração ou pedidos ao website.','Redação automática de segredos tem limitações. Envie apenas código previamente revisto e sem dados privados.','Achados de ferramentas e IA requerem validação humana. Ausência de achados não é certificação de segurança.']}

def execute_ai(run_id):
    with SessionLocal() as db:
        run=db.get(LabRun,run_id)
        if not run or run.status!='running':return
        project=db.get(LabProject,run.project_id)
        try:
            if run.tool=='ai':report,model=lab_ai.review(project.files,project.digest)
            else:
                findings=snapshot(db,project)['findings']
                report,model=lab_ai.synthesize(findings)
                report['context_hash']=context_hash(findings)
            status='completed'
        except providers.SourceError as exc:
            report,model,status={'message':exc.message},'',exc.status
        except Exception:
            # Never retain raw exceptions: they can contain untrusted model/source text.
            report,model,status={'message':'Análise interrompida ou resposta inválida. Nenhuma correção foi aplicada.'},'','error'
        db.execute(update(LabRun).where(LabRun.id==run_id,LabRun.status=='running').values(report=report,version=model or 'unknown',status=status))
        db.commit()

def recover():
    with SessionLocal.begin() as db:
        db.execute(update(LabRun).where(LabRun.status=='running').values(status='interrupted',report={'message':'Processo reiniciado. A análise não é retomada automaticamente; uma nova tentativa usa nova quota.'}))
