"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { investigations, downloadInvestigation, Investigation, Evidence, Claim, Comparison, dateLabel, statusLabel, errorMessage, externalLink } from "@/lib/investigations";

const providerNames: Record<string, string> = { osint: "Notícias, fóruns e relatórios", ai: "Síntese IA", technical: "Verificações técnicas", urlhaus: "URLhaus", phishtank: "PhishTank", kev: "CISA KEV", exposure: "Exposição de dados" };

function EvidenceCard({ entry, index }: { entry: Evidence; index: number }) {
  const source = externalLink(entry.source_url);
  return <article className="evidenceItem" id={"evidence-" + entry.id}>
    <div className="evidenceHeading"><span className="evidenceNumber">E{index + 1}</span><div><span className="eyebrow">{entry.provider}</span><h3>{entry.title}</h3></div><span className="status neutral">{statusLabel(entry.confirmation)}</span></div>
    <p>{entry.description}</p>
    {entry.meta.not_returned_in_latest_success ? <p className="notice">Recolha anterior: esta evidência não voltou a ser devolvida na última consulta concluída. Não integra os resultados atuais nem comprova que a ameaça desapareceu.</p> : entry.meta.retained_from_earlier_attempt ? <p className="notice">Resultado anterior conservado: a última tentativa desta fonte falhou ou ficou incompleta. Verifica a data de consulta e a cobertura.</p> : null}
    {entry.meta.relevance === "general_alert_not_associated_with_target" ? <p className="notice">Alerta geral: não foi associado ao alvo investigado.</p> : null}
    {entry.meta.relevance === "product_candidate_version_unconfirmed" ? <p className="notice">Candidato por produto: a versão e as condições da vulnerabilidade não foram confirmadas neste website.</p> : null}
    {entry.meta.relevance === "needs_review" ? <p className="notice">Relação com a organização por verificar. Esta referência pode ser irrelevante.</p> : null}
    {entry.meta.matched_by === "organization_name" ? <p className="notice">Coincidência apenas pelo nome: pode tratar-se de uma organização diferente. O domínio do alvo não foi identificado nesta referência.</p> : null}
    <dl className="evidenceDates"><div><dt>Publicação</dt><dd>{dateLabel(entry.published_at)}</dd></div><div><dt>Incidente</dt><dd>{dateLabel(entry.event_at)}</dd></div><div><dt>Consulta</dt><dd>{dateLabel(entry.observed_at)}</dd></div></dl>
    {typeof entry.meta.catalog_added_at === "string" ? <p className="muted smallNote">Entrada no catálogo KEV: {entry.meta.catalog_added_at}. Esta data não é a do último ataque.</p> : null}
    {source ? <a className="sourceLink" href={source} target="_blank" rel="noopener noreferrer">Consultar fonte original ↗</a> : <span className="muted smallNote">Sem ligação externa associada.</span>}
  </article>;
}
function Claims({ claims, evidence }: { claims: Claim[]; evidence: Evidence[] }) {
  return <ul className="claimList">{claims.map((claim, index) => <li key={index}><p>{claim.text}</p><div className="citationLinks">{claim.evidence_ids.map((id) => { const found = evidence.findIndex((e) => e.id === id); return found >= 0 ? <a key={id} href={"#evidence-" + id}>E{found + 1}</a> : <span key={id} className="muted">Referência anterior indisponível</span>; })}</div></li>)}</ul>;
}
export default function InvestigationDetail({ id }: { id: string }) {
  const router = useRouter();
  const [data, setData] = useState<Investigation | null>(null);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [question, setQuestion] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    let active = true;
    async function refresh() {
      try {
        const result = await investigations.get(id, controller.signal);
        if (!active) return;
        setData(result);
        if (["queued", "running"].includes(result.status)) timer = setTimeout(refresh, 1500);
        else {
          const previous = await investigations.compare(id);
          if (active) setComparison(previous);
        }
      } catch (e) { if (active && !controller.signal.aborted) setError(errorMessage(e)); }
    }
    void refresh();
    return () => { active = false; controller.abort(); if (timer) clearTimeout(timer); };
  }, [id, refreshKey]);

  async function download() { setError(""); try { await downloadInvestigation(id); } catch (e) { setError(errorMessage(e)); } }
  async function ask(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await investigations.ask(id, question); setQuestion(""); setData(await investigations.get(id)); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  async function retry(provider: string) {
    const authorized = provider === "technical" ? window.confirm("Confirmo que este website é meu ou tenho autorização para repetir os pedidos técnicos.") : false;
    if (provider === "technical" && !authorized) return;
    setBusy(true); setError("");
    try {
      await investigations.retry(id, provider, authorized);
      setComparison(null);
      setData((current) => current ? { ...current, status: "queued", retryable_providers: [] } : current);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); setRefreshKey((key) => key + 1); }
  }
  async function remove() {
    if (!window.confirm("Remover esta investigação e os seus resultados?")) return;
    setBusy(true);
    try { await investigations.remove(id); router.push("/investigations"); }
    catch (e) { setError(errorMessage(e)); setBusy(false); }
  }
  if (!data) return <main className="container"><p role="status">{error || "A carregar investigação…"}</p><Link href="/investigations">Voltar às investigações</Link></main>;

  const running = ["queued", "running"].includes(data.status);
  const latest = data.reports.at(-1);
  const sourceRuns = data.runs.filter((r) => ["urlhaus", "phishtank", "osint", "exposure", "kev"].includes(r.provider));
  const allEvidence = [...data.evidence, ...data.previous_evidence];
  const allRuns = [...data.runs, ...data.retryable_providers.filter((name) => !data.runs.some((run) => run.provider === name)).map((name) => ({ provider: name, status: "not_started", message: "A investigação terminou antes de executar este módulo.", results_count: 0, observed_at: "" }))];
  const timeline = data.evidence.filter((e) => ["incident_report", "public_reference", "exposure"].includes(e.category)).sort((a, b) => (b.published_at || "").localeCompare(a.published_at || ""));
  const otherEvidence = data.evidence.filter((e) => !timeline.some((t) => t.id === e.id));
  const index = (entry: Evidence) => data.evidence.findIndex((e) => e.id === entry.id);
  const canAsk = !running && !data.is_demo && latest?.is_current && data.runs.some((r) => r.provider === "ai" && r.status === "success");

  return <main className="container investigationDetail">
    <Link className="backLink muted" href="/investigations">← Todas as investigações</Link>
    {data.is_demo ? <div className="demoBanner" role="note"><strong>DEMONSTRAÇÃO</strong> Dados fictícios, sem consultas às fontes nem a modelos de IA. Não representam incidentes reais.</div> : null}
    <header className="workspaceHeading"><div><span className="eyebrow">{data.kind === "message" ? "Análise de mensagem" : "Dossiê de domínio"}</span><h1>{data.kind === "message" ? "Mensagem suspeita" : data.domain}</h1><p className="muted">{dateLabel(data.created_at)} · <span role="status">{statusLabel(data.status)}</span></p></div><div className="actions"><button type="button" className="btn primary" onClick={() => void download()}>Exportar PDF</button>{!running ? <button type="button" className="linkButton" disabled={busy} onClick={() => void remove()}>Remover</button> : null}</div></header>
    {error ? <p role="alert" className="error">{error}</p> : null}
    <div className="investigationMetrics"><div><strong>{data.evidence.length}</strong><span>Evidências recolhidas</span></div><div><strong>{sourceRuns.filter((r) => ["success", "no_results", "demo"].includes(r.status)).length}/{sourceRuns.length}</strong><span>Fontes com resultado</span></div><div><strong>{timeline.length}</strong><span>Referências públicas</span></div><div><strong>{data.technical ? data.technical.score + "/100" : "—"}</strong><span>Postura técnica</span></div></div>
    <p className="notice">Configuração técnica, reputação e incidentes reportados são dimensões distintas. Ausência de correspondências não comprova segurança.</p>
    {!running && data.status === "partial" ? <p className="notice">Investigação terminada com cobertura incompleta. Fontes opcionais sem acesso também originam este estado; os módulos consultados mantêm os seus resultados. <Link href="/investigations#sources-heading">Ver requisitos dos acessos</Link>.</p> : null}

    <section className="card" aria-labelledby="coverage-heading"><h2 id="coverage-heading">Cobertura e estado das fontes</h2>{running ? <p className="muted" role="status">A recolher resultados. Cada módulo aparece à medida que termina.</p> : <p className="muted">Podes repetir uma fonte que falhou depois de confirmar o acesso. Os módulos concluídos mantêm os seus resultados. As quotas continuam a aplicar-se.</p>}<div className="runList">{allRuns.map((run) => <div className="runItem" key={run.provider}><div><strong>{providerNames[run.provider] || run.provider}</strong><p>{run.message}</p></div><div className="runActions"><span className={"status neutral state-" + run.status}>{statusLabel(run.status)}</span>{!running && data.retryable_providers.includes(run.provider) ? <button type="button" className="btn" disabled={busy} onClick={() => void retry(run.provider)} aria-label={run.provider === "ai" ? "Atualizar síntese IA" : "Repetir " + (providerNames[run.provider] || run.provider)}>{run.provider === "ai" ? "Atualizar síntese" : "Repetir fonte"}</button> : null}</div></div>)}</div></section>

    {data.message_analysis ? <section className="card"><h2>Sinais da mensagem</h2><p className="muted">{data.message_analysis.limitation}</p>{data.message_analysis.signals.length ? <ul>{data.message_analysis.signals.map((signal) => <li key={signal.code}>{signal.description}</li>)}</ul> : <p>Sem sinais nas regras implementadas. O resultado é inconclusivo.</p>}<p>{data.message_analysis.links.length} URL(s) normalizado(s). Os links não foram visitados.</p></section> : null}

    {data.coverage_summary ? <section className="card" aria-labelledby="coverage-notes-heading"><h2 id="coverage-notes-heading">O que a cobertura permite concluir</h2><ul>{data.coverage_summary.notes.map((note, index) => <li key={index}>{note}</li>)}</ul><p className="muted smallNote">Explicação gerada por regras locais a partir do estado das fontes. Não representa uma análise produzida por IA nem confirma a segurança do alvo.</p></section> : null}
    <section className="card aiSection" aria-labelledby="ai-heading"><span className="eyebrow">Interpretação com referências</span><h2 id="ai-heading">{data.is_demo ? "Exemplo de síntese" : "Assistente IA"}</h2>
      {latest && !latest.is_current ? <p className="notice" role="note">Síntese anterior desatualizada: as evidências ou a cobertura das fontes mudaram. Atualiza a síntese antes de fazer novas perguntas. O texto abaixo fica conservado para consulta.</p> : null}
      {latest ? <><p className="summaryText">{latest.report.summary}</p><h3>Observações</h3><Claims claims={latest.report.observations} evidence={allEvidence} /><h3>Ações sugeridas</h3><Claims claims={latest.report.recommendations} evidence={allEvidence} /><h3>Limitações</h3><ul className="muted">{latest.report.limitations.map((limit, i) => <li key={i}>{limit}</li>)}</ul><p className="muted smallNote">Modelo: {latest.model} · {latest.prompt_version} · {dateLabel(latest.created_at)}. As referências são verificadas pelo sistema; a interpretação continua sujeita a revisão.</p></> : <p className="muted">{running ? "A síntese será pedida após a recolha das evidências, ou atualizada no respetivo módulo." : "Sem síntese disponível. Consulta o estado da integração acima; os resultados recolhidos continuam acessíveis."}</p>}
      {canAsk ? <form className="form questionForm" onSubmit={ask}><label htmlFor="question">Pergunta sobre estas evidências</label><input id="question" className="input" value={question} onChange={(e) => setQuestion(e.target.value)} minLength={5} maxLength={500} required placeholder="O que merece ser investigado primeiro?" /><button className="btn" disabled={busy} type="submit">{busy ? "A consultar…" : "Perguntar ao assistente"}</button></form> : null}
    </section>

    {data.incident_grouping ? <section className="card" aria-labelledby="groups-heading"><h2 id="groups-heading">Agrupamento de referências candidatas</h2><p className="muted">{data.incident_grouping.limitation}</p>{data.incident_grouping.groups.length ? data.incident_grouping.groups.map((group) => <details key={group.id}><summary>{group.evidence_ids.length} referências candidatas · {group.event_at ? dateLabel(group.event_at) : "Mesma ligação de origem"}</summary><p>{group.note}</p><div className="citationLinks">{group.evidence_ids.map((eid) => <a key={eid} href={"#evidence-" + eid}>E{data.evidence.findIndex((e) => e.id === eid) + 1}</a>)}</div></details>) : <p>As referências disponíveis mantêm-se separadas porque não existem critérios suficientes para as agrupar.</p>}<p className="muted smallNote">{data.incident_grouping.ungrouped_evidence_ids.length} referência(s) sem agrupamento. Estes grupos não confirmam um incidente nem a sua relação com o alvo.</p></section> : null}
    <section aria-labelledby="timeline-heading"><div className="sectionHeading"><h2 id="timeline-heading">Referências e cronologia pública</h2><span className="muted">Publicação e incidente são datas diferentes</span></div><p className="muted">Excertos e alegações exigem leitura da fonte e confirmação da relação com a organização.</p>{timeline.length ? timeline.map((e) => <EvidenceCard key={e.id} entry={e} index={index(e)} />) : <div className="emptyState"><p>Sem referências nesta investigação. Verifica a cobertura das fontes antes de interpretar este resultado.</p></div>}</section>

    <section aria-labelledby="indicators-heading"><h2 id="indicators-heading">Indicadores e alertas</h2>{otherEvidence.length ? otherEvidence.map((e) => <EvidenceCard key={e.id} entry={e} index={index(e)} />) : <p className="muted">Ainda não existem evidências nesta secção.</p>}</section>
    {data.previous_evidence.length ? <section aria-labelledby="previous-evidence-heading"><h2 id="previous-evidence-heading">Evidências de recolhas anteriores</h2><p className="muted">Conservadas para contexto; não integram a contagem atual, a comparação ou a nova síntese IA.</p>{data.previous_evidence.map((e) => <EvidenceCard key={e.id} entry={e} index={allEvidence.findIndex((entry) => entry.id === e.id)} />)}</section> : null}
    {data.technical ? <section className="card"><h2>Postura técnica: {data.technical.score}/100</h2><p>{data.technical.summary}</p><p className="muted">Score académico de configuração, separado da reputação e das referências a incidentes.</p>{data.technical.findings.map((f, i) => <div className="technicalFinding" key={i}><h3>{f.title}</h3><p>{f.description}</p><p className="muted">{f.recommendation}</p></div>)}</section> : null}
    {comparison ? <section className="card"><h2>Comparação com investigação anterior</h2><p className="muted">{comparison.message}</p>{comparison.previous_id ? <><Link className="sourceLink" href={"/investigations/" + comparison.previous_id}>Consultar investigação anterior ↗</Link><p>{comparison.added.length} evidência(s) nova(s) · {comparison.removed.length} deixou/deixaram de constar da recolha.</p></> : null}</section> : null}
  </main>;
}
