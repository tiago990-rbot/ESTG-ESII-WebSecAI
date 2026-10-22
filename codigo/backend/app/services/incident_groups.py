"""Conservative, reproducible candidate groups. No inferred dates or extra requests."""
from collections import defaultdict
from datetime import datetime
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


def event_kind(entry):
    text = (entry.get("title", "") + " " + entry.get("description", "")).lower()
    if "ransomware" in text:
        return "ransomware"
    if "phishing" in text:
        return "phishing"
    if re.search(r"breach|fuga de dados|data leak", text):
        return "data_exposure"
    return "unknown"


def known_date(raw):
    if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def candidate_groups(evidence, domain):
    buckets = defaultdict(list)
    references = [e for e in evidence if e.get("category") in {"incident_report", "public_reference", "exposure"}]
    for entry in references:
        meta = entry.get("meta", {})
        if meta.get("relevance") == "needs_review" or meta.get("matched_by") == "organization_name":
            continue
        date = known_date(entry.get("event_at"))
        kind = event_kind(entry)
        scope = meta.get("queried_domain") or domain
        if date and kind != "unknown" and scope:
            # Same day/type/domain is a candidate, never proof of one shared incident.
            key = ("shared_event_date_and_type", scope, date, kind)
        else:
            try:
                url = urlsplit(entry.get("source_url", ""))
                if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                    continue
                canonical = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, ""))
            except ValueError:
                continue
            # Keep the query: ?id=1 and ?id=2 may be different articles.
            key = ("same_source_url", canonical)
        buckets[key].append(entry)
    groups = []
    for key, entries in buckets.items():
        if len(entries) < 2:
            continue
        source_urls = list(dict.fromkeys(e.get("source_url", "") for e in entries if e.get("source_url")))
        groups.append({"id": hashlib.sha256(repr(key).encode()).hexdigest()[:16],
                       "reason": key[0], "status": "candidate_requires_review",
                       "event_at": key[2] if key[0] == "shared_event_date_and_type" else None,
                       "kind": key[3] if key[0] == "shared_event_date_and_type" else "unknown",
                       "evidence_ids": [e["id"] for e in entries], "source_urls": source_urls,
                       "note": "Referências agrupadas por data estruturada, tipo e alvo; podem descrever incidentes diferentes." if key[0] == "shared_event_date_and_type" else "Referências com a mesma ligação de origem; não representam fontes independentes."})
    grouped = {eid for group in groups for eid in group["evidence_ids"]}
    return {"origin": "local_rules", "groups": groups,
            "ungrouped_evidence_ids": [e["id"] for e in references if e["id"] not in grouped],
            "limitation": "Datas de publicação e consulta não são usadas como datas de incidente. Referências sem critérios suficientes permanecem separadas."}
