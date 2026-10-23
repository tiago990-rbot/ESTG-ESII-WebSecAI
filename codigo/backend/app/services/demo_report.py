"""Explicitly fictional, rule-written preview of the intelligence contract. No LLM."""
from app.services.intelligence import QUESTIONS

def demo_analysis(evidence):
    public = next(entry["id"] for entry in evidence if entry["category"] == "incident_report")
    signal = next(entry["id"] for entry in evidence if entry["provider"] == "urlhaus")
    technical = next((entry["id"] for entry in evidence if entry["category"] == "technical_posture"), None)
    answers = {
        "history": ("O exemplo contém uma notícia fictícia sobre um incidente anterior. Serve para mostrar como documentar um relato; não descreve um ataque real.", [public]),
        "identity": ("O domínio .example é reservado para demonstração. Não foi verificada a identidade de qualquer empresa real.", []),
        "current_signals": ("Existe uma sinalização de malware simulada. Não se pode concluir que exista compromisso atual num sistema real.", [signal]),
        "technical": (("O cenário inclui uma postura técnica fictícia de 72/100 e duas configurações a rever. Não foram enviados pedidos ao domínio.", [technical]) if technical else ("As verificações técnicas não fazem parte deste exemplo. Não existe base para avaliar a configuração.", [])),
        "correlation": (("A notícia e os resultados técnicos coexistem no mesmo dossiê fictício. Não há prova de que as configurações expliquem o incidente referido.", [public, technical]) if technical else ("Sem resultados técnicos, não é possível cruzar configuração e histórico.", [])),
        "priorities": ("Numa investigação real, confirmar a relação da fonte com o alvo e a data do indicador antes de tomar decisões.", [public, signal]),
    }
    questions = [{"key": key, "answer": answers[key][0], "assessment": "supported" if answers[key][1] else "insufficient", "confidence": "low", "evidence_ids": answers[key][1], "caveat": "Demonstração escrita por regras locais, sem consulta a fontes ou modelo de IA."} for key in QUESTIONS]
    conclusions = [{"text": "O dossiê permite distinguir um relato, uma alegação e um indicador, preservando a origem e as datas desconhecidas.", "kind": "observation", "confidence": "low", "evidence_ids": [public, signal], "caveat": "Todos estes resultados são fictícios."}]
    correlations = []
    if technical:
        conclusions.append({"text": "O score técnico simulado mede configuração; a reputação e o histórico mantêm-se como dimensões separadas.", "kind": "observation", "confidence": "medium", "evidence_ids": [technical], "caveat": "Score fictício; não é uma certificação de segurança."})
        correlations.append({"text": "A referência pública e a configuração técnica foram reunidas para a mesma investigação. A recolha permite analisá-las lado a lado, sem estabelecer causalidade.", "kind": "contextual_link", "confidence": "low", "evidence_ids": [public, technical], "caveat": "Nenhuma evidência demonstra que a configuração observada tenha sido explorada no incidente referido."})
    return {
        "summary": "Demonstração de um relatório orientado à decisão: há referências fictícias a rever, sem prova de compromisso atual. " + ("A postura técnica simulada acrescenta contexto de configuração, sem explicar automaticamente o histórico. " if technical else "Não foram incluídas medições técnicas. ") + "O primeiro passo, num caso real, seria confirmar a identidade, a origem e a atualidade dos sinais. Este exemplo foi escrito por regras locais, sem utilização de um modelo de IA.",
        "observations": [{"text": "A notícia do exemplo tem data de publicação, mas não uma data de incidente confirmada.", "evidence_ids": [public]}],
        "recommendations": [{"text": "Confirmar o conteúdo e a relação com a organização antes de atribuir um incidente.", "evidence_ids": [public]}],
        "limitations": ["Dados fictícios e identificados como demonstração.", "Nenhum domínio foi visitado, nenhuma fonte foi consultada e nenhum modelo de IA foi chamado."],
        "intelligence": {"conclusions": conclusions, "correlations": correlations, "questions": questions, "actions": [
            {"priority": "P2", "action": "Validar a referência pública e a identidade do alvo num caso real.", "reason": "Uma notícia ou um nome semelhante não confirmam a organização afetada.", "validation": "Registar uma fonte original identificada, o domínio referido e as datas efetivamente conhecidas.", "evidence_ids": [public]},
            {"priority": "P2", "action": "Rever a data e o contexto do indicador antes de concluir sobre o estado atual.", "reason": "Uma sinalização de reputação não prova intrusão atual.", "validation": "Confirmar o registo de origem, a data de consulta e a relação específica com o alvo.", "evidence_ids": [signal]},
        ], "gaps": ["Não existem factos de um incidente real neste exemplo.", "Não há prova de causa, autoria, impacto ou compromisso atual."]},
    }
