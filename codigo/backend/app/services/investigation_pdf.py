"""Professional, snapshot-only intelligence report. Export never calls a provider."""
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, CondPageBreak, Table, TableStyle, KeepTogether
from app.services.intelligence import QUESTIONS, CONFIDENCE, JUDGEMENT, CORRELATION, ASSESSMENT, safe_source
from app.services.investigation_pdf_visuals import TimelineVisual, ModuleVolumeVisual, RelationVisual, graph_data, balanced_pages

INK = colors.HexColor("#112b38")
TEAL = colors.HexColor("#147b73")
MUTED = colors.HexColor("#556c77")
PALE = colors.HexColor("#eff6f5")
LINE = colors.HexColor("#d7e2e5")
AMBER = colors.HexColor("#805822")
PROVIDERS = {"osint": "Pesquisa pública", "technical": "Verificações técnicas", "urlhaus": "URLhaus", "phishtank": "PhishTank", "kev": "CISA KEV", "exposure": "Exposição de dados", "ai": "Síntese IA", "message": "Regras da mensagem", "hibp_catalog": "HIBP — metadados públicos", "urlscan": "urlscan — pesquisa passiva"}
STATUS = {"completed": "Concluída", "partial": "Parcial", "running": "Em curso", "queued": "Em fila", "interrupted": "Interrompida", "error": "Erro", "success": "Consultada", "no_results": "Sem correspondências", "demo": "Demonstração", "not_configured": "Sem acesso", "not_requested": "Não solicitada", "rate_limited": "Quota atingida", "access_denied": "Acesso recusado", "stale": "Síntese desatualizada", "unverified": "Por verificar", "allegation": "Alegação", "reported": "Reportado pela fonte", "known_exploited": "Exploração conhecida"}

def date_label(value):
    if not value:
        return "Desconhecida"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if len(str(value)) == 10:
            return parsed.strftime("%d/%m/%Y")
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    except (ValueError, TypeError):
        return "Data por validar"

def draw_eye(canvas, x, y, scale=1):
    canvas.saveState()
    canvas.translate(x, y)
    canvas.scale(scale, scale)
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(1.5)
    path = canvas.beginPath()
    path.moveTo(2, 17)
    path.curveTo(10, 29, 18, 34, 30, 34)
    path.curveTo(42, 34, 50, 29, 58, 17)
    path.curveTo(50, 5, 42, 0, 30, 0)
    path.curveTo(18, 0, 10, 5, 2, 17)
    canvas.drawPath(path)
    canvas.circle(30, 17, 11, stroke=1, fill=0)
    canvas.setFillColor(TEAL)
    canvas.circle(30, 17, 4.5, stroke=0, fill=1)
    canvas.line(30, -4, 30, 3)
    canvas.line(30, 31, 30, 38)
    canvas.restoreState()

