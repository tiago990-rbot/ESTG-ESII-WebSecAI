"use client";
import AuthGuard from "@/components/AuthGuard";
import InvestigationLens from "@/components/InvestigationLens";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { investigations, InvestigationListItem, Provider, dateLabel, statusLabel, errorMessage, externalLink } from "@/lib/investigations";

function Workspace() {
  const router = useRouter();
  const [rows, setRows] = useState<InvestigationListItem[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [kind, setKind] = useState<"domain" | "message">("domain");
  const [target, setTarget] = useState("");
  const [organization, setOrganization] = useState("");
  const [product, setProduct] = useState("");
  const [message, setMessage] = useState("");
  const [technical, setTechnical] = useState(true);
  const [optionalSources, setOptionalSources] = useState<string[]>([]);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyStatus, setHistoryStatus] = useState("all");
  const [sourcesOpen, setSourcesOpen] = useState(false);

  useEffect(() => {
    let active = true;
    const query = new URLSearchParams(window.location.search);
    if (query.get("target")) setTarget(query.get("target")!.slice(0, 2000));
    if (query.get("mode") === "public") setTechnical(false);
    if (window.location.hash === "#sources-heading") setSourcesOpen(true);
    Promise.all([investigations.list(), investigations.providers()])
      .then(([list, sources]) => { if (active) { setRows(list); setProviders(sources.providers); setDemoEnabled(sources.demo_enabled); } })
      .catch((e) => { if (active) setError(errorMessage(e)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function start(demo: boolean) {
    setBusy(true); setError("");
    try {
      const result = await investigations.create({ kind, target, organization, product, message, technical: kind === "domain" && technical, authorized, demo, optional_sources: optionalSources });
      router.push("/investigations/" + result.id);
    } catch (e) { setError(errorMessage(e)); setBusy(false); }
  }
  function submit(event: FormEvent) { event.preventDefault(); void start(false); }
  const available = providers.filter((provider) => provider.group === "essential" && (provider.ready ?? provider.configured)).length;
  const implemented = providers.filter((provider) => provider.group === "essential").length;
  const shownRows = rows.filter((row) => (historyStatus === "all" || (historyStatus === "demo" ? row.is_demo : row.status === historyStatus)) && [row.domain, row.kind === "message" ? "Mensagem suspeita" : row.target].join(" ").toLocaleLowerCase("pt-PT").includes(historyQuery.trim().toLocaleLowerCase("pt-PT")));

  return <main className="container investigationsWorkspace wb-workspace">
    <header className="wb-workspaceHero"><div><span className="eyebrow"><span className="wb-liveDot" /> Threat Intelligence · OSINT</span><h1>Transforma pistas<br />em <em>contexto.</em></h1><p className="muted">Segue as fontes. Cruza os sinais. Descobre o que merece uma segunda análise.</p><div className="wb-heroStats"><span><strong>{loading ? "…" : rows.length}</strong> dossiês na tua conta</span><button type="button" onClick={() => { setSourcesOpen(true); document.getElementById("sources-heading")?.scrollIntoView({ block: "start" }); }}><strong>{loading ? "…" : available + "/" + implemented}</strong> fontes essenciais prontas ↗</button></div></div><InvestigationLens /></header>
    {error ? <p className="error" role="alert">{error}</p> : null}

    <div className="wb-startGrid"><section className="card investigationForm" aria-labelledby="new-investigation-heading"><div className="sectionHeading"><div><span className="eyebrow">01 / Ponto de partida</span><h2 id="new-investigation-heading">O que vamos investigar?</h2></div></div><div className="modeSelector" aria-label="Tipo de investigação"><button type="button" aria-pressed={kind === "domain"} className={kind === "domain" ? "mode active" : "mode"} onClick={() => setKind("domain")}><span aria-hidden="true">◎</span> Domínio ou link</button><button type="button" aria-pressed={kind === "message"} className={kind === "message" ? "mode active" : "mode"} onClick={() => setKind("message")}><span aria-hidden="true">≋</span> Mensagem suspeita</button></div>
      <form onSubmit={submit} className="form"><fieldset className="wb-disclosure"><legend>Fontes opcionais — desativadas por predefinição</legend><p className="muted smallNote">Seleciona apenas as fontes de que precisas. A escolha não configura credenciais nem garante acesso.</p>{providers.filter((provider) => provider.group === "optional").map((provider) => <label className="checkLabel" key={provider.id}><input type="checkbox" checked={optionalSources.includes(provider.id)} onChange={(event) => setOptionalSources((selected) => event.target.checked ? [...selected, provider.id] : selected.filter((id) => id !== provider.id))} />{provider.name} · {provider.ready ? "pronta para consulta" : "acesso por configurar"}</label>)}</fieldset>{kind === "domain" ? <><label htmlFor="target">Domínio ou URL público</label><div className="wb-targetInput"><span aria-hidden="true">◎</span><input id="target" className="input" placeholder="exemplo.pt" value={target} onChange={(event) => setTarget(event.target.value)} maxLength={2000} required autoCapitalize="none" spellCheck={false} /></div><fieldset className="wb-scopePicker"><legend>Âmbito do dossiê</legend><div><button type="button" aria-pressed={!technical} onClick={() => { setTechnical(false); setAuthorized(false); }}><strong>Investigação pública</strong><span>Notícias, indicadores e fontes. Sem pedidos técnicos ao alvo.</span></button><button type="button" aria-pressed={technical} onClick={() => setTechnical(true)}><strong>Dossiê completo</strong><span>Threat Intelligence + análise técnica + relatório integrado.</span></button></div></fieldset>{technical ? <label className="checkLabel wb-authorization"><input type="checkbox" checked={authorized} required onChange={(event) => setAuthorized(event.target.checked)} /> Confirmo que o website é meu ou que tenho autorização para as verificações técnicas.</label> : null}<p className="muted smallNote">{technical ? "O modo completo envia pedidos técnicos ao website autorizado. A IA cruza os resultados recolhidos; a exportação não repete a pesquisa." : "A pesquisa de inteligência não visita automaticamente o alvo."} Parâmetros de consulta e fragmentos do URL são omitidos. A demonstração usa sempre dados fictícios e não visita o alvo.</p><details className="wb-disclosure"><summary>Refinar contexto e verificações <span className="muted">· opcional</span></summary><div className="form wb-options"><label htmlFor="organization">Nome da organização</label><input id="organization" className="input" placeholder="Ajuda a distinguir organizações com nomes semelhantes" value={organization} onChange={(event) => setOrganization(event.target.value)} maxLength={150} /><label htmlFor="product">Produto tecnológico conhecido</label><input id="product" className="input" placeholder="Por exemplo: WordPress" value={product} onChange={(event) => setProduct(event.target.value)} maxLength={80} /><p className="muted smallNote">Filtra candidatos KEV; não confirma versões afetadas.</p></div></details></> : <><label htmlFor="message">Texto da mensagem</label><textarea id="message" className="input messageInput" placeholder="Cola uma mensagem de exemplo, removendo informação pessoal ou confidencial." value={message} onChange={(event) => setMessage(event.target.value)} minLength={10} maxLength={8000} required /><p className="muted smallNote">O texto integral não fica no histórico. São guardados sinais e URLs normalizados; os links não são abertos.</p></>}
      <div className="actions"><button className="btn primary" disabled={busy || loading} type="submit">{busy ? "A criar dossiê…" : "Iniciar investigação →"}</button>{demoEnabled ? <button className="btn wb-ghost" disabled={busy} type="button" onClick={() => void start(true)}>Explorar demonstração</button> : null}</div></form>
    </section><aside className="wb-processCard"><span className="eyebrow">Um percurso rastreável</span><h2>Da pergunta<br />à evidência.</h2><ol><li><span>01</span><div><strong>Recolher</strong><p>Notícias, fontes de ameaças e referências públicas, conforme os acessos.</p></div></li><li><span>02</span><div><strong>Explorar</strong><p>Filtra as pistas, percorre a cronologia e abre o mapa de proveniência.</p></div></li><li><span>03</span><div><strong>Interpretar</strong><p>Uma síntese com referências e limites claros, quando a IA está disponível.</p></div></li></ol><Link className="sourceLink" href="/dashboard">Só precisas de verificações técnicas? ↗</Link></aside></div>

    <section className="wb-history" aria-labelledby="history-heading"><div className="sectionHeading"><div><span className="eyebrow">O teu arquivo de investigação</span><h2 id="history-heading">Retoma o fio à investigação.</h2></div><span className="wb-tag">Até 100 registos recentes</span></div><div className="wb-historyFilters"><label>Pesquisar dossiês<input className="input" type="search" value={historyQuery} onChange={(event) => setHistoryQuery(event.target.value)} placeholder="Domínio ou mensagem…" /></label><label>Estado<select aria-label="Estado" className="input" value={historyStatus} onChange={(event) => setHistoryStatus(event.target.value)}><option value="all">Todos os estados</option>{Array.from(new Set(rows.map((row) => row.status))).sort().map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}<option value="demo">Apenas demonstrações</option></select></label></div>{!rows.length ? <div className="emptyState"><h3>{loading ? "A carregar histórico…" : "O primeiro dossiê começa acima."}</h3><p className="muted">Os resultados, fontes e limitações ficam associados à tua conta.</p></div> : <><p className="muted smallNote" role="status">{shownRows.length} de {rows.length} dossiês</p>{shownRows.length ? <div className="investigationList">{shownRows.map((row) => <Link className="investigationRow" key={row.id} href={"/investigations/" + row.id}><span className="wb-rowGlyph" aria-hidden="true">{row.kind === "message" ? "≋" : "◎"}</span><div><strong>{row.kind === "message" ? "Mensagem suspeita" : row.domain}</strong><p className="muted">{dateLabel(row.created_at)}{row.is_demo ? " · Dados fictícios" : ""}</p></div><span className={"status neutral state-" + row.status}>{statusLabel(row.status)}</span><span className="wb-rowArrow" aria-hidden="true">↗</span></Link>)}</div> : <div className="emptyState"><h3>Sem dossiês para estes filtros.</h3><button className="btn" type="button" onClick={() => { setHistoryQuery(""); setHistoryStatus("all"); }}>Limpar pesquisa</button></div>}</>}
    </section>

    <details className="card wb-sourcesDisclosure" id="sources-heading" open={sourcesOpen} onToggle={(event) => setSourcesOpen(event.currentTarget.open)}><summary><div><span className="eyebrow">Configuração e acessos</span><h2>Fontes desta instalação</h2></div><span className="wb-tag">{loading ? "A consultar…" : available + "/" + implemented + " configuradas"}</span></summary><p className="muted">Uma chave configurada só comprova acesso depois de uma consulta bem-sucedida. Uma fonte opcional só é consultada quando selecionada. Falhas nas fontes solicitadas mantêm o estado Parcial. Os limites são partilhados por toda a instalação.</p>{loading ? <p role="status">A consultar disponibilidade…</p> : <div className="sourceList">{providers.map((provider) => { const documentation = externalLink(provider.documentation_url); return <div className="sourceItem" key={provider.id}><span className={provider.configured ? "sourceDot available" : "sourceDot"} aria-hidden="true" /><div><strong>{provider.name}</strong><p className="muted">{provider.purpose}</p><p className="muted smallNote">Grupo: {({ essential: "Essencial", optional: "Opcional", analysis: "Síntese IA", context: "Contexto global", future: "Extensão futura" } as Record<string, string>)[provider.group || "optional"]}</p><p className="muted smallNote">{provider.setup_note} {documentation ? <a className="sourceLink" href={documentation} target="_blank" rel="noopener noreferrer">Documentação ↗</a> : null}</p></div><span className="sourceAvailability">{!provider.implemented ? "Extensão futura" : provider.configured ? "Configurada" : provider.id === "exposure" ? "Acesso condicionado" : "Sem chave nesta instalação"}</span></div>; })}</div>}</details>
    <p className="notice">Threat Intelligence ajuda a investigar. Uma referência exige confirmação; a ausência de correspondências não comprova segurança.</p>
  </main>;
}
export default function InvestigationsPage() { return <AuthGuard><Workspace /></AuthGuard>; }
