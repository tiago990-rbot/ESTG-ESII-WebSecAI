"""Saved static-review dossier. Export has no provider or runner side effects."""
from collections import Counter
from html import escape
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from app.services.investigation_pdf import draw_eye, date_label, INK, TEAL, MUTED, PALE, LINE

class SourceChart(Flowable):
    def __init__(self,findings):
        super().__init__();self.width=490;self.height=116;self.counts=Counter(f['tool'] for f in findings)
    def draw(self):
        c=self.canv;maximum=max([1,*self.counts.values()])
        for i,(key,label) in enumerate([('semgrep','Semgrep'),('osv','OSV'),('gitleaks','Gitleaks'),('ai','IA - hipoteses')]):
            y=98-i*27;c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(0,y,label)
            c.setFillColor(PALE);c.roundRect(102,y-2,320,10,3,fill=1,stroke=0)
            c.setFillColor(TEAL);count=self.counts[key]
            if count:c.roundRect(102,y-2,320*count/maximum,10,3,fill=1,stroke=0)
            c.setFillColor(INK);c.drawString(435,y,str(count))

class RelationshipMap(Flowable):
    def __init__(self,findings):
        super().__init__();self.width=490
        grouped={}
        for f in findings:grouped.setdefault(f['path'],set()).add(f['tool'])
        self.rows=list(grouped.items())[:8];self.height=35+len(self.rows)*26
    def draw(self):
        c=self.canv;c.setFont('Helvetica',8)
        for i,(path,tools) in enumerate(self.rows):
            y=self.height-22-i*26;c.setStrokeColor(LINE);c.line(125,y,230,y)
            c.setFillColor(TEAL);c.roundRect(0,y-9,125,20,5,fill=1,stroke=0);c.setFillColor(colors.white)
            c.drawString(8,y-2,', '.join(sorted(tools))[:25])
            c.setFillColor(PALE);c.roundRect(230,y-9,254,20,5,fill=1,stroke=0);c.setFillColor(INK)
            shown=path if len(path)<49 else '...'+path[-45:];c.drawString(238,y-2,shown)
        c.setFillColor(MUTED);c.setFont('Helvetica',7);c.drawString(0,0,'Ligacao = achado localizado no ficheiro. Nao representa exploracao ou causalidade.')

