from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import value
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.lab import LabProject, LabRun, LabReview
from app.schemas.lab import ProjectCreate, ReportImport, CodeReviewRequest, FindingReview
from app.services import lab_service, lab_input, lab_scanners

router=APIRouter(prefix='/api/v1/lab',tags=['security-lab'])

def available():
    if not lab_service.enabled():raise HTTPException(503,'Security Lab desativado nesta instalação. O administrador pode ativar o módulo estático.')

def owned(db,user,id):
    project=db.query(LabProject).filter_by(id=id,user_id=user.id).first()
    if not project:raise HTTPException(404,'Projeto não encontrado.')
    return project

def lock(db,project,admit=True):
    db.execute(update(LabProject).where(LabProject.id==project.id).values(name=LabProject.name))
    db.expire(project,['runs'])
    if any(r.status=='running' for r in project.runs):raise HTTPException(409,'Aguarde ou cancele a análise em curso.')
    if admit and len(project.runs)>=16:raise HTTPException(429,'Limite de 16 execuções/importações por revisão. Crie uma nova revisão apenas se o código mudou.')

@router.get('/configuration')
def configuration(user:User=Depends(get_current_user)):
    return {'enabled':lab_service.enabled(),'ai_configured':bool(value('GROQ_API_KEY')),'runner':'import_only','languages':['Python','JavaScript','TypeScript'],
            'limits':{'files':40,'file_bytes':30000,'total_bytes':150000,'projects':10,'runs_per_project':16},
            'note':'Os motores são executados separadamente em ambiente controlado; esta API não executa código recebido.'}

@router.get('')
def projects(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available()
    rows=db.query(LabProject).filter_by(user_id=user.id).order_by(LabProject.created_at.desc()).limit(10).all()
    return [{'id':p.id,'name':p.name,'revision':p.revision,'source_digest':p.digest,'created_at':p.created_at.isoformat(),'file_count':len(p.files)} for p in rows]

@router.post('',status_code=201)
def create(data:ProjectCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available()
    # Serialize admission per owner so concurrent uploads cannot exceed storage quotas.
    db.execute(update(User).where(User.id==user.id).values(auth_version=User.auth_version))
    rows=db.query(LabProject).filter_by(user_id=user.id).all()
    recent=sum(p.created_at>datetime.now(timezone.utc)-timedelta(hours=1) for p in rows)
    if len(rows)>=10 or recent>=3:raise HTTPException(429,'Limite de 10 projetos guardados ou três envios por hora atingido.')
    try:files,digest=lab_input.prepare(data)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    if any(p.digest==digest for p in rows):raise HTTPException(409,'Esta revisão já existe no teu histórico.')
    project=LabProject(id=str(uuid4()),user_id=user.id,name=lab_input.scrub(data.name.strip()) or 'Projeto',revision=lab_input.scrub(data.revision.strip()) or 'Revisão',digest=digest,files=files)
    db.add(project);db.commit()
    return lab_service.snapshot(db,project)

@router.get('/{project_id}')
def detail(project_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();return lab_service.snapshot(db,owned(db,user,project_id))

@router.post('/{project_id}/imports',status_code=201)
def import_report(project_id:str,data:ReportImport,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();project=owned(db,user,project_id);lock(db,project)
    if data.source_digest!=project.digest:raise HTTPException(409,'Relatório de outra revisão. Confirme o digest do código original.')
    try:report=lab_scanners.normalize(data.tool,data.report_json,project.files)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    db.add(LabRun(id=str(uuid4()),project_id=project.id,tool=data.tool,version=lab_input.scrub(data.version),status='partial' if report['partial'] else 'completed',report=report))
    db.commit();db.expire_all();return lab_service.snapshot(db,project)

@router.get('/{project_id}/runs/{run_id}')
def historical_run(project_id:str,run_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();owned(db,user,project_id)
    run=db.query(LabRun).filter_by(id=run_id,project_id=project_id).first()
    if not run:raise HTTPException(404,'Execução não encontrada.')
    return {'id':run.id,'tool':run.tool,'version':run.version,'status':run.status,'report':run.report,'created_at':run.created_at.isoformat()}

@router.post('/{project_id}/ai/{task}',status_code=202)
def analyze(project_id:str,task:str,data:CodeReviewRequest,tasks:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available()
    if task not in {'review','synthesis'}:raise HTTPException(404,'Tarefa desconhecida.')
    project=owned(db,user,project_id);lock(db,project)
    if not value('GROQ_API_KEY'):raise HTTPException(409,'IA sem configuração nesta instalação. Nenhuma quota consumida.')
    if task=='synthesis' and not lab_service.snapshot(db,project)['findings']:raise HTTPException(409,'Sem achados para cruzar.')
    run=LabRun(id=str(uuid4()),project_id=project.id,tool='ai' if task=='review' else 'synthesis',status='running',report={})
    db.add(run);db.commit();tasks.add_task(lab_service.execute_ai,run.id)
    return {'id':run.id,'status':'running'}

@router.post('/{project_id}/runs/{run_id}/cancel')
def cancel(project_id:str,run_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();owned(db,user,project_id)
    changed=db.execute(update(LabRun).where(LabRun.id==run_id,LabRun.project_id==project_id,LabRun.status=='running').values(status='cancelled',report={'message':'Resultado cancelado. Um pedido já enviado pode consumir quota; o fornecedor não é interrompido.'})).rowcount
    if not changed:raise HTTPException(409,'Execução inexistente ou já terminada.')
    db.commit();return {'status':'cancelled'}

@router.post('/{project_id}/findings/{finding_id}/reviews',status_code=201)
def review(project_id:str,finding_id:str,data:FindingReview,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();project=owned(db,user,project_id);lock(db,project,admit=False)
    if finding_id not in {f['id'] for f in lab_service.snapshot(db,project)['findings']}:raise HTTPException(404,'Achado não encontrado nesta revisão.')
    previous=db.query(LabReview).filter_by(project_id=project_id,finding_id=finding_id).order_by(LabReview.sequence.desc()).first()
    seq=previous.sequence if previous else 0
    if data.previous_sequence!=seq:raise HTTPException(409,'A revisão humana mudou. Atualize o projeto.')
    db.add(LabReview(project_id=project_id,finding_id=finding_id,sequence=seq+1,actor_id=user.id,status=data.status,note=lab_input.scrub(data.note)))
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Revisão concorrente; atualize o projeto.') from None
    return lab_service.snapshot(db,project)

@router.get('/{project_id}/report')
def report_pdf(project_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();project=owned(db,user,project_id)
    from app.services.lab_pdf import lab_pdf
    return Response(lab_pdf(lab_service.snapshot(db,project)),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="websecai-code-{project.id}.pdf"','Cache-Control':'no-store'})

@router.delete('/{project_id}',status_code=204)
def delete(project_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    available();project=owned(db,user,project_id);lock(db,project,admit=False)
    db.query(LabReview).filter_by(project_id=project_id).delete();db.delete(project);db.commit()