def investigation_pdf(snapshot: dict) -> bytes:
    buffer = BytesIO()
    width, height = A4
    content_width = width - 96
    styles = {
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9, leading=14, textColor=INK, spaceAfter=8, alignment=TA_LEFT, splitLongWords=True),
        "small": ParagraphStyle("Small", fontName="Helvetica", fontSize=7.5, leading=11, textColor=MUTED, spaceAfter=6, splitLongWords=True),
        "label": ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=8, leading=12, textColor=TEAL, spaceAfter=9, tracking=1),
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=29, leading=34, textColor=INK, spaceAfter=17, wordWrap="CJK"),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=21, leading=27, textColor=INK, spaceAfter=17, keepWithNext=True),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=17, textColor=INK, spaceBefore=12, spaceAfter=8, keepWithNext=True),
        "h3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=INK, spaceBefore=9, spaceAfter=6, keepWithNext=True),
        "tableHead": ParagraphStyle("TableHead", fontName="Helvetica-Bold", fontSize=7.5, leading=11, textColor=TEAL),
        "callout": ParagraphStyle("Callout", fontName="Helvetica", fontSize=9, leading=14, textColor=INK),
        "url": ParagraphStyle("URL", fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=TEAL, wordWrap="CJK", splitLongWords=True),
        "question": ParagraphStyle("Question", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=INK, spaceBefore=10, spaceAfter=6),
        "answer": ParagraphStyle("Answer", fontName="Helvetica", fontSize=8.5, leading=12.5, textColor=INK, spaceAfter=6),
    }
    story = []
    entries = snapshot.get("evidence", [])
    previous = snapshot.get("previous_evidence", [])
    index = {entry["id"]: position + 1 for position, entry in enumerate(entries + previous)}
    reports = snapshot.get("reports", [])
    latest = reports[-1] if reports else None
    current = latest if latest and latest.get("is_current", False) else None
    analysis = current["report"].get("intelligence") if current else None
    technical = snapshot.get("technical")
    technical_run = next((run for run in snapshot.get("runs", []) if run["provider"] == "technical"), None)
    technical_retained = bool(technical and technical_run and technical_run["status"] not in {"success", "demo"})
    target = snapshot.get("domain") or snapshot.get("target", "Mensagem suspeita")
    demo = snapshot.get("is_demo", False)

    def paragraph(text, style="body"):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])
    def add(text, style="body"):
        story.append(paragraph(text, style))
    def refs(ids):
        links = [f'<link href="#evidence-E{index[eid]}" color="#147b73">[E{index[eid]}]</link>' if eid in index else "[Referência indisponível]" for eid in ids]
        if links:
            story.append(Paragraph("Evidências: " + " ".join(links), styles["small"]))
    def note(text):
        block = Table([[paragraph(text, "callout")]], colWidths=[content_width])
        block.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("LINEBEFORE", (0, 0), (0, -1), 2, TEAL), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        story.extend([block, Spacer(1, 12)])
    def section(number, title, new_page=False):
        if new_page:
            story.append(PageBreak())
        else:
            story.extend([CondPageBreak(200), Spacer(1, 22)])
        add(number + " / WEBSECAI", "label")
        add(title, "h1")
    def table(headers, rows, widths):
        data = [[paragraph(value, "tableHead") for value in headers]] + [[paragraph(value, "small") for value in row] for row in rows]
        block = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), PALE), ("LINEBELOW", (0, 0), (-1, 0), .8, LINE), ("LINEBELOW", (0, 1), (-1, -1), .4, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        story.extend([block, Spacer(1, 12)])
    def legacy_report(report):
        add(report.get("summary", "Sem resumo."))
        for key, label in [("observations", "Observações"), ("recommendations", "Recomendações")]:
            add(label, "h2")
            for claim in report.get(key, []):
                add(claim["text"])
                refs(claim.get("evidence_ids", []))

    def chrome(canvas, doc):
        canvas.saveState()
        draw_eye(canvas, 46, height - 61, .65)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.setFillColor(INK)
        canvas.drawString(94, height - 43, "WebSecAI")
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(TEAL)
        canvas.drawString(94, height - 55, "THREAT INTELLIGENCE / ANALISE TECNICA / IA")
        canvas.setStrokeColor(LINE)
        canvas.line(48, height - 75, width - 48, height - 75)
        if demo:
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(AMBER)
            canvas.drawRightString(width - 48, height - 42, "DEMONSTRAÇÃO")
            canvas.setFont("Helvetica", 7)
            canvas.drawRightString(width - 48, height - 54, "Dados fictícios / sem LLM")
        canvas.setStrokeColor(LINE)
        canvas.line(48, 45, width - 48, 45)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(48, 31, "WebSecAI | " + str(target)[:58])
        canvas.drawRightString(width - 48, 31, "Página " + str(doc.page))
        canvas.restoreState()

    add("RELATÓRIO DE INTELIGÊNCIA E EXPOSIÇÃO", "label")
    add(target, "title")
    if snapshot.get("organization"):
        add(snapshot["organization"], "h2")
    add("Documento de apoio à decisão | " + date_label(snapshot.get("created_at")), "small")
    add("Dossiê " + str(snapshot.get("id", "exemplo"))[:8] + " | Estado da recolha: " + STATUS.get(snapshot.get("status"), snapshot.get("status", "Desconhecido")), "small")
    if demo:
        note("DEMONSTRAÇÃO: todos os dados são fictícios. O texto foi escrito por regras locais, sem chamadas a fontes ou a modelos de IA. Não representa uma avaliação de uma empresa real.")
    if snapshot.get("status") in {"queued", "running"}:
        note("RECOLHA EM CURSO: este documento é provisório e pode estar incompleto.")
    score = str(technical.get("score")) + "/100" if technical else "Não avaliada"
    if technical_retained:
        score += " (anterior)"
    rows = [[str(len(entries)) + " evidências atuais", score, "Atual" if current else "Anterior" if latest else "Indisponível"]]
    table(["EVIDÊNCIAS", "POSTURA TÉCNICA", "SÍNTESE"], rows, [content_width / 3] * 3)
    add("Referências atuais por dimensão: " + str(sum(entry.get("provider") == "technical" for entry in entries)) + " técnicas; " + str(sum(entry.get("provider") in {"osint", "hibp_catalog"} for entry in entries)) + " de pesquisa pública; " + str(sum(entry.get("category") == "kev_general" for entry in entries)) + " de contexto global KEV. São referências, não contagens de incidentes.", "small")
    add("Resumo executivo", "h2")
    if current:
        add(current["report"]["summary"])
    else:
        add("Não existe uma análise IA atual para esta recolha. Este documento organiza os resultados disponíveis, a cobertura e os pontos por esclarecer. Não apresenta uma conclusão automática de segurança ou de intrusão.")
    add("Âmbito e decisão", "h2")
    add(("A investigação reúne verificações técnicas e pesquisa de Threat Intelligence." if technical else "A investigação contém pesquisa e indicadores disponíveis, sem avaliação técnica do website.") + " Configuração, reputação e incidentes reportados são dimensões distintas. A análise não estabelece, por si só, causa, autoria ou compromisso atual.")
    add("Leitura do documento", "small")
    add("01 Conclusões e correlações  /  02 Perguntas essenciais  /  03 Prioridades  /  04 Contexto técnico  /  05 Cobertura e limites  /  06 Cronologia  /  07 Mapa de relações  /  08 Evidências e datas", "small")
    if latest and not current:
        note("SÍNTESE ANTERIOR DESATUALIZADA: as evidências, a cobertura ou a versão de análise mudaram. O texto anterior está conservado no fim do documento e não sustenta o resumo executivo atual.")

    section("01", "Conclusões e correlações", new_page=True)
    note("A confiança é qualitativa e expressa os limites da interpretação. Não é uma probabilidade calculada. Referências válidas permitem rastrear o texto; não garantem, por si só, a veracidade de uma alegação.")
    if analysis:
        add("Conclusões fundamentadas", "h2")
        for item in analysis["conclusions"]:
            add(JUDGEMENT[item["kind"]] + " | Confiança " + CONFIDENCE[item["confidence"]].lower(), "label")
            add(item["text"])
            refs(item["evidence_ids"])
            add("Limite: " + item["caveat"], "small")
        if not analysis["conclusions"]:
            add("As evidências não permitem formular conclusões sustentadas nesta recolha.")
        add("Cruzamento entre evidências", "h2")
        for item in analysis["correlations"]:
            add(CORRELATION[item["kind"]] + " | Confiança " + CONFIDENCE[item["confidence"]].lower(), "label")
            add(item["text"])
            refs(item["evidence_ids"])
            add("O que falta confirmar: " + item["caveat"], "small")
        if not analysis["correlations"]:
            add("Não foram propostas correlações sustentadas. A ausência de correlação documentada é preferível a ligar sinais sem fundamento.")
    elif current:
        note("Esta síntese usa o formato anterior. Pode ser consultada, mas ainda não inclui as seis respostas, correlações e prioridades estruturadas. Atualize o módulo IA para produzir a análise enriquecida.")
        legacy_report(current["report"])
    else:
        add("Sem conclusões produzidas por IA. Consulte a cobertura e as evidências. Configure o acesso ou atualize o módulo IA na aplicação para obter uma análise fundamentada; descarregar o PDF não faz novas consultas.")

    section("02", "As perguntas essenciais")
    answers = {answer["key"]: answer for answer in analysis["questions"]} if analysis else {}
    if not analysis:
        add("Sem respostas estruturadas atuais. Permanecem por avaliar: " + " / ".join(QUESTIONS.values()), "small")
    for number, (key, question) in enumerate(QUESTIONS.items() if analysis else [], 1):
        start = len(story)
        add(f"{number:02d}. " + question, "question")
        if key in answers:
            answer = answers[key]
            add(ASSESSMENT[answer["assessment"]] + " | Confiança " + CONFIDENCE[answer["confidence"]].lower(), "label")
            add(answer["answer"], "answer")
            refs(answer["evidence_ids"])
            add("Limite: " + answer["caveat"], "small")
        else:
            add("Sem resposta IA atual. Esta pergunta permanece por avaliar; a ausência de uma resposta não permite concluir segurança ou ausência de incidentes.", "answer")
        block = story[start:]
        del story[start:]
        story.append(KeepTogether(block))

    section("03", "Prioridades e próximos passos")
    add("Prioridades de acompanhamento e correção, proporcionais às evidências. P1: tratar primeiro; P2: curto prazo; P3: planeamento. Não medem a probabilidade de ataque.")
    if analysis:
        for item in sorted(analysis["actions"], key=lambda action: action["priority"]):
            add(item["priority"] + " / " + item["action"], "h2")
            add("Motivo: " + item["reason"])
            refs(item["evidence_ids"])
            add("Critério de conclusão: " + item["validation"])
        if not analysis["actions"]:
            add("Sem ações prioritárias sustentadas propostas nesta análise.")
    elif current:
        for item in current["report"].get("recommendations", []):
            add(item["text"])
            refs(item["evidence_ids"])
    else:
        add("Antes de decidir, rever a cobertura, ler as fontes originais e obter uma análise atual. Não foram geradas prioridades específicas para o alvo sem suporte suficiente.")

    section("04", "Contexto técnico")
    if technical:
        add("Postura de configuração: " + score, "h2")
        if technical_retained:
            note("RESULTADOS TÉCNICOS CONSERVADOS: a última tentativa não terminou com sucesso. Estas medições pertencem à recolha anterior; consultar as datas e o estado do módulo antes de as interpretar.")
        add(technical.get("summary", ""))
        note("Score académico de configuração. Não é uma certificação, não mede reputação e não comprova que uma falha tenha sido explorada.")
        technical_refs = [entry["id"] for entry in entries if entry.get("category") == "technical_posture"]
        refs(technical_refs)
        for finding in technical.get("findings", []):
            severity = {"critical": "Crítica", "high": "Elevada", "medium": "Moderada", "low": "Baixa", "info": "Informativa"}.get(finding.get("severity"), finding.get("severity", ""))
            add(finding["title"] + " | " + severity, "h2")
            add(finding["description"])
            add("Recomendação técnica: " + finding["recommendation"])
        if not technical.get("findings"):
            add("Sem findings nas regras executadas. Isto não comprova ausência de vulnerabilidades.")
    else:
        add("A análise técnica não foi executada ou não produziu resultados disponíveis. Não foi inferida configuração a partir de notícias ou alertas gerais.")
        note("Para incluir esta dimensão, criar uma investigação em modo Dossiê completo e confirmar que o website é próprio ou autorizado. Não são iniciadas verificações ao exportar.")
    if snapshot.get("message_analysis"):
        add("Sinais da mensagem", "h2")
        message = snapshot["message_analysis"]
        add(message.get("limitation", "Sinais linguísticos não confirmam phishing."))
        for signal in message.get("signals", []):
            add(signal["description"])

    section("05", "Cobertura, lacunas e método")
    rows = [[PROVIDERS.get(run["provider"], run["provider"]), STATUS.get(run["status"], run["status"]), str(run.get("results_count", 0)), date_label(run.get("observed_at"))] for run in snapshot.get("runs", [])]
    if rows:
        table(["MÓDULO", "ESTADO", "N.º", "CONSULTA"], rows, [145, 135, 35, content_width - 315])
    for run in snapshot.get("runs", []):
        if run["status"] != "demo":
            add(PROVIDERS.get(run["provider"], run["provider"]) + ": " + run.get("message", ""), "small")
    for item in snapshot.get("coverage_summary", {}).get("notes", []):
        add(item)
    add("Lacunas e limitações", "h2")
    gaps = (analysis.get("gaps", []) if analysis else []) + (current["report"].get("limitations", []) if current else [])
    for item in dict.fromkeys(gaps):
        add(item)
    add("Ausência de correspondências não comprova segurança. Um registo de exploração conhecida de uma CVE não comprova versão afetada ou ataque ao alvo. Publicação, incidente e consulta são datas distintas. Fontes ou conteúdos repetidos não equivalem a confirmação independente.")
    grouping = snapshot.get("incident_grouping")
    if grouping:
        add("Referências candidatas agrupadas por regras", "h2")
        add(grouping["limitation"], "small")
        for group in grouping.get("groups", []):
            add(group["note"])
            refs(group["evidence_ids"])
    add("Rastreabilidade da análise", "h2")
    add("As datas com hora são apresentadas em UTC. Datas de calendário são preservadas sem inferir uma hora de ocorrência.", "small")
    add("A exportação organiza um snapshot guardado; não faz consultas ao alvo, a fornecedores ou à IA. O texto recebido de fontes é tratado como dados não confiáveis. O sistema valida estrutura, identificadores e algumas regras conservadoras de confiança; a revisão semântica e a confirmação dos factos continuam necessárias.")
    if current:
        add("Origem do texto: " + current.get("model", "desconhecida") + " | Versão: " + current.get("prompt_version", "anterior") + " | Gerado: " + date_label(current.get("created_at")), "small")

    section("06", "Cronologia das evidências", new_page=True)
    add("Três datas independentes, mais recentes no topo. A publicação não substitui a data do incidente; a consulta indica apenas quando o resultado foi recolhido.")
    related = [entry for entry in entries if entry.get("category") != "kev_general"]
    if related:
        timeline = TimelineVisual(content_width, related, index)
        story.append(timeline)
        story.append(Spacer(1, 14))
        add("Leitura: ordem temporal com espaçamento uniforme, sem escala de duração. Até cinco datas por coluna e seis referências por data; as restantes e todas as datas desconhecidas estão no anexo. Clique em E# para consultar a evidência.", "small")
        if timeline.height <= 260:
            add("Volume de referências por módulo", "h2")
            story.append(ModuleVolumeVisual(content_width, related))
            add("Contagem de evidências atuais, não de incidentes ou de fontes independentes. Mais referências não significam maior risco nem maior confiança.", "small")
    else:
        note("Sem evidências atuais para representar. Não foram inventados eventos ou datas; resultados anteriores, quando existem, permanecem no anexo.")
    if previous:
        add(str(len(previous)) + " evidência(s) anterior(es) fora desta cronologia; consultar o anexo.", "small")

    related = [entry for entry in entries if entry.get("category") != "kev_general"]
    visual = graph_data(related)
    pages = balanced_pages(visual["entries"])
    for page_number, page_entries in enumerate(pages, 1):
        section("07", "Mapa de relações" + (" / " + str(page_number) + " de " + str(len(pages)) if len(pages) > 1 else ""), new_page=True)
        add("Mapa de proveniência: dossiê, módulos consultados e referências guardadas. As ligações representam recolha, não causalidade, confirmação independente ou um ataque ao alvo.")
        if page_entries:
            story.append(RelationVisual(content_width, target, page_entries, index))
            story.append(Spacer(1, 12))
            add(str(len(page_entries)) + " referências nesta página; " + str(len(visual["entries"])) + " de " + str(visual["total"]) + " no mapa completo. E# abre o anexo; títulos longos são abreviados apenas nesta vista. A cor descreve proveniência/incerteza, não gravidade.", "small")
        else:
            note("Sem evidências atuais para desenhar o mapa. A ausência de ligações não é uma conclusão de segurança.")
        if visual["omitted"]:
            add(str(visual["omitted"]) + " referências adicionais no anexo. O mapa seleciona até 24, por alternância de módulos, para preservar legibilidade.", "small")
        add("As correlações interpretativas, quando disponíveis e atuais, estão na secção 01 com confiança, ressalvas e referências. Resultados anteriores do anexo não são acrescentados silenciosamente ao mapa.", "small")

    general = [entry for entry in entries if entry.get("category") == "kev_general"]
    if general:
        add("Contexto global CISA KEV — sem associação demonstrada ao alvo", "h2")
        add("Estes alertas gerais ficam fora do mapa e da cronologia do alvo. Não demonstram produto em uso, versão afetada ou ataque.")
        for entry in general:
            add(entry["title"])
            refs([entry["id"]])

    section("08", "Anexo de evidências e datas", new_page=True)
    add("As referências [E#] remetem para este anexo. A numeração é a mesma da aplicação. Resultados anteriores estão identificados e não integram a contagem atual.")
    if not entries and not previous:
        add("Sem evidências disponíveis nesta recolha.")
    for entry in entries + previous:
        start = len(story)
        number = index[entry["id"]]
        story.append(Paragraph(f'<a name="evidence-E{number}"/>E{number} / ' + escape(entry["title"]), styles["h2"]))
        add(PROVIDERS.get(entry["provider"], entry["provider"]) + " | " + STATUS.get(entry.get("confirmation"), entry.get("confirmation", "Por verificar")), "label")
        if entry.get("review"):
            review = entry["review"]
            add("Revisão humana: " + {"unreviewed": "Por rever", "reviewed": "Revista", "contested": "Contestada"}.get(review["status"], review["status"]) + " | Autor: " + review["author"] + " | " + date_label(review["created_at"]), "small")
            add("Identidade: " + {"unverified": "Por verificar", "matches": "Correspondência apreciada pelo autor", "does_not_match": "Não corresponde", "uncertain": "Incerta"}.get(review["identity_status"], review["identity_status"]), "small")
            add(review["note"], "small")
            add("Anotação humana, não confirmação independente de intrusão. " + ("A evidência mudou desde esta revisão." if not review["is_current"] else "") + " Histórico completo disponível na aplicação.", "small")
        meta = entry.get("meta", {})
        if meta.get("provider_queried_at"):
            add("Consulta original ao fornecedor: " + date_label(meta["provider_queried_at"]) + ". O resultado pode ter sido reutilizado da cache.", "small")
        if meta.get("not_returned_in_latest_success"):
            note("RECOLHA ANTERIOR: não devolvida na última consulta concluída; não integra os resultados atuais nem prova desaparecimento da ameaça.")
        elif meta.get("retained_from_earlier_attempt"):
            note("RESULTADO ANTERIOR CONSERVADO: a última tentativa desta fonte falhou ou ficou incompleta.")
        if meta.get("relevance") == "needs_review" or meta.get("matched_by") == "organization_name":
            add("Relação com a organização por verificar; pode tratar-se de outra entidade.", "small")
        if entry.get("category") in {"kev_general", "kev_candidate"}:
            add("Alerta geral sem associação ao alvo." if entry.get("category") == "kev_general" else "Candidato por produto; versão afetada e condições não confirmadas.", "small")
        add(entry["description"])
        table(["PUBLICAÇÃO", "INCIDENTE", "CONSULTA"], [[date_label(entry.get("published_at")), date_label(entry.get("event_at")), date_label(entry.get("observed_at"))]], [content_width / 3] * 3)
        if meta.get("catalog_added_at"):
            add("Entrada no catálogo KEV: " + date_label(meta["catalog_added_at"]) + ". Não é a data do último ataque.", "small")
        source = safe_source(entry.get("source_url", ""))
        if source:
            story.append(Paragraph('<link href="' + escape(source, quote=True) + '" color="#147b73">' + escape(source) + '</link>', styles["url"]))
        else:
            add("Sem ligação externa validada.", "small")
        block = story[start:]
        del story[start:]
        story.append(KeepTogether(block))
    if latest and not current:
        section("ARQUIVO", "Síntese anterior, para contexto", new_page=True)
        note("SÍNTESE ANTERIOR DESATUALIZADA. Não deve ser usada como conclusão da recolha atual.")
        legacy_report(latest["report"])
        old_analysis = latest["report"].get("intelligence")
        if old_analysis:
            add("Conclusões e correlações anteriores", "h2")
            for item in old_analysis["conclusions"] + old_analysis["correlations"]:
                add(item["text"])
                refs(item["evidence_ids"])
                add("Limite: " + item["caveat"], "small")
            for answer in old_analysis["questions"]:
                add(QUESTIONS[answer["key"]], "h2")
                add(answer["answer"])
                refs(answer["evidence_ids"])
            for action in old_analysis["actions"]:
                add(action["priority"] + " / " + action["action"], "h2")
                add(action["reason"])
                refs(action["evidence_ids"])
                add("Critério: " + action["validation"])
        for limit in latest["report"].get("limitations", []):
            add(limit, "small")
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=48, rightMargin=48, topMargin=98, bottomMargin=66, title="WebSecAI - Relatório de inteligência - " + str(target), author="WebSecAI", subject="Análise com referências, cobertura e limites")
    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    return buffer.getvalue()
