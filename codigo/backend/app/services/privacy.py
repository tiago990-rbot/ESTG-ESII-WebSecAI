import re
from app.core.targets import parse_target

def redact(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email]", text)
    text = re.sub(r"(?i)(password|passwd|palavra-passe|token|api[_-]?key)\s*[:=]\s*\S+", r"\1=[omitido]", text)
    text = re.sub(r"\bCVE-\d{4}-\d{4,}\b|\b(?:\+?\d[\d .()-]{8,}\d)\b", lambda m: m[0] if m[0].upper().startswith("CVE-") else "[número]", text, flags=re.I)
    return text

def extract_links(message: str) -> list[str]:
    links = []
    for raw in re.findall(r"https?://[^\s<>\"']+", message, flags=re.I):
        try:
            clean = parse_target(raw.rstrip(").,;!?]")).url
            if clean not in links:
                links.append(clean)
        except ValueError:
            continue
    return links[:3]

def message_signals(message: str) -> dict:
    low = message.lower()
    rules = [
        ("urgency", ["urgente", "imediatamente", "última oportunidade", "24 horas", "immediately", "urgent"], "Linguagem de urgência ou pressão temporal."),
        ("credentials", ["password", "palavra-passe", "credenciais", "iniciar sessão", "verify your account"], "Pedido relacionado com credenciais ou confirmação de conta."),
        ("payment", ["pagamento", "transferência", "bitcoin", "payment", "prémio"], "Referência a pagamento ou recompensa."),
    ]
    signals = [{"code": code, "description": description} for code, terms, description in rules if any(t in low for t in terms)]
    return {"signals": signals, "links": extract_links(message), "assessment": "sinais_a_investigar" if signals else "informacao_insuficiente", "limitation": "Sinais linguísticos não confirmam phishing. Links não foram visitados."}
