def _finding(title: str, severity: str, category: str, description: str, recommendation: str) -> dict:
    return {
        "title": title,
        "severity": severity,
        "category": category,
        "description": description,
        "recommendation": recommendation,
    }


def calculate_score(details: dict) -> dict:
    """Calcula um score académico de postura de segurança.

    Importante: este score é um indicador de boas práticas públicas observáveis.
    Não é uma certificação de segurança e não prova, sozinho, a existência de uma vulnerabilidade explorável.
    """
    score = 100
    findings: list[dict] = []

    dns = details.get("dns", {})
    tls = details.get("tls", {})
    http = details.get("http", {})
    headers = http.get("headers", {})
    cookies = http.get("cookies", {})

    if not dns.get("dns_ok"):
        score -= 30
        findings.append(_finding(
            "Falha na resolução DNS",
            "high",
            "dns",
            "O domínio não resolveu corretamente no momento da análise.",
            "Verificar configuração DNS, disponibilidade do domínio e possíveis bloqueios temporários.",
        ))

    if not tls.get("https_supported"):
        score -= 30
        findings.append(_finding(
            "HTTPS não disponível",
            "critical",
            "tls",
            "Não foi possível estabelecer ligação HTTPS ao domínio analisado.",
            "Ativar HTTPS com certificado válido e cadeia de certificação correta.",
        ))
    elif not tls.get("tls_ok"):
        score -= 20
        findings.append(_finding(
            "Problema no certificado TLS",
            "high",
            "tls",
            "Foi detetado um problema na validação TLS/certificado.",
            "Verificar validade, cadeia de certificação e correspondência do hostname.",
        ))

    if tls.get("expired"):
        score -= 25
        findings.append(_finding(
            "Certificado expirado",
            "critical",
            "tls",
            "O certificado digital aparenta estar expirado.",
            "Renovar o certificado imediatamente.",
        ))
    elif tls.get("days_remaining") is not None and tls.get("days_remaining") < 30:
        score -= 10
        findings.append(_finding(
            "Certificado próximo da expiração",
            "medium",
            "tls",
            "O certificado expira em menos de 30 dias.",
            "Planear renovação do certificado antes da data de expiração.",
        ))

    if http.get("https_ok") and not http.get("http_to_https_redirect"):
        score -= 8
        findings.append(_finding(
            "Redirecionamento HTTP para HTTPS não confirmado",
            "medium",
            "http",
            "O acesso por HTTP não redirecionou claramente para HTTPS durante a análise.",
            "Configurar redirecionamento permanente de HTTP para HTTPS quando aplicável.",
        ))

    header_penalties = [
        ("hsts", "Strict-Transport-Security não detetado", 10, "high", "Ativar HSTS para forçar o uso de HTTPS nos browsers."),
        ("csp", "Content-Security-Policy não detetada", 7, "medium", "Definir uma política CSP adequada ou documentar proteção equivalente por rota/camada."),
        ("x_content_type_options", "X-Content-Type-Options não detetado", 5, "medium", "Adicionar X-Content-Type-Options: nosniff."),
        ("referrer_policy", "Referrer-Policy não detetada", 4, "low", "Definir uma Referrer-Policy adequada."),
        ("permissions_policy", "Permissions-Policy não detetada", 4, "low", "Limitar permissões do browser com Permissions-Policy quando fizer sentido."),
        ("x_frame_options", "X-Frame-Options não detetado", 4, "medium", "Adicionar X-Frame-Options ou usar frame-ancestors na CSP quando aplicável."),
    ]
    for key, title, penalty, severity, recommendation in header_penalties:
        if headers.get(key) is False:
            score -= penalty
            readable = title.replace(" não detetado", "").replace(" não detetada", "")
            findings.append(_finding(
                title,
                severity,
                "headers",
                f"O header {readable} não foi encontrado na resposta HTTP analisada. Isto indica uma boa prática não confirmada, não uma prova automática de vulnerabilidade.",
                recommendation,
            ))

    if headers.get("server_header"):
        score -= 2
        findings.append(_finding(
            "Header Server exposto",
            "low",
            "headers",
            "O servidor expõe informação sobre a tecnologia utilizada.",
            "Reduzir informação exposta nos headers quando possível.",
        ))
    if headers.get("x_powered_by"):
        score -= 3
        findings.append(_finding(
            "Header X-Powered-By exposto",
            "low",
            "headers",
            "A aplicação expõe tecnologia/framework através do header X-Powered-By.",
            "Remover ou ocultar este header quando possível.",
        ))

    if cookies.get("has_cookies"):
        if cookies.get("all_secure") is False:
            score -= 8
            findings.append(_finding(
                "Cookies sem atributo Secure",
                "medium",
                "cookies",
                "Nem todos os cookies recebidos nesta resposta usam o atributo Secure.",
                "Configurar cookies sensíveis com Secure.",
            ))
        if cookies.get("all_httponly") is False:
            score -= 8
            findings.append(_finding(
                "Cookies sem atributo HttpOnly",
                "medium",
                "cookies",
                "Nem todos os cookies recebidos nesta resposta usam o atributo HttpOnly.",
                "Configurar cookies sensíveis com HttpOnly quando não precisarem de acesso por JavaScript.",
            ))
        if cookies.get("all_samesite") is False:
            score -= 5
            findings.append(_finding(
                "Cookies sem atributo SameSite",
                "low",
                "cookies",
                "Nem todos os cookies recebidos nesta resposta definem SameSite.",
                "Definir SameSite=Lax ou Strict quando adequado.",
            ))

    score = max(0, min(100, score))
    if score >= 85:
        risk_level = "good"
        summary = "O website apresenta uma postura de segurança boa nas verificações públicas efetuadas."
    elif score >= 60:
        risk_level = "medium"
        summary = "O website apresenta uma postura de segurança média, com algumas boas práticas não confirmadas."
    else:
        risk_level = "weak"
        summary = "O website apresenta uma postura de segurança fraca ou incompleta nas verificações públicas efetuadas."

    if not findings:
        findings.append(_finding(
            "Nenhum problema relevante detetado",
            "info",
            "general",
            "A análise não identificou problemas relevantes nas verificações implementadas.",
            "Manter boas práticas e monitorizar periodicamente.",
        ))

    return {"score": score, "risk_level": risk_level, "summary": summary, "findings": findings}
