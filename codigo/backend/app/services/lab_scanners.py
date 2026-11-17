"""Normalize untrusted reports. Import provenance is declared, never attested execution."""
import hashlib
import json
import re
from app.services.lab_input import safe_path, scrub

SEVERITIES={"ERROR":"high","WARNING":"medium","INFO":"info","error":"high","warning":"medium","note":"info","HIGH":"high","CRITICAL":"high","MODERATE":"medium","MEDIUM":"medium","LOW":"low"}

def normalize(tool,raw,files):
    try: report=json.loads(raw)
    except (ValueError,RecursionError): raise ValueError("Relatório JSON inválido.") from None
    paths={f['path']:f for f in files}
    findings=[]
    warnings=[]
    def add(rule,path,line,end,title,description,severity='medium',recommendation='Rever o contexto e corrigir apenas após validação.',line_known=True):
        path=safe_path(path.removeprefix('./'))
        if path not in paths: raise ValueError("O relatório referencia um ficheiro ausente desta revisão.")
        if isinstance(line,bool) or not isinstance(line,int) or line<1 or line>paths[path]['lines']:raise ValueError("Linha do relatório fora do código recebido.")
        if not isinstance(end,int) or end<line or end>paths[path]['lines']:raise ValueError("Intervalo de linhas inválido.")
        rule=scrub(str(rule))[:120]
        digest=hashlib.sha256(f'{tool}:{rule}:{path}:{line}:{end}'.encode()).hexdigest()
        if any(f['id']==digest for f in findings):return
        if len(findings)>=200:raise ValueError("Mais de 200 achados; divida o relatório.")
        findings.append({'id':digest,'origin':'scanner_import','tool':tool,'rule':rule,'path':path,'line':line,'end_line':end,'line_known':line_known,
                         'title':scrub(str(title))[:150],'description':scrub(str(description))[:1600],
                         'severity':SEVERITIES.get(severity,severity if severity in {'high','medium','low','info'} else 'medium'),
                         'confidence':'medium','recommendation':scrub(recommendation)[:1000],'regression_test':'Confirmar a correção com um teste dedicado e repetir o motor.',
                         'snippet':'[Conteúdo omitido: potencial segredo]' if tool=='gitleaks' else '\n'.join(paths[path]['content'].splitlines()[line-1:min(end,line+4)]),
                         'related_paths':[]})
    try:
        if isinstance(report,dict) and report.get('version')=='2.1.0' and 'runs' in report:
            if not isinstance(report['runs'],list) or len(report['runs'])>10:raise ValueError()
            for run in report['runs']:
                driver=run['tool']['driver'].get('name','').lower()
                expected={'semgrep':('semgrep',),'osv':('osv-scanner','osv scanner'),'gitleaks':('gitleaks',)}[tool]
                if not any(x in driver for x in expected):raise ValueError("Motor SARIF não corresponde ao selecionado.")
                if run.get('invocations') and any(i.get('executionSuccessful') is False for i in run['invocations']):warnings.append('O motor comunicou execução incompleta no SARIF.')
                for result in run.get('results',[]):
                    loc=result['locations'][0]['physicalLocation']
                    region=loc.get('region',{})
                    line=region.get('startLine',1)
                    secret=tool=='gitleaks'
                    add(result.get('ruleId','unknown'),loc['artifactLocation']['uri'],line,region.get('endLine',line),
                        'Possível segredo no código' if secret else result.get('ruleId','Achado estático'),
                        'Valor potencialmente sensível omitido integralmente. Não foi testado.' if secret else result.get('message',{}).get('text','Achado importado.'),result.get('level','warning'),line_known='startLine' in region)
        elif tool=='semgrep':
            if not isinstance(report,dict) or not isinstance(report.get('results'),list):raise ValueError()
            if report.get('errors'):warnings.append('Semgrep comunicou erros; cobertura parcial.')
            for r in report['results']:
                add(r['check_id'],r['path'],r['start']['line'],r.get('end',r['start'])['line'],r['check_id'],r['extra'].get('message','Achado Semgrep.'),r['extra'].get('severity','WARNING'))
        elif tool=='gitleaks':
            if not isinstance(report,list):raise ValueError()
            for r in report:
                # NEVER read Secret, Match, Line, Email, Author, Commit or arbitrary metadata.
                add(r.get('RuleID','secret'),r['File'],r['StartLine'],r.get('EndLine',r['StartLine']),'Possível segredo no código','Valor omitido integralmente. Um padrão não comprova que a credencial esteja ativa.','high','Confirmar com o responsável; se real, revogar/substituir privadamente. Não testar a credencial.')
        elif tool=='osv':
            if not isinstance(report,dict) or not isinstance(report.get('results'),list):raise ValueError()
            for source in report['results']:
                for package in source['packages']:
                    name=package.get('package',{}).get('name','Dependência')
                    for vuln in package.get('vulnerabilities',[]):
                        add(vuln['id'],source['source']['path'],1,1,str(name)+' · '+vuln['id'],vuln.get('summary','Versão de dependência associada a um aviso OSV. Não prova exploração ou alcançabilidade.'),'medium','Rever aviso e versão corrigida; atualizar o lockfile e testar compatibilidade.',False)
        else:raise ValueError()
    except (KeyError,IndexError,TypeError,AttributeError,RecursionError):
        raise ValueError("Estrutura do relatório incompatível ou incompleta.") from None
    return {'findings':findings,'limitations':['Relatório importado pelo utilizador; a aplicação não atesta que o motor foi executado nem a autenticidade do ficheiro.','Correspondência declarada com a revisão recebida; sem prova de exploração.']+warnings,
            'summary':f'{len(findings)} achado(s) importado(s). Zero achados não comprova ausência de vulnerabilidades.','provenance':'user_import','partial':bool(warnings)}
