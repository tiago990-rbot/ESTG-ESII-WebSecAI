"""Manual CLI, never called by the web API. Use a disposable OS sandbox for untrusted projects."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import signal
import sys
import tempfile
import time

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'codigo'/'backend'))
from app.schemas.lab import ProjectCreate
from app.services.lab_input import prepare, safe_path, scrub
from app.services.lab_scanners import normalize

def terminate(proc):
    if os.name=='nt':
        taskkill=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'taskkill.exe'
        subprocess.run([str(taskkill),'/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False,timeout=10)
    else:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    if proc.poll() is None:proc.kill()
    proc.wait(timeout=10)

def bounded_process(command,cwd,output,timeout=90,report=None):
    # No shell, inherited application secrets, install scripts or source execution.
    env={key:val for key,val in os.environ.items() if key in {'PATH','SystemRoot','WINDIR','TEMP','TMP','SYSTEMROOT'}}
    env.update(SEMGREP_SEND_METRICS='off',SEMGREP_ENABLE_VERSION_CHECK='0',GIT_TERMINAL_PROMPT='0',HOME=str(cwd),USERPROFILE=str(cwd))
    with output.open('wb') as stdout:
        process_options={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
        proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=subprocess.DEVNULL,shell=False,**process_options)
        started=time.monotonic()
        try:
            while proc.poll() is None:
                if time.monotonic()-started>timeout or output.stat().st_size>1_000_000 or (report and report.exists() and report.stat().st_size>1_000_000):
                    terminate(proc);raise ValueError('Motor excedeu tempo/tamanho. Resultado descartado.')
                time.sleep(.05)
        finally:
            if proc.poll() is None:terminate(proc)
    if output.stat().st_size>1_000_000:raise ValueError('Saída do motor excedeu 1 MB.')
    return proc.returncode

def execute(source,tool,engine,out,allow_osv_network=False):
    source=source.resolve(strict=True);out=out.resolve()
    if not source.is_dir() or source.is_symlink():raise ValueError('Origem deve ser diretório autorizado, sem symlinks.')
    if out.is_relative_to(source) or (out.exists() and any(out.iterdir())):raise ValueError('Saída deve ser uma pasta nova e fora da origem. Resultados anteriores não são substituídos.')
    entries=[]
    # Reject symlinks at every level before opening files; read only explicitly supported inputs.
    for directory,dirs,names in os.walk(source,followlinks=False):
        for dirname in list(dirs):
            candidate=Path(directory)/dirname
            if candidate.is_symlink():raise ValueError('Links não são aceites.')
            if dirname.lower() in {'.git','.venv','node_modules','.next','dist','build'}:dirs.remove(dirname)
        for name in names:
            path=Path(directory)/name
            if path.is_symlink():raise ValueError('Links não são aceites.')
            relative=path.relative_to(source).as_posix()
            try:safe_path(relative)
            except ValueError:continue
            if path.stat().st_size>30_000:raise ValueError('Ficheiro acima de 30 KB.')
            entries.append({'path':relative,'content':path.read_text(encoding='utf-8')})
            if len(entries)>40:raise ValueError('Mais de 40 ficheiros suportados.')
    files,digest=prepare(ProjectCreate(name='runner',revision='manual',authorized=True,files=entries))
    binary=Path(engine).resolve(strict=True)
    expected={'gitleaks':{'gitleaks','gitleaks.exe'},'semgrep':{'semgrep','semgrep.exe'},'osv':{'osv-scanner','osv-scanner.exe'}}
    if binary.name.lower() not in expected[tool]:raise ValueError('Executável não corresponde ao motor escolhido.')
    if tool=='osv' and not allow_osv_network:raise ValueError('OSV pode consultar a base de avisos externa. Requer --allow-osv-network; não executa análise de chamadas/builds.')
    with tempfile.TemporaryDirectory(prefix='websecai-lab-') as temporary:
        job=Path(temporary);copy=job/'source';copy.mkdir()
        for f in entries:
            target=copy/f['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(f['content'],encoding='utf-8',newline='\n')
        raw=job/'raw.json';console=job/'console.bin'
        if tool=='gitleaks':
            command=[str(binary),'dir','source','--config',str(Path(__file__).with_name('gitleaks.toml')),'--redact=100','--report-format','json','--report-path',str(raw),'--exit-code','10','--no-banner','--no-color']
            success={0,10}
        elif tool=='semgrep':
            command=[str(binary),'scan','--config',str(Path(__file__).with_name('semgrep-rules.yml')),'--json','--metrics=off','--disable-version-check','--no-git-ignore','--output',str(raw),'source'];success={0,1}
        else:
            command=[str(binary),'scan','source','--format','json','--recursive','source'];success={0,1}
        code=bounded_process(command,job,console,report=raw)
        if code not in success:raise ValueError('Motor falhou. Não foi exportado um relatório limpo; verifique a instalação isolada.')
        if tool=='osv':raw=console
        if not raw.exists() or raw.stat().st_size>1_000_000:raise ValueError('Relatório ausente ou demasiado grande.')
        report=json.loads(raw.read_text(encoding='utf-8-sig'))
        def relative(path):
            path=str(path).replace('\\','/')
            if path.startswith(copy.as_posix()+'/'):path=path[len(copy.as_posix())+1:]
            return path.removeprefix('source/').removeprefix('./')
        # Rebuild a minimal native report. Drop secret-bearing and arbitrary metadata fields.
        if tool=='gitleaks':
            report=[{key:r[key] for key in ('RuleID','File','StartLine','EndLine') if key in r} for r in report]
            for r in report:r['File']=relative(r['File'])
        elif tool=='semgrep':
            report={'results':[{'check_id':scrub(r['check_id']),'path':relative(r['path']),'start':{'line':r['start']['line']},'end':{'line':r['end']['line']},'extra':{'message':scrub(r['extra'].get('message','Achado estático.')),'severity':r['extra'].get('severity','WARNING')}} for r in report['results']], 'errors':[{'message':'Motor comunicou erro; consulte cobertura.'} for _ in report.get('errors',[])]}
        else:
            report={'results':[{'source':{'path':relative(r['source']['path'])},'packages':[{'package':{'name':scrub(p.get('package',{}).get('name','Dependência'))},'vulnerabilities':[{'id':scrub(v['id']),'summary':scrub(v.get('summary','Aviso OSV.'))} for v in p.get('vulnerabilities',[])]} for p in r['packages']]} for r in report['results']]}
        raw_json=json.dumps(report,ensure_ascii=False)
        normalized=normalize(tool,raw_json,files)
        # Deliberately no raw report, source code, credentials or full process environment in output.
        out.mkdir(parents=True,exist_ok=True)
        (out/'report.json').write_text(raw_json,encoding='utf-8')
        envelope={'tool':tool,'version':'manual - see engine-sha256','source_digest':digest,'report_json':raw_json}
        (out/'import_payload.json').write_text(json.dumps(envelope,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest={'tool':tool,'engine_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'source_digest':digest,'exit_code':code,'findings':len(normalized['findings']),'source_execution':False,'network_opt_in':allow_osv_network,'limitations':normalized['limitations']}
        (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--tool',choices=['gitleaks','semgrep','osv'],required=True);parser.add_argument('--engine',required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--authorized',action='store_true',required=True);parser.add_argument('--allow-osv-network',action='store_true')
    args=parser.parse_args()
    try:manifest=execute(args.source,args.tool,args.engine,args.out,args.allow_osv_network)
    except Exception:
        print('Runner falhou; nenhum resultado deve ser tratado como uma análise limpa. Reveja caminhos, limites, versão e isolamento. Não são impressos erros brutos.',file=sys.stderr);return 2
    print(json.dumps({'tool':manifest['tool'],'findings':manifest['findings'],'source_digest':manifest['source_digest']}));return 0
if __name__=='__main__':raise SystemExit(main())
