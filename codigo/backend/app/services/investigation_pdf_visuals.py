"""Bounded vector views of saved evidence; no network, model or inferred dates."""
from collections import defaultdict, deque
from datetime import datetime, timezone
import re
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable

INK = colors.HexColor("#112b38")
TEAL = colors.HexColor("#147b73")
MUTED = colors.HexColor("#556c77")
PALE = colors.HexColor("#eff6f5")
LINE = colors.HexColor("#d7e2e5")
AMBER = colors.HexColor("#805822")
PROVIDERS = {"osint": "Pesquisa pública", "technical": "Verificações técnicas", "urlhaus": "URLhaus", "phishtank": "PhishTank", "kev": "CISA KEV", "exposure": "Exposição de dados", "ai": "Síntese IA", "message": "Regras da mensagem"}
DATE_FIELDS = (("published_at", "Publicação"), ("event_at", "Incidente"), ("observed_at", "Consulta"))


def parsed_date(value):
    """Preserve calendar-only precision; normalize actual timestamps to UTC."""
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T)", value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if len(value) == 10:
            return parsed.replace(tzinfo=timezone.utc), parsed.strftime("%d/%m/%Y")
        if "T" not in value:
            return None
        parsed = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
        return parsed, parsed.strftime("%d/%m/%Y %H:%M UTC")
    except (ValueError, TypeError):
        return None


def timeline_data(entries, index, limit=5):
    lanes = []
    for field, label in DATE_FIELDS:
        groups = {}
        unknown = []
        for entry in entries:
            number = index[entry["id"]]
            parsed = parsed_date(entry.get(field))
            if parsed is None:
                unknown.append(number)
                continue
            moment, display = parsed
            # Separate labels retain day-only precision versus timestamp precision.
            group = groups.setdefault(display, {"label": display, "moment": moment, "numbers": []})
            group["numbers"].append(number)
        ordered = sorted(groups.values(), key=lambda group: (group["moment"], group["label"]), reverse=True)
        shown = ordered[:limit]
        lanes.append({"field": field, "label": label, "groups": shown, "dated": len(entries) - len(unknown), "unknown": unknown, "omitted_groups": len(ordered) - len(shown)})
    return lanes


def relation(entry):
    meta = entry.get("meta") or {}
    if meta.get("retained_from_earlier_attempt") or meta.get("not_returned_in_latest_success"):
        return "Resultado anterior", True
    if meta.get("relevance") == "general_alert_not_associated_with_target" or entry.get("category") == "kev_general":
        return "Alerta geral", True
    if meta.get("matched_by") == "organization_name" or meta.get("relevance") == "needs_review":
        return "Relação por verificar", True
    if entry.get("category") == "kev_candidate" or meta.get("relevance") == "product_candidate_version_unconfirmed":
        return "Candidato por produto", True
    if entry.get("provider") == "technical":
        return "Resultado técnico", False
    if entry.get("confirmation") == "allegation":
        return "Alegação", True
    if entry.get("confirmation") == "unverified":
        return "Conteúdo por verificar", True
    return "Referência recolhida", False