def lab_pdf(snapshot):
    buf=BytesIO();styles={
        'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=27,leading=32,textColor=INK,spaceAfter=18),
        'h':ParagraphStyle('heading',fontName='Helvetica-Bold',fontSize=16,leading=21,textColor=INK,spaceBefore=16,spaceAfter=12,keepWithNext=True),
        'sub':ParagraphStyle('sub',fontName='Helvetica-Bold',fontSize=10,leading=14,textColor=TEAL,spaceBefore=10,spaceAfter=7,keepWithNext=True),
        'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=14,textColor=INK,spaceAfter=9,splitLongWords=True),
        'small':ParagraphStyle('small',fontName='Helvetica',fontSize=7.5,leading=11,textColor=MUTED,spaceAfter=6,splitLongWords=True)}
    def p(text,style='body'):return Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])
    findings=snapshot['findings'];story=[]
    story += [Spacer(1,20),p('SECURITY LAB / ANALISE DE CODIGO','sub'),p(snapshot['name'],'title'),p('Revisão '+snapshot['revision']),p('Código: '+snapshot['source_digest'],'small'),p('Recebido: '+date_label(snapshot['created_at']),'small')]
    synthesis=snapshot.get('synthesis')
    if synthesis:
        story += [p('Análise de inteligência','h'),p(synthesis['report']['summary']),p('Origem: IA '+synthesis['version']+'; interpretação de achados, sem exploração.','small')]
        if not synthesis.get('is_current',True):story.append(p('Síntese desatualizada: os achados ou revisões humanas mudaram.','small'))
    else:
        story += [p('Leitura executiva','h'),p(f'{len(snapshot["files"])} ficheiro(s) recebidos; {len(findings)} achado(s) na seleção atual. A síntese IA não foi gerada. Este resumo de cobertura é calculado por regras locais.'),p('Próximo passo: validar os achados no contexto do projeto, rever prioridades e repetir a análise sobre uma revisão corrigida. Não existem conclusões de exploração.')]
    for note in snapshot['limitations']:story.append(p(note,'small'))
    story += [p('Cobertura e origens','h'),SourceChart(findings),p('Contagem por origem; não representa risco calculado. Uma origem sem achados pode não ter sido executada.','small')]
    rows=[[p('Origem','sub'),p('Estado / cobertura','sub'),p('Data de registo','sub')]]
    for r in snapshot['runs']:
        rows.append([p(r['tool']+' / '+r['version'],'small'),p(r['status']+' · '+r['report'].get('provenance','processamento local'),'small'),p(date_label(r['created_at']),'small')])
    if len(rows)==1:rows.append([p('Nenhum motor','small'),p('Código recebido, sem análise executada.','small'),p('-','small')])
    table=Table(rows,colWidths=[125,240,125],repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,LINE),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(table)
    story += [p('Mapa de relações observadas','h'),RelationshipMap(findings),p('Mostra até oito ficheiros; todos os achados constam do anexo.','small')]
    if synthesis:
        report=synthesis['report']
        story.append(p('Prioridades e correlações da IA','h'))
        index={f['id']:i+1 for i,f in enumerate(findings)}
        for priority in report['priorities']:story.append(p('Acompanhar achado '+str(index.get(priority,'histórico'))+'.'))
        for relation in report['correlations']:
            refs=', '.join(str(index.get(i,'histórico')) for i in relation['finding_ids'])
            story.extend([p('Achados '+refs,'sub'),p(relation['explanation']),p('Como validar: '+relation['validation'])])
        for note in report['limitations']:story.append(p(note,'small'))
    story.append(PageBreak());story.append(p('Achados e validação humana','title'))
    if not findings:story.append(p('Sem achados disponíveis na seleção atual. Consulte o histórico e os estados dos motores; isto não comprova segurança.'))
    for i,f in enumerate(findings,1):
        story.extend([p(f'{i:02d} / {f["title"]}','h'),p(f'{f["severity"].upper()} · {f["tool"]} · '+('Hipótese IA' if f['origin']=='ai_hypothesis' else 'Importação de scanner'),'sub'),
            p(f['path']+(f' : {f["line"]}-{f["end_line"]}' if f.get('line_known',True) else ' · localização no ficheiro, sem linha fornecida'),'small'),p('ID: '+f['id'],'small'),p(f['description']),p('Correção proposta: '+f['recommendation']),p('Teste a acrescentar: '+f['regression_test'])])
        review=f.get('review',{})
        story.append(p('Revisão humana: '+review.get('status','pending')+'. '+review.get('note',''),'small'))
        story.append(p('Uma marcação humana de corrigido não equivale a uma nova execução limpa.','small'))
    story.extend([p('Inventário da revisão','h')])
    for f in snapshot['files']:story.append(p(f['path']+f' · {f["lines"]} linhas · SHA-256 '+f['sha256']+(' · Conteúdo redigido' if f['redacted'] else ''),'small'))
    def page(c,doc):
        c.saveState();draw_eye(c,48,797,.42);c.setFillColor(INK);c.setFont('Helvetica-Bold',10);c.drawString(84,805,'WebSecAI');c.setFont('Helvetica',7);c.setFillColor(MUTED);c.drawRightString(547,805,'SECURITY LAB / CODIGO AUTORIZADO')
        c.setStrokeColor(LINE);c.line(48,788,547,788);c.line(48,45,547,45);c.drawString(48,31,'Revisao estatica. Sem prova de exploracao.');c.drawRightString(547,31,f'Pagina {doc.page}');c.restoreState()
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=48,rightMargin=48,topMargin=73,bottomMargin=64,title='WebSecAI - Security Lab',author='WebSecAI')
    doc.build(story,onFirstPage=page,onLaterPages=page);return buf.getvalue()
