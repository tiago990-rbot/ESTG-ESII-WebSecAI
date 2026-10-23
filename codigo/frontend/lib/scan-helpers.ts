export function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("pt-PT");
}

export function riskLabel(risk?: string) {
  if (risk === "good") return "Bom";
  if (risk === "medium") return "Médio";
  if (risk === "weak") return "Fraco";
  return risk || "-";
}

export function severityLabel(severity?: string) {
  if (severity === "critical") return "Crítico";
  if (severity === "high") return "Alto";
  if (severity === "medium") return "Médio";
  if (severity === "low") return "Baixo";
  if (severity === "info") return "Informativo";
  return severity || "-";
}

export function scoreMessage(score?: number) {
  if (score === undefined || score === null) return "Sem score";
  if (score >= 85) return "Postura de segurança boa";
  if (score >= 60) return "Postura de segurança média";
  return "Postura de segurança fraca";
}
