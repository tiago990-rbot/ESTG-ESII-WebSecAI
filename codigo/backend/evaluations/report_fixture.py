"""Reproducible fictional document preview. Never presented as model output."""
from app.services.demo_report import demo_analysis
from app.services.ai_service import validated_report

def snapshot():
    date = "2026-10-23T10:00:00+00:00"
    def entry(id, provider, category, title, description, **extra):
        return {"id": id, "provider": provider, "category": category, "title": title, "description": description, "source_url": "", "confirmation": "unverified", "published_at": None, "event_at": None, "observed_at": date, "meta": {"demo": True}, **extra}
    evidence = [
        entry("demo-news", "osint", "incident_report", "Exemplo didático: incidente reportado", "Notícia fictícia para demonstrar a cronologia. Não descreve um incidente real.", published_at="2026-10-01"),
        entry("demo-forum", "osint", "public_reference", "Exemplo didático: alegação num fórum", "Alegação fictícia, sem confirmação. Demonstra a distinção entre publicação e facto."),
        entry("demo-indicator", "urlhaus", "malware", "Exemplo didático: sinalização de malware", "Indicador simulado. Nenhum domínio real foi consultado.", source_url="https://urlhaus.abuse.ch/", confirmation="reported"),
        entry("demo-general", "kev", "kev_general", "Exemplo didático: alerta geral", "Sem CVE real e sem associação ao alvo. Demonstra a apresentação de alertas.", source_url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog"),
        entry("demo-posture", "technical", "technical_posture", "Resumo da postura técnica", "Score académico fictício: 72/100. Não comprova intrusão.", meta={"demo": True, "score": 72, "scope": "authorized_technical_checks"}),
        entry("demo-csp", "technical", "technical", "Content-Security-Policy não observada no exemplo", "Resultado simulado de configuração; não prova vulnerabilidade explorável.", meta={"demo": True, "severity": "medium"}),
        entry("demo-cookies", "technical", "technical", "Atributos de cookies a rever no exemplo", "Cenário fictício de atributo Secure por verificar.", meta={"demo": True, "severity": "medium"}),
    ]
    runs = [{"provider": provider, "status": "demo", "message": "Demonstração fictícia, sem pedidos externos.", "results_count": sum(entry["provider"] == provider for entry in evidence), "observed_at": date} for provider in ["osint", "urlhaus", "kev", "technical", "ai"]]
    technical = {"score": 72, "summary": "Postura técnica fictícia, criada para demonstrar a apresentação conjunta com Threat Intelligence.", "risk_level": "medium", "details": {}, "findings": [
        {"title": "Content-Security-Policy não observada no exemplo", "description": "Resultado simulado de configuração; não prova vulnerabilidade explorável.", "recommendation": "Num sistema próprio, validar a política aplicável e testar compatibilidade antes de a alterar.", "severity": "medium", "category": "headers"},
        {"title": "Atributos de cookies a rever no exemplo", "description": "Cenário fictício de atributo Secure por verificar.", "recommendation": "Num sistema autorizado, confirmar os atributos por cookie e o contexto de utilização.", "severity": "medium", "category": "cookies"},
    ]}
    return {"id": "example-intelligence-v6", "kind": "domain", "domain": "loja-exemplo.example", "target": "https://loja-exemplo.example/", "organization": "Organização fictícia - exemplo académico", "is_demo": True, "created_at": date, "status": "completed", "technical": technical, "evidence": evidence, "previous_evidence": [], "runs": runs, "reports": [{"model": "demonstracao-sem-LLM", "prompt_version": "demo-v2-intelligence", "is_current": True, "created_at": date, "report": validated_report(demo_analysis(evidence), evidence)}], "coverage_summary": {"notes": ["Este cenário mostra o formato do relatório, sem avaliação de um sistema real."]}, "incident_grouping": {"groups": [], "limitation": "Referências sem critérios suficientes mantêm-se separadas; publicação não é data de incidente."}}
