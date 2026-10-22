import { request, getToken, API_BASE } from "./api";

export type Provider = { id: string; name: string; configured: boolean; purpose: string; implemented: boolean; access_requirement: string; setup_note: string; documentation_url: string };
export type ProviderRun = { provider: string; status: string; message: string; results_count: number; observed_at: string };
export type Evidence = { id: string; provider: string; category: string; title: string; description: string; source_url: string; confirmation: string; published_at: string | null; event_at: string | null; observed_at: string; meta: Record<string, unknown> };
export type Claim = { text: string; evidence_ids: string[] };
export type AnalystReport = { summary: string; observations: Claim[]; recommendations: Claim[]; limitations: string[] };
export type AIReport = { id: number; model: string; prompt_version: string; created_at: string; report: AnalystReport; is_current: boolean };
export type InvestigationListItem = { id: string; target: string; domain: string; kind: string; status: string; is_demo: boolean; created_at: string };
export type Investigation = InvestigationListItem & {
  organization: string; finished_at: string | null;
  technical: { score: number; risk_level: string; summary: string; details: Record<string, unknown>; findings: { title: string; description: string; recommendation: string; severity: string; category: string }[] } | null;
  message_analysis: { signals: { code: string; description: string }[]; links: string[]; assessment: string; limitation: string } | null;
  runs: ProviderRun[]; evidence: Evidence[]; previous_evidence: Evidence[]; reports: AIReport[]; retryable_providers: string[];
  coverage_summary: { origin: "local_rules"; has_target_evidence: boolean; target_evidence_count: number; notes: string[] };
  incident_grouping: { origin: "local_rules"; groups: { id: string; reason: string; status: string; event_at: string | null; kind: string; evidence_ids: string[]; source_urls: string[]; note: string }[]; ungrouped_evidence_ids: string[]; limitation: string };
};
export type NewInvestigation = { kind: "domain" | "message"; target: string; organization: string; product: string; message: string; technical: boolean; authorized: boolean; demo: boolean };
export type Comparison = { previous_id: string | null; added: string[]; removed: string[]; message: string };

export const investigations = {
  providers: () => request<{ providers: Provider[]; demo_enabled: boolean }>("/api/v1/investigations/providers"),
  list: () => request<InvestigationListItem[]>("/api/v1/investigations"),
  create: (data: NewInvestigation) => request<{ id: string; status: string }>("/api/v1/investigations", { method: "POST", body: JSON.stringify(data) }),
  get: (id: string, signal?: AbortSignal) => request<Investigation>("/api/v1/investigations/" + id, { signal }),
  compare: (id: string) => request<Comparison>("/api/v1/investigations/" + id + "/comparison"),
  ask: (id: string, text: string) => request<{ model: string; report: AnalystReport }>("/api/v1/investigations/" + id + "/questions", { method: "POST", body: JSON.stringify({ text }) }),
  retry: (id: string, provider: string, authorized = false) => request<{ id: string; provider: string; status: string }>("/api/v1/investigations/" + id + "/retry", { method: "POST", body: JSON.stringify({ provider, authorized }) }),
  remove: (id: string) => request<void>("/api/v1/investigations/" + id, { method: "DELETE" }),
};

export async function downloadInvestigation(id: string) {
  const response = await fetch(API_BASE + "/api/v1/investigations/" + id + "/report", { headers: { Authorization: "Bearer " + (getToken() || "") } });
  if (!response.ok) throw new Error("Não foi possível exportar o relatório.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url; link.download = "websecai-" + id + ".pdf";
  document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}

const labels: Record<string, string> = {
  queued: "Em fila", running: "Em curso", completed: "Concluída", partial: "Parcial", error: "Erro",
  interrupted: "Interrompida", success: "Consultada", no_results: "Sem correspondências",
  not_configured: "Sem acesso configurado", not_requested: "Não solicitada", rate_limited: "Quota atingida",
  access_denied: "Acesso recusado", demo: "Demonstração", unverified: "Por verificar",
  reported: "Reportado pela fonte", known_exploited: "Exploração conhecida",
  allegation: "Alegação por verificar",
  stale: "Síntese desatualizada", not_started: "Não executada",
};
export function statusLabel(status: string) { return labels[status] || status; }
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : "Ocorreu um erro inesperado."; }
export function dateLabel(value: string | null) {
  if (!value) return "Desconhecida";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "Data por validar";
  return /^\d{4}-\d{2}-\d{2}$/.test(value)
    ? d.toLocaleDateString("pt-PT", { timeZone: "UTC" })
    : d.toLocaleString("pt-PT", { timeZone: "Europe/Lisbon" });
}
export function externalLink(url: string): string | undefined {
  try { const p = new URL(url); return ["https:", "http:"].includes(p.protocol) && !p.username && !p.password ? url : undefined; }
  catch { return undefined; }
}
