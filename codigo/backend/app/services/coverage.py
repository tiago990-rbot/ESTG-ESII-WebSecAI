"""Coverage facts derived locally, without asking a model to invent citations."""


def target_evidence(evidence):
    return [entry for entry in evidence
            if entry.get("category") not in {"kev_general", "kev_candidate"}
            and entry.get("meta", {}).get("relevance") != "needs_review"
            and entry.get("meta", {}).get("matched_by") != "organization_name"]


def summarize_coverage(evidence, runs):
    direct = target_evidence(evidence)
    missing = [run["provider"] for run in runs if run["status"] == "not_configured"]
    empty = [run["provider"] for run in runs if run["status"] == "no_results" and run["provider"] != "ai"]
    failed = [run["provider"] for run in runs if run["status"] in {"error", "partial", "rate_limited", "access_denied", "interrupted"}]
    notes = []
    if not direct:
        notes.append("Não há evidências atuais diretamente associadas ao alvo nesta recolha. Alertas gerais e referências por verificar continuam disponíveis para consulta.")
    if empty:
        notes.append("Uma ou mais fontes não devolveram correspondências para as consultas efetuadas. Isto não prova segurança nem ausência de incidentes.")
    if missing:
        notes.append("Existem fontes sem acesso configurado; a cobertura dessas fontes não foi avaliada.")
    if failed:
        notes.append("Uma ou mais consultas falharam ou ficaram incompletas. Os resultados disponíveis não representam uma pesquisa exaustiva.")
    if not notes:
        notes.append("A cobertura corresponde apenas às fontes e consultas indicadas. As referências exigem validação da relação com o alvo e do seu conteúdo.")
    return {"origin": "local_rules", "has_target_evidence": bool(direct), "target_evidence_count": len(direct),
            "unconfigured_providers": missing, "no_match_providers": empty, "incomplete_providers": failed, "notes": notes}
