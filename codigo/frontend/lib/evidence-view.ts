import type { Evidence } from "./investigations";

export const providerNames: Record<string, string> = {
  osint: "Pesquisa pública", ai: "Síntese IA", technical: "Verificações técnicas",
  urlhaus: "URLhaus", phishtank: "PhishTank", kev: "CISA KEV", exposure: "Exposição de dados", message: "Regras da mensagem",
};
export const categoryNames: Record<string, string> = {
  incident_report: "Relato de incidente", public_reference: "Referência pública", exposure: "Exposição",
  kev_general: "Alerta geral KEV", kev_candidate: "Candidato KEV", message_signal: "Sinal da mensagem",
  malware: "Indicador de malware", phishing: "Indicador de phishing",
};
export const relationNames = {
  reference: "Referência recolhida", review: "Relação por verificar", general: "Alerta geral",
  product: "Candidato por produto", signal: "Sinal local",
};
export type Relation = keyof typeof relationNames;
export type EvidenceFilters = { query: string; provider: string; relation: string };
export const emptyFilters: EvidenceFilters = { query: "", provider: "all", relation: "all" };

// These labels describe provenance/uncertainty, never whether the target was attacked.
export function relationOf(entry: Evidence): Relation {
  if (entry.meta.relevance === "general_alert_not_associated_with_target" || entry.category === "kev_general") return "general";
  if (entry.meta.matched_by === "organization_name" || entry.meta.relevance === "needs_review") return "review";
  if (entry.meta.relevance === "product_candidate_version_unconfirmed" || entry.category === "kev_candidate") return "product";
  return entry.category === "message_signal" ? "signal" : "reference";
}
function normalize(text: string) { return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-PT"); }
export function filterEvidence(entries: Evidence[], filters: EvidenceFilters) {
  const query = normalize(filters.query.trim());
  return entries.filter((entry) =>
    (filters.provider === "all" || entry.provider === filters.provider) &&
    (filters.relation === "all" || relationOf(entry) === filters.relation) &&
    (!query || normalize([entry.title, entry.description, entry.source_url, entry.provider, providerNames[entry.provider] || "", categoryNames[entry.category] || entry.category].join(" ")).includes(query)));
}
export type TimelineField = "published_at" | "event_at" | "observed_at";
export const timelineNames: Record<TimelineField, string> = { published_at: "Publicação", event_at: "Incidente", observed_at: "Consulta" };

export function dateTimestamp(value: string | null): number | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}(?:$|T)/.test(value)) return null;
  const day = value.slice(0, 10);
  const midnight = Date.parse(day + "T00:00:00Z");
  if (!Number.isFinite(midnight) || new Date(midnight).toISOString().slice(0, 10) !== day) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}
export function timelineEvidence(entries: Evidence[], field: TimelineField) {
  const dated: { entry: Evidence; timestamp: number }[] = [];
  const undated: Evidence[] = [];
  for (const entry of entries) {
    const timestamp = dateTimestamp(entry[field]);
    if (timestamp === null) undated.push(entry);
    else dated.push({ entry, timestamp });
  }
  // Do not substitute publication, consultation or catalog dates for incident dates.
  dated.sort((a, b) => b.timestamp - a.timestamp || a.entry.id.localeCompare(b.entry.id));
  return { dated, undated };
}
export function evidenceGraph(entries: Evidence[], limit = 24) {
  const seen = new Set<string>();
  const unique: Evidence[] = [];
  for (const entry of entries) {
    if (seen.has(entry.id)) continue;
    seen.add(entry.id);
    unique.push(entry);
  }
  const visible = unique.slice(0, Math.max(0, Math.min(48, Math.floor(limit) || 0))).sort((a, b) => a.provider.localeCompare(b.provider));
  const providers = Array.from(new Set(visible.map((entry) => entry.provider))).sort();
  return {
    entries: visible, providers, omitted: unique.length - visible.length,
    // Only collection edges: no inferred relationship between targets and incidents.
    edges: visible.map((entry) => ({ provider: entry.provider, evidenceId: entry.id, relation: relationOf(entry), kind: "collected_by" as const })),
  };
}