def balanced_pages(entries, maximum=12):
    """Preserve order; avoid almost empty final map pages."""
    if maximum < 1:
        raise ValueError("A capacidade da página tem de ser positiva.")
    count = max(1, (len(entries) + maximum - 1) // maximum)
    size, extra = divmod(len(entries), count)
    pages, start = [], 0
    for index in range(count):
        end = start + size + (index < extra)
        pages.append(entries[start:end])
        start = end
    return pages


def graph_data(entries, limit=24):
    """Balanced collection view. Edges do not assert association or causality."""
    buckets = defaultdict(deque)
    seen = set()
    for entry in entries:
        if entry["id"] not in seen:
            buckets[entry["provider"]].append(entry)
            seen.add(entry["id"])
    selected = []
    while len(selected) < limit and any(buckets.values()):
        for bucket in buckets.values():
            if bucket and len(selected) < limit:
                selected.append(bucket.popleft())
    selected.sort(key=lambda entry: entry["provider"])
    return {"entries": selected, "total": len(seen), "omitted": len(seen) - len(selected), "edges": [{"provider": entry["provider"], "evidence_id": entry["id"], "kind": "collected_by"} for entry in selected]}


def fitted(text, width, size=8, font="Helvetica"):
    text = " ".join(str(text).split())
    if stringWidth(text, font, size) <= width:
        return text
    while text and stringWidth(text + "...", font, size) > width:
        text = text[:-1]
    return text + "..."


def text_line(canvas, x, y, text, width, size=8, color=INK, bold=False):
    font = "Helvetica-Bold" if bold else "Helvetica"
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    canvas.drawString(x, y, fitted(text, width, size, font))


def link_number(canvas, x, y, number, width=29):
    text_line(canvas, x, y, "E" + str(number), width, 7.5, TEAL, True)
    canvas.linkRect("E" + str(number), "evidence-E" + str(number), (x, y - 2, x + width - 2, y + 9), relative=1, thickness=0)


class TimelineVisual(Flowable):
    def __init__(self, width, entries, index):
        super().__init__()
        self.lanes = timeline_data(entries, index)
        self.width = width
        self.height = max(230, 164 + 52 * max((len(lane["groups"]) for lane in self.lanes), default=0))

    def draw(self):
        c = self.canv
        c.saveState()
        gap = 12
        lane_width = (self.width - 2 * gap) / 3
        for position, lane in enumerate(self.lanes):
            x = position * (lane_width + gap)
            c.setFillColor(PALE)
            c.roundRect(x, 0, lane_width, self.height, 7, stroke=0, fill=1)
            text_line(c, x + 12, self.height - 24, lane["label"].upper(), lane_width - 24, 8.5, TEAL, True)
            text_line(c, x + 12, self.height - 41, str(lane["dated"]) + " com data", lane_width - 24, 8, MUTED)
            c.setStrokeColor(LINE)
            c.setLineWidth(1.4)
            c.line(x + 17, 93, x + 17, self.height - 65)
            if not lane["groups"]:
                text_line(c, x + 30, self.height - 81, "Sem datas disponíveis", lane_width - 40, 7.5, MUTED)
                text_line(c, x + 30, self.height - 96, "Não são inferidas datas.", lane_width - 40, 7.5, MUTED)
            for i, group in enumerate(lane["groups"]):
                y = self.height - 74 - i * 52
                c.setFillColor(TEAL)
                c.circle(x + 17, y, 3.3, stroke=0, fill=1)
                # Split actual timestamp into two lines; no synthetic time for day-only data.
                label = group["label"]
                text_line(c, x + 29, y + 1, label[:10], 58, 8, INK, True)
                text_line(c, x + 90, y + 1, str(len(group["numbers"])) + " ref.", lane_width - 100, 6.5, MUTED)
                if len(label) > 10:
                    text_line(c, x + 29, y - 10, label[11:], lane_width - 40, 7, MUTED)
                numbers = group["numbers"][:6]
                ref_y = y - (23 if len(label) > 10 else 14)
                for j, number in enumerate(numbers):
                    link_number(c, x + 29 + (j % 3) * 32, ref_y - (j // 3) * 12, number, 31)
            if lane["omitted_groups"]:
                text_line(c, x + 12, 71, "+ " + str(lane["omitted_groups"]) + " datas no anexo", lane_width - 24, 7.5, AMBER)
            c.setStrokeColor(LINE)
            c.line(x + 12, 60, x + lane_width - 12, 60)
            text_line(c, x + 12, 43, str(len(lane["unknown"])) + " sem data válida", lane_width - 24, 7.5, AMBER, True)
            unknown = ", ".join("E" + str(n) for n in lane["unknown"])
            text_line(c, x + 12, 26, unknown or "Todas as datas disponíveis", lane_width - 24, 7, MUTED)
            if unknown and stringWidth(unknown, "Helvetica", 7) > lane_width - 24:
                text_line(c, x + 12, 13, "Lista integral no anexo", lane_width - 24, 6.5, MUTED)
        c.restoreState()


class ModuleVolumeVisual(Flowable):
    """Counts of references, never a severity, risk or independent-source score."""
    def __init__(self, width, entries):
        super().__init__()
        counts = defaultdict(int)
        for entry in entries:
            counts[entry["provider"]] += 1
        rows = sorted(counts.items(), key=lambda row: (-row[1], row[0]))
        self.rows = [(PROVIDERS.get(provider, provider), count) for provider, count in rows[:5]]
        if len(rows) > 5:
            self.rows.append(("Outros módulos", sum(count for _, count in rows[5:])))
        self.width, self.height = width, len(self.rows) * 22 + 10

    def draw(self):
        c = self.canv
        c.saveState()
        maximum = max((count for _, count in self.rows), default=1)
        bar_x, bar_width = 145, self.width - 179
        for i, (label, count) in enumerate(self.rows):
            y = self.height - 19 - i * 22
            text_line(c, 0, y, label, 137, 8, MUTED)
            c.setFillColor(PALE)
            c.roundRect(bar_x, y - 1, bar_width, 9, 3, fill=1, stroke=0)
            c.setFillColor(TEAL)
            c.roundRect(bar_x, y - 1, bar_width * count / maximum, 9, 3, fill=1, stroke=0)
            text_line(c, self.width - 25, y, str(count), 25, 8, INK, True)
        c.restoreState()


class RelationVisual(Flowable):
    def __init__(self, width, target, entries, index):
        super().__init__()
        self.width, self.height = width, 450
        self.target, self.entries, self.index = target, entries, index

    def draw(self):
        c = self.canv
        c.saveState()
        module_x, evidence_x = 150, 292
        module_width, evidence_width = 111, self.width - evidence_x
        for x, label, max_width in [(0, "DOSSIÊ", 120), (module_x, "MÓDULO CONSULTADO", 132), (evidence_x, "EVIDÊNCIA GUARDADA", evidence_width)]:
            text_line(c, x, 436, label, max_width, 7.2, TEAL, True)
        n = len(self.entries)
        step = min(47, 414 / max(n, 1))
        center = 221
        top = center + (n - 1) * step / 2
        positions = [(entry, top - i * step) for i, entry in enumerate(self.entries)]
        groups = defaultdict(list)
        for entry, y in positions:
            groups[entry["provider"]].append(y)
        c.setStrokeColor(LINE)
        c.setLineWidth(.9)
        # The first edge only describes the investigation's collection scope.
        for provider, ys in groups.items():
            y = sum(ys) / len(ys)
            path = c.beginPath()
            path.moveTo(117, center)
            path.curveTo(132, center, 132, y, module_x, y)
            c.drawPath(path)
        for entry, y in positions:
            module_y = sum(groups[entry["provider"]]) / len(groups[entry["provider"]])
            label, uncertain = relation(entry)
            c.setStrokeColor(AMBER if uncertain else LINE)
            c.setDash(3, 2) if uncertain else c.setDash()
            path = c.beginPath()
            path.moveTo(module_x + module_width, module_y)
            path.curveTo(275, module_y, 275, y, evidence_x, y)
            c.drawPath(path)
            c.setDash()
        c.setFillColor(INK)
        c.roundRect(0, center - 32, 117, 64, 6, fill=1, stroke=0)
        text_line(c, 9, center + 13, "ÂMBITO PESQUISADO", 99, 6.7, colors.white, True)
        text_line(c, 9, center - 4, self.target, 99, 7.6, colors.white, True)
        text_line(c, 9, center - 20, "Não confirma associação", 99, 6.3, colors.white)
        for provider, ys in groups.items():
            y = sum(ys) / len(ys)
            c.setFillColor(PALE)
            c.roundRect(module_x, y - 15, module_width, 30, 5, fill=1, stroke=0)
            text_line(c, module_x + 8, y + 3, PROVIDERS.get(provider, provider), module_width - 16, 7.4, INK, True)
            text_line(c, module_x + 8, y - 11, str(len(ys)) + " nesta vista", module_width - 16, 7, MUTED)
        for entry, y in positions:
            label, uncertain = relation(entry)
            c.setFillColor(PALE if not uncertain else colors.HexColor("#faf4e9"))
            c.roundRect(evidence_x, y - 16, evidence_width, 33, 4, fill=1, stroke=0)
            number = self.index[entry["id"]]
            link_number(c, evidence_x + 7, y + 4, number)
            text_line(c, evidence_x + 39, y + 4, entry.get("title", ""), evidence_width - 46, 7.4, INK, True)
            text_line(c, evidence_x + 39, y - 9, label, evidence_width - 46, 6.8, AMBER if uncertain else MUTED)
        c.setStrokeColor(LINE)
        c.setDash()
        c.line(0, 8, 22, 8)
        text_line(c, 28, 5, "Origem / recolha", 110, 7.2, MUTED)
        c.setStrokeColor(AMBER)
        c.setDash(3, 2)
        c.line(153, 8, 175, 8)
        c.setDash()
        text_line(c, 181, 5, "Relação incerta, geral ou resultado anterior", self.width - 181, 7.2, MUTED)
        c.restoreState()
