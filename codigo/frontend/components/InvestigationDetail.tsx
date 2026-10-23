"use client";
import Link from "next/link";
import dynamic from "next/dynamic";
import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { investigations, downloadInvestigation, Investigation, Evidence, Claim, Comparison, dateLabel, statusLabel, errorMessage } from "@/lib/investigations";
import { emptyFilters, EvidenceFilters, filterEvidence, providerNames, relationNames, relationOf } from "@/lib/evidence-view";
import EvidenceCard from "./EvidenceCard";
import EvidenceTimeline from "./EvidenceTimeline";
import EyeMark from "./EyeMark";

const EvidenceGraph = dynamic(() => import("./EvidenceGraph"), { ssr: false, loading: () => <p role="status" className="muted">A construir o mapa de proveniência…</p> });
const views = [
  ["overview", "Panorama"], ["evidence", "Evidências"], ["timeline", "Cronologia"],
  ["map", "Mapa de relações"], ["ai", "Assistente IA"], ["sources", "Fontes"],
] as const;
type View = typeof views[number][0];

function Citations({ ids, evidence, onEvidence }: { ids: string[]; evidence: Evidence[]; onEvidence: (id: string) => void }) {
  return <div className="citationLinks">{ids.map((id) => {
    const index = evidence.findIndex((entry) => entry.id === id);
    return index < 0 ? <span key={id} className="muted smallNote">Referência anterior indisponível</span> : <a key={id} href={"#evidence-" + id} onClick={(event) => { event.preventDefault(); onEvidence(id); }}>E{index + 1}</a>;
  })}</div>;
}
function Claims({ claims, evidence, onEvidence }: { claims: Claim[]; evidence: Evidence[]; onEvidence: (id: string) => void }) {
  return <ul className="claimList">{claims.map((claim, index) => <li key={index}><p>{claim.text}</p><Citations ids={claim.evidence_ids} evidence={evidence} onEvidence={onEvidence} /></li>)}</ul>;
}

