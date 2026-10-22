from html import escape
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def investigation_pdf(snapshot: dict) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = []
    def add(text, style="Normal"):
        story.append(Paragraph(escape(str(text)), styles[style]))
        story.append(Spacer(1, 6))
    add("WebSecAI — Investigação", "Title")
    if snapshot["is_demo"]:
        add("DEMONSTRAÇÃO: dados fictícios; não representam incidentes reais.", "Heading2")
    add(snapshot["target"], "Heading1")
    add("Data: " + str(snapshot["created_at"]) + " | Estado: " + snapshot["status"])
    add("Cobertura das fontes", "Heading2")
    for run in snapshot["runs"]:
        add(run["provider"] + " — " + run["status"] + ": " + run["message"])
    if snapshot.get("coverage_summary"):
        add("Interpretação da cobertura — regras locais, sem geração IA", "Heading2")
        for note in snapshot["coverage_summary"]["notes"]:
            add(note)
    if snapshot["reports"]:
        report = snapshot["reports"][-1]
        add("Síntese — " + report["model"], "Heading2")
        if not report.get("is_current", False):
            add("SÍNTESE ANTERIOR DESATUALIZADA: as evidências ou a cobertura mudaram. O texto está conservado para consulta e requer atualização.")
        add(report["report"]["summary"])
        for group in ("observations", "recommendations"):
            for claim in report["report"][group]:
                add(claim["text"] + " [Evidências: " + ", ".join(claim["evidence_ids"]) + "]")
        for limit in report["report"]["limitations"]:
            add("Limitação: " + limit)
    grouping = snapshot.get("incident_grouping")
    if grouping:
        add("Agrupamento de referências candidatas — regras locais", "Heading2")
        add(grouping["limitation"])
        for group in grouping["groups"]:
            add(group["note"])
            add("Data do incidente: " + str(group["event_at"] or "desconhecida") + " | Evidências: " + ", ".join(group["evidence_ids"]))
    add("Evidências e referências", "Heading2")
    for e in snapshot["evidence"] + snapshot.get("previous_evidence", []):
        if e.get("meta", {}).get("not_returned_in_latest_success"):
            add("RECOLHA ANTERIOR: não devolvida na última consulta concluída; não integra os resultados atuais.")
        elif e.get("meta", {}).get("retained_from_earlier_attempt"):
            add("RESULTADO ANTERIOR CONSERVADO: a última tentativa desta fonte falhou ou ficou incompleta.")
        add(e["title"], "Heading3")
        add("ID: " + e["id"] + " | Fonte: " + e["provider"] + " | Estado: " + e["confirmation"])
        add(e["description"])
        add("Publicação: " + str(e["published_at"] or "desconhecida") + " | Incidente: " + str(e["event_at"] or "desconhecida") + " | Consulta: " + str(e["observed_at"]))
        if e["source_url"]:
            add(e["source_url"])
    add("As fontes consultadas têm cobertura limitada. Ausência de resultados não comprova segurança. Exploração conhecida de uma falha não comprova ataque ao alvo.")
    SimpleDocTemplate(buffer, pagesize=A4, title="WebSecAI — Investigação").build(story)
    return buffer.getvalue()
