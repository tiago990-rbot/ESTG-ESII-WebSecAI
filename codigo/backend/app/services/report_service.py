from io import BytesIO
from html import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def safe_paragraph(text, style):
    return Paragraph(escape(str(text)), style)


def generate_scan_pdf(scan, findings) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Relatorio WebSec Check {scan.domain}")
    styles = getSampleStyleSheet()
    story = []

    story.append(safe_paragraph("WebSec Check — Relatório de Análise", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(safe_paragraph(f"URL: {scan.url}", styles["Normal"]))
    story.append(safe_paragraph(f"Domínio: {scan.domain}", styles["Normal"]))
    story.append(safe_paragraph(f"Data: {scan.created_at}", styles["Normal"]))
    story.append(safe_paragraph(f"Score: {scan.score}/100", styles["Normal"]))
    story.append(safe_paragraph(f"Nível de risco: {scan.risk_level}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(safe_paragraph("Resumo", styles["Heading2"]))
    story.append(safe_paragraph(scan.summary or "Sem resumo.", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(safe_paragraph("Findings e recomendações", styles["Heading2"]))

    for finding in findings:
        story.append(safe_paragraph(f"{finding.title} — {finding.severity}", styles["Heading3"]))
        story.append(safe_paragraph(f"Categoria: {finding.category}", styles["Normal"]))
        story.append(safe_paragraph(finding.description, styles["Normal"]))
        story.append(safe_paragraph(f"Recomendação: {finding.recommendation}", styles["Normal"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