export default function InvestigationDetail({ id }: { id: string }) {
  const router = useRouter();
  const [data, setData] = useState<Investigation | null>(null);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [question, setQuestion] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [view, setView] = useState<View>("overview");
  const [filters, setFilters] = useState<EvidenceFilters>(emptyFilters);
  const [pendingEvidence, setPendingEvidence] = useState("");

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

  useEffect(() => {
    if (!data?.id || !window.location.hash.startsWith("#evidence-")) return;
    const entryId = window.location.hash.slice("#evidence-".length);
    setView("evidence"); setFilters(emptyFilters); setPendingEvidence(entryId);
  }, [data?.id]);

  useEffect(() => {
    if (!pendingEvidence || view !== "evidence") return;
    const frame = requestAnimationFrame(() => {
      const element = document.getElementById("evidence-" + pendingEvidence);
      if (element) { element.scrollIntoView({ behavior: "auto", block: "center" }); element.focus({ preventScroll: true }); }
      setPendingEvidence("");
    });
    return () => cancelAnimationFrame(frame);
  }, [pendingEvidence, view, data]);

  function revealEvidence(entryId: string) {
    setFilters(emptyFilters); setView("evidence"); setPendingEvidence(entryId);
    window.history.replaceState(null, "", "#evidence-" + encodeURIComponent(entryId));
  }
  function changeView(next: View) {
    setView(next);
    if (window.location.hash) window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }
  function tabKey(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % views.length;
    else if (event.key === "ArrowLeft") next = (index + views.length - 1) % views.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = views.length - 1;
    else return;
    event.preventDefault(); changeView(views[next][0]);
    document.getElementById("tab-" + views[next][0])?.focus();
  }
  async function download() {
    setError(""); setDownloading(true);
    try { await downloadInvestigation(id); } catch (e) { setError(errorMessage(e)); } finally { setDownloading(false); }
  }
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
      await investigations.retry(id, provider, authorized); setComparison(null);
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
  if (!data) return <main className="container"><div className="wb-loading"><EyeMark /><p role="status">{error || "A abrir o dossiê…"}</p><Link className="sourceLink" href="/investigations">Voltar às investigações</Link></div></main>;

  const running = ["queued", "running"].includes(data.status);
  const latest = data.reports.at(-1);
  const sourceRuns = data.runs.filter((run) => ["urlhaus", "phishtank", "osint", "exposure", "kev"].includes(run.provider));
  const consulted = sourceRuns.filter((run) => ["success", "no_results", "demo"].includes(run.status)).length;
  const allEvidence = [...data.evidence, ...data.previous_evidence];
  const numberOf = (entryId: string) => allEvidence.findIndex((entry) => entry.id === entryId) + 1;
  const filtered = filterEvidence(data.evidence, filters);
  const allRuns = [...data.runs, ...data.retryable_providers.filter((name) => !data.runs.some((run) => run.provider === name)).map((name) => ({ provider: name, status: "not_started", message: "A investigação terminou antes de executar este módulo.", results_count: 0, observed_at: "" }))];
  const canAsk = !running && !data.is_demo && latest?.is_current && data.runs.some((run) => run.provider === "ai" && run.status === "success");
  const exploring = ["evidence", "timeline", "map"].includes(view);
  const relationCounts = Object.entries(relationNames).map(([key, label]) => ({ key, label, count: data.evidence.filter((entry) => relationOf(entry) === key).length })).filter((group) => group.count > 0);

  return <main className="container investigationDetail wb-dossier">
    <div className="wb-breadcrumb"><Link className="backLink muted" href="/investigations">← Investigações</Link><span className="wb-caseId">Dossiê / {data.id.slice(0, 8)}</span></div>
    {data.is_demo ? <div className="demoBanner" role="note"><strong>Demonstração · ambiente fictício</strong> Sem consultas a fontes ou modelos de IA. Os resultados não representam incidentes reais.</div> : null}
    <header className="workspaceHeading wb-dossierHeader"><div><span className="eyebrow"><span className="wb-liveDot" /> {data.kind === "message" ? "Análise de mensagem" : "Dossiê de domínio"}</span><h1>{data.kind === "message" ? "Mensagem suspeita" : data.domain}</h1><p className="muted">{data.organization ? data.organization + " · " : ""}{dateLabel(data.created_at)} <span className={"status neutral state-" + data.status} role="status">{statusLabel(data.status)}</span></p></div><div className="actions"><button type="button" className="btn" disabled={downloading} onClick={() => void download()}>{downloading ? "A exportar…" : "↓ PDF completo"}</button>{!running ? <button type="button" className="linkButton" disabled={busy} onClick={() => void remove()}>Remover</button> : null}</div></header>
    {error ? <p role="alert" className="error">{error}</p> : null}
    <div className="wb-flow" aria-label="Percurso da investigação"><button type="button" onClick={() => changeView("sources")}><span className={running ? "wb-stepNumber is-running" : "wb-stepNumber"}>01</span><span><strong>Recolha</strong><small>{running ? "Em curso" : consulted + " fontes com resultado"}</small></span><span aria-hidden="true">→</span></button><button type="button" onClick={() => changeView("evidence")}><span className="wb-stepNumber">02</span><span><strong>Evidências</strong><small>{data.evidence.length} referências atuais</small></span><span aria-hidden="true">→</span></button><button type="button" onClick={() => changeView("ai")}><span className="wb-stepNumber">03</span><span><strong>Interpretação</strong><small>{latest ? latest.is_current ? "Síntese disponível" : "Síntese por atualizar" : "Consultar cobertura"}</small></span><span aria-hidden="true">↗</span></button></div>
    <div className="wb-tabbar" role="tablist" aria-label="Vistas do dossiê">{views.map(([key, label], index) => <button type="button" role="tab" id={"tab-" + key} key={key} aria-controls={"panel-" + key} aria-selected={view === key} tabIndex={view === key ? 0 : -1} onClick={() => changeView(key)} onKeyDown={(event) => tabKey(event, index)}>{label}{key === "evidence" ? <span>{data.evidence.length}</span> : null}</button>)}</div>

    {exploring ? <section className="wb-filterbar" aria-label="Filtros das vistas de evidências"><div className="wb-filters"><label>Pesquisar nas evidências<input className="input" type="search" value={filters.query} placeholder="Título, descrição ou origem…" onChange={(event) => setFilters({ ...filters, query: event.target.value })} /></label><label>Módulo<select aria-label="Módulo" className="input" value={filters.provider} onChange={(event) => setFilters({ ...filters, provider: event.target.value })}><option value="all">Todos os módulos</option>{Array.from(new Set(data.evidence.map((entry) => entry.provider))).sort().map((provider) => <option key={provider} value={provider}>{providerNames[provider] || provider}</option>)}</select></label><label>Contexto<select aria-label="Contexto" className="input" value={filters.relation} onChange={(event) => setFilters({ ...filters, relation: event.target.value })}><option value="all">Todos os contextos</option>{Object.entries(relationNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label></div><div className="wb-filterMeta"><span className="muted" role="status">{filtered.length} de {data.evidence.length} evidências atuais · filtros partilhados entre as três vistas</span><button type="button" className="linkButton" onClick={() => setFilters(emptyFilters)}>Limpar filtros</button></div></section> : null}

    <section className="wb-view" role="tabpanel" id={"panel-" + view} aria-labelledby={"tab-" + view} tabIndex={0}>
      {view === "overview" ? <div className="wb-stack">
        <div className="wb-overviewGrid"><section className="card wb-brief"><span className="eyebrow">Leitura inicial · regras locais</span><h2>O que encontramos<br /><span className="wb-softText">e o que falta verificar.</span></h2><p className="muted">{data.evidence.length ? "Há referências para explorar. A presença num dossiê, por si só, não confirma uma intrusão." : "Ainda não há evidências nesta recolha. Consulta o estado das fontes antes de interpretar a ausência de resultados."}</p><div className="wb-relationBar" aria-hidden="true">{relationCounts.map((group) => <span key={group.key} className={"relation-" + group.key} style={{ flex: group.count }} />)}</div><div className="wb-contextCounts">{relationCounts.map((group) => <button type="button" key={group.key} onClick={() => { setFilters({ ...emptyFilters, relation: group.key }); changeView("evidence"); }}><span className={"wb-legendDot " + (group.key === "general" ? "general" : ["product", "review"].includes(group.key) ? "review" : "")} /><span>{group.label}</span><strong>{group.count}</strong><span aria-hidden="true">↗</span></button>)}</div></section>
        <section className="card wb-coverageCard"><span className="eyebrow">Cobertura desta recolha</span><div className="wb-bigMetric">{sourceRuns.length ? <>{consulted}<span>/{sourceRuns.length}</span></> : "—"}</div><p>Fontes com resultado{data.is_demo ? " demonstrativo" : " de consulta"}</p><div className="wb-coverageSegments" aria-label="Estado das fontes">{sourceRuns.map((run) => <button key={run.provider} type="button" className={"state-" + run.status} aria-label={(providerNames[run.provider] || run.provider) + ": " + statusLabel(run.status)} title={(providerNames[run.provider] || run.provider) + ": " + statusLabel(run.status)} onClick={() => changeView("sources")} />)}</div><p className="muted smallNote">Uma fonte sem correspondências conta como consultada. O valor mede cobertura, não segurança.</p><button type="button" className="btn" onClick={() => changeView("sources")}>Examinar fontes →</button></section></div>
        <div className="wb-twoColumns"><section className="card"><span className="eyebrow">Limites da pesquisa</span><h2>Antes de tirar conclusões</h2>{data.coverage_summary ? <ul className="wb-readableList">{data.coverage_summary.notes.map((note, index) => <li key={index}>{note}</li>)}</ul> : <p className="muted">Consulta os módulos executados para avaliar a cobertura.</p>}<p className="muted smallNote">Explicação por regras locais. Não é uma análise produzida por IA.</p>{data.status === "partial" ? <button type="button" className="sourceLink wb-textButton" onClick={() => changeView("sources")}>Ver cobertura incompleta e acessos →</button> : null}</section><section className="card aiSection"><EyeMark className="wb-miniEye" /><span className="eyebrow">Interpretação com referências</span><h2>{data.is_demo ? "Exemplo de síntese" : "Assistente IA"}</h2><p className="wb-summaryPreview">{latest?.report.summary || "A síntese ficará aqui quando o respetivo módulo produzir um resultado. As evidências continuam acessíveis sem IA."}</p>{latest && !latest.is_current ? <p className="notice">A síntese está desatualizada em relação à recolha atual.</p> : null}<button className="btn" type="button" onClick={() => changeView("ai")}>Abrir análise e referências →</button></section></div>
        {data.message_analysis ? <section className="card"><span className="eyebrow">Regras locais · mensagem</span><h2>Sinais a rever</h2><p className="muted">{data.message_analysis.limitation}</p>{data.message_analysis.signals.length ? <ul className="wb-readableList">{data.message_analysis.signals.map((signal) => <li key={signal.code}>{signal.description}</li>)}</ul> : <p>Sem sinais nas regras implementadas. O resultado é inconclusivo.</p>}<p>{data.message_analysis.links.length} URL(s) normalizado(s). Os links não foram visitados.</p></section> : null}
        {data.incident_grouping ? <section className="card"><div className="sectionHeading"><div><span className="eyebrow">Associações candidatas</span><h2>Referências que merecem ser cruzadas</h2></div><span className="wb-tag">{data.incident_grouping.groups.length} grupos</span></div><p className="muted">{data.incident_grouping.limitation}</p>{data.incident_grouping.groups.length ? data.incident_grouping.groups.map((group) => <details className="wb-disclosure" key={group.id}><summary>{group.evidence_ids.length} referências candidatas · {group.event_at ? dateLabel(group.event_at) : "Mesma ligação de origem"}</summary><p>{group.note}</p><Citations ids={group.evidence_ids} evidence={allEvidence} onEvidence={revealEvidence} /></details>) : <p>As referências mantêm-se separadas: não existem critérios suficientes para as agrupar.</p>}<p className="muted smallNote">{data.incident_grouping.ungrouped_evidence_ids.length} referência(s) sem agrupamento. Estes grupos não confirmam um incidente nem a sua relação com o alvo.</p></section> : null}
        {data.technical ? <section className="card"><div className="sectionHeading"><div><span className="eyebrow">Dimensão técnica</span><h2>Postura de configuração</h2></div><strong className="wb-score">{data.technical.score}<span>/100</span></strong></div><p>{data.technical.summary}</p><p className="notice">Score académico de configuração, separado da reputação e das referências a incidentes.</p><details className="wb-disclosure"><summary>Examinar {data.technical.findings.length} verificações técnicas</summary>{data.technical.findings.map((finding, index) => <div className="technicalFinding" key={index}><h3>{finding.title}</h3><p>{finding.description}</p><p className="muted">{finding.recommendation}</p></div>)}</details></section> : null}
        {comparison ? <section className="card"><span className="eyebrow">Continuidade</span><h2>O que mudou desde a última recolha?</h2><p className="muted">{comparison.message}</p>{comparison.previous_id ? <><Link className="sourceLink" href={"/investigations/" + comparison.previous_id}>Consultar investigação anterior ↗</Link><p>{comparison.added.length} evidência(s) nova(s) · {comparison.removed.length} deixou/deixaram de constar da recolha.</p></> : null}</section> : null}
      </div> : null}

      {view === "evidence" ? <div className="wb-stack"><div className="sectionHeading"><div><span className="eyebrow">Biblioteca de evidências</span><h2>Abre, cruza, verifica.</h2></div><span className="muted smallNote">As referências E# mantêm a numeração entre vistas.</span></div>{filtered.length ? <div className="wb-evidenceList">{filtered.map((entry) => <EvidenceCard key={entry.id} entry={entry} number={numberOf(entry.id)} />)}</div> : <div className="emptyState"><h3>{data.evidence.length ? "Nenhuma evidência corresponde aos filtros." : "Sem evidências atuais."}</h3><p className="muted">{data.evidence.length ? "Altera a pesquisa, o módulo ou o contexto para continuar." : "Verifica a cobertura das fontes. Ausência de resultados não comprova segurança."}</p><button className="btn" type="button" onClick={() => data.evidence.length ? setFilters(emptyFilters) : changeView("sources")}>{data.evidence.length ? "Mostrar todas" : "Ver fontes"}</button></div>}{data.previous_evidence.length ? <details className="wb-disclosure" open><summary>Arquivo · {data.previous_evidence.length} evidências de recolhas anteriores</summary><p className="muted">Conservadas para contexto; fora dos filtros, da contagem atual, do mapa, da comparação e da nova síntese IA.</p>{data.previous_evidence.map((entry) => <EvidenceCard key={entry.id} entry={entry} number={numberOf(entry.id)} />)}</details> : null}</div> : null}
      {view === "timeline" ? <EvidenceTimeline entries={filtered} numberOf={numberOf} onEvidence={revealEvidence} /> : null}
      {view === "map" ? <EvidenceGraph target={data.kind === "message" ? "Mensagem" : data.domain} entries={filtered} numberOf={numberOf} onEvidence={revealEvidence} /> : null}

      {view === "ai" ? <section className="card aiSection"><span className="eyebrow">Interpretação com referências</span><h2>{data.is_demo ? "Exemplo de síntese · regras demonstrativas" : "Assistente IA"}</h2>{latest && !latest.is_current ? <p className="notice" role="note">Síntese anterior desatualizada: as evidências ou a cobertura mudaram. Atualiza a síntese antes de fazer novas perguntas. O texto fica conservado para consulta.</p> : null}{latest ? <><p className="summaryText">{latest.report.summary}</p><h3>Observações</h3><Claims claims={latest.report.observations} evidence={allEvidence} onEvidence={revealEvidence} /><h3>Ações sugeridas</h3><Claims claims={latest.report.recommendations} evidence={allEvidence} onEvidence={revealEvidence} /><h3>Limitações</h3><ul className="muted wb-readableList">{latest.report.limitations.map((limit, index) => <li key={index}>{limit}</li>)}</ul><p className="muted smallNote">Modelo: {latest.model} · {latest.prompt_version} · {dateLabel(latest.created_at)}. O sistema valida os identificadores das referências; a interpretação do seu conteúdo exige revisão.</p></> : <p className="muted">{running ? "A síntese será pedida após a recolha das evidências." : "Sem síntese disponível. Consulta o estado da integração; os resultados recolhidos continuam acessíveis."}</p>}{canAsk ? <form className="form questionForm" onSubmit={ask}><label htmlFor="question">Pergunta sobre estas evidências</label><input id="question" className="input" value={question} onChange={(event) => setQuestion(event.target.value)} minLength={5} maxLength={500} required placeholder="O que merece ser investigado primeiro?" /><button className="btn primary" disabled={busy} type="submit">{busy ? "A consultar…" : "Perguntar ao assistente"}</button></form> : null}<button className="sourceLink wb-textButton" type="button" onClick={() => changeView("sources")}>Ver estado ou atualizar o módulo IA →</button></section> : null}

      {view === "sources" ? <section className="card"><span className="eyebrow">Transparência da recolha</span><h2>Cada módulo, o seu resultado.</h2><p className="muted">{running ? "A recolher resultados. Cada módulo aparece à medida que termina." : "Podes repetir um módulo disponível depois de confirmar o acesso. Os restantes resultados são mantidos e as quotas continuam a aplicar-se."}</p>{data.status === "partial" ? <p className="notice">Cobertura incompleta. Fontes opcionais sem acesso também originam o estado Parcial. <Link className="sourceLink" href="/investigations#sources-heading">Requisitos dos acessos ↗</Link></p> : null}<div className="runList">{allRuns.map((run) => <div className="runItem" key={run.provider}><div><strong>{providerNames[run.provider] || run.provider}</strong><p>{run.message}</p><span className="muted smallNote">{run.results_count} resultado(s){run.observed_at ? " · " + dateLabel(run.observed_at) : ""}</span></div><div className="runActions"><span className={"status neutral state-" + run.status}>{statusLabel(run.status)}</span>{!running && data.retryable_providers.includes(run.provider) ? <button type="button" className="btn" disabled={busy} onClick={() => void retry(run.provider)} aria-label={run.provider === "ai" ? "Atualizar síntese IA" : "Repetir " + (providerNames[run.provider] || run.provider)}>{run.provider === "ai" ? "Atualizar síntese" : "Repetir fonte"}</button> : null}</div></div>)}</div></section> : null}
    </section>
    {views.filter(([key]) => key !== view).map(([key]) => <section hidden key={key} role="tabpanel" id={"panel-" + key} aria-labelledby={"tab-" + key} />)}
    <footer className="wb-dossierFooter"><EyeMark /><p>Configuração, reputação e incidentes reportados são dimensões distintas.<br /><span className="muted">Ausência de correspondências não comprova segurança. O PDF exporta o dossiê completo, independentemente dos filtros.</span></p></footer>
  </main>;
}
