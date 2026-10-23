"""Report contract and provenance checks. No model calls or network access here."""
from urllib.parse import urlsplit, urlunsplit

QUESTIONS = {
    "history": "Há referências a incidentes anteriores?",
    "identity": "As referências dizem respeito à mesma organização?",
    "current_signals": "Existem sinais atuais de ameaça?",
    "technical": "Que fragilidades técnicas foram observadas?",
    "correlation": "O histórico e a configuração atual estão relacionados?",
    "priorities": "O que deve ser feito primeiro?",
}
CONFIDENCE = {"low": "Baixa", "medium": "Moderada", "high": "Elevada"}
JUDGEMENT = {"observation": "Observação", "inference": "Inferência", "hypothesis": "Hipótese"}
CORRELATION = {"contextual_link": "Contexto em comum", "possible_link": "Relação possível", "contradiction": "Divergência entre referências"}
ASSESSMENT = {"supported": "Resposta fundamentada", "hypothesis": "Hipótese", "insufficient": "Informação insuficiente"}

def uncertain(entry):
    meta = entry.get("meta", {})
    return (entry.get("confirmation") in {"allegation", "unverified"}
            or entry.get("category") in {"kev_general", "kev_candidate"}
            or meta.get("matched_by") == "organization_name"
            or meta.get("relevance") in {"needs_review", "general_alert_not_associated_with_target", "product_candidate_version_unconfirmed"}
            or meta.get("retained_from_earlier_attempt"))

def safe_source(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password:
            return None
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
    except (ValueError, TypeError):
        return None

def validate_intelligence(analysis, evidence):
    """Validate references and conservative confidence, not semantic truth of prose."""
    index = {entry["id"]: entry for entry in evidence}
    if {answer.key for answer in analysis.questions} != set(QUESTIONS):
        raise ValueError("O relatório deve responder às seis perguntas distintas.")
    claims = analysis.conclusions + analysis.correlations + analysis.questions + analysis.actions
    for claim in claims:
        refs = claim.evidence_ids
        if len(set(refs)) != len(refs) or any(ref not in index for ref in refs):
            raise ValueError("Referências de inteligência inválidas ou repetidas.")
        confidence = getattr(claim, "confidence", None)
        if confidence == "high" and (getattr(claim, "kind", None) in {"hypothesis", "possible_link"}
                                     or getattr(claim, "assessment", None) in {"hypothesis", "insufficient"}
                                     or not refs or any(uncertain(index[ref]) for ref in refs)):
            raise ValueError("Confiança incompatível com a incerteza das referências.")
    for answer in analysis.questions:
        if not answer.evidence_ids and answer.assessment != "insufficient":
            raise ValueError("Uma resposta sem evidências tem de indicar informação insuficiente.")
        if answer.assessment == "insufficient" and answer.confidence != "low":
            raise ValueError("Informação insuficiente exige confiança baixa.")
    for correlation in analysis.correlations:
        sources = [safe_source(index[ref].get("source_url", "")) for ref in correlation.evidence_ids]
        providers = {index[ref].get("provider") for ref in correlation.evidence_ids}
        if correlation.confidence == "high" and (len(providers) < 2 or (all(sources) and len(set(sources)) < 2)):
            raise ValueError("Referências repetidas ou do mesmo módulo não justificam correlação de confiança elevada.")

def select_evidence(evidence, limit=24):
    """Round-robin prevents technical findings from crowding out public references."""
    buckets = {}
    for entry in evidence:
        if entry.get("meta", {}).get("not_returned_in_latest_success"):
            continue
        buckets.setdefault(entry.get("provider", "unknown"), []).append(entry)
    severity = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    if "technical" in buckets:
        buckets["technical"].sort(key=lambda entry: -1 if entry.get("category") == "technical_posture" else severity.get(entry.get("meta", {}).get("severity"), 5))
    chosen = []
    while len(chosen) < limit and any(buckets.values()):
        for name in buckets:
            if buckets[name] and len(chosen) < limit:
                chosen.append(buckets[name].pop(0))
    return chosen

def technical_records(technical, item):
    """Only safe structured measurements/findings, never response headers or cookies."""
    entries = [item("technical_posture", "Resumo da postura técnica", "Score académico: " + str(technical.get("score", "?")) + "/100. " + technical.get("summary", "") + " O score não mede reputação nem confirma intrusão.", score=technical.get("score"), scope="authorized_technical_checks")]
    for finding in technical.get("findings", [])[:15]:
        entries.append(item("technical", finding["title"], finding["description"] + " Recomendação: " + finding["recommendation"], severity=finding["severity"], scope="authorized_technical_checks"))
    return entries
