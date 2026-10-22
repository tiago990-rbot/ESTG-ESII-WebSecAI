"use client";
import AuthGuard from "@/components/AuthGuard";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { investigations, InvestigationListItem, Provider, dateLabel, statusLabel, errorMessage } from "@/lib/investigations";

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
  const [technical, setTechnical] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([investigations.list(), investigations.providers()])
      .then(([list, sources]) => { if (active) { setRows(list); setProviders(sources.providers); setDemoEnabled(sources.demo_enabled); } })
      .catch((e) => { if (active) setError(errorMessage(e)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function start(demo: boolean) {
    setBusy(true); setError("");
    try {
      const result = await investigations.create({ kind, target, organization, product, message, technical: kind === "domain" && technical && !demo, authorized, demo });
      router.push("/investigations/" + result.id);
    } catch (e) { setError(errorMessage(e)); setBusy(false); }
  }

  function submit(event: FormEvent) { event.preventDefault(); void start(false); }
  const available = providers.filter((p) => p.configured && p.implemented).length;
  const implemented = providers.filter((p) => p.implemented).length;

  return <main className="container investigationsWorkspace">
    <div className="workspaceHeading"><div><span className="eyebrow">Threat Intelligence · OSINT</span><h1>Investiga com evidências.</h1><p className="muted">Cruza sinais técnicos, referências públicas e fontes de ameaças num único local.</p></div><Link className="btn" href="/dashboard">Análise técnica anterior</Link></div>
    {error ? <p className="error" role="alert">{error}</p> : null}
    <section className="card investigationForm">
      <div className="modeSelector" aria-label="Tipo de investigação">
        <button type="button" aria-pressed={kind === "domain"} className={kind === "domain" ? "mode active" : "mode"} onClick={() => setKind("domain")}>Domínio ou link</button>
        <button type="button" aria-pressed={kind === "message"} className={kind === "message" ? "mode active" : "mode"} onClick={() => setKind("message")}>Mensagem suspeita</button>
      </div>
      <form onSubmit={submit} className="form">
        {kind === "domain" ? <>
          <label htmlFor="target">Domínio ou URL público</label><input id="target" className="input" placeholder="exemplo.pt" value={target} onChange={(e) => setTarget(e.target.value)} maxLength={2000} required />
          <label htmlFor="organization">Nome da organização <span className="muted">(opcional)</span></label><input id="organization" className="input" placeholder="Ajuda a distinguir referências a organizações com nomes semelhantes" value={organization} onChange={(e) => setOrganization(e.target.value)} maxLength={150} />
          <label htmlFor="product">Produto tecnológico conhecido <span className="muted">(opcional)</span></label><input id="product" className="input" placeholder="Por exemplo: WordPress. Filtra candidatos KEV; não confirma versões afetadas." value={product} onChange={(e) => setProduct(e.target.value)} maxLength={80} />
          <label className="checkLabel"><input type="checkbox" checked={technical} onChange={(e) => setTechnical(e.target.checked)} /> Incluir verificações técnicas do website</label>
          {technical ? <label className="checkLabel"><input type="checkbox" checked={authorized} required onChange={(e) => setAuthorized(e.target.checked)} /> Confirmo que o website é meu ou que tenho autorização para estas verificações.</label> : null}
          <p className="muted smallNote">Os parâmetros de consulta e fragmentos do URL são omitidos. A pesquisa de inteligência não visita automaticamente o alvo.</p>
        </> : <>
          <label htmlFor="message">Texto da mensagem</label><textarea id="message" className="input messageInput" placeholder="Cola uma mensagem de exemplo, removendo informação pessoal ou confidencial." value={message} onChange={(e) => setMessage(e.target.value)} minLength={10} maxLength={8000} required />
          <p className="muted smallNote">O texto integral não fica no histórico. São guardados sinais e URLs normalizados; os links não são abertos.</p>
        </>}
        <div className="actions"><button className="btn primary" disabled={busy || loading} type="submit">{busy ? "A criar investigação…" : "Iniciar investigação"}</button>{demoEnabled ? <button className="btn" disabled={busy} type="button" onClick={() => void start(true)}>Experimentar demonstração</button> : null}</div>
      </form>
    </section>

    <section className="sourcesOverview" aria-labelledby="sources-heading"><div className="sectionHeading"><h2 id="sources-heading">Fontes desta instalação</h2><span className="muted">{available} de {implemented} integrações configuradas</span></div>
      <p className="muted">Pesquisa pública, CISA e IA formam o núcleo do dossiê. As fontes adicionais são opcionais. O estado Parcial indica cobertura incompleta; consulta o resultado de cada módulo. Uma chave configurada só comprova acesso depois de uma consulta bem-sucedida.</p>
      {loading ? <p className="muted">A consultar disponibilidade…</p> : <div className="sourceList">{providers.map((p) => <div className="sourceItem" key={p.id}><span className={p.configured ? "sourceDot available" : "sourceDot"} aria-hidden="true" /><div><strong>{p.name}</strong><p className="muted">{p.purpose}</p><p className="muted smallNote">{p.setup_note} <a className="sourceLink" href={p.documentation_url} target="_blank" rel="noopener noreferrer">Documentação ↗</a></p></div><span className="sourceAvailability">{!p.implemented ? "Extensão futura" : p.configured ? "Configurada" : p.id === "exposure" ? "Acesso condicionado" : "Sem chave nesta instalação"}</span></div>)}</div>}
    </section>

    <section aria-labelledby="history-heading"><div className="sectionHeading"><h2 id="history-heading">As tuas investigações</h2><span className="muted">Até 100 registos recentes</span></div>
      {!rows.length ? <div className="emptyState"><h3>{loading ? "A carregar histórico…" : "A primeira investigação começa aqui."}</h3><p className="muted">Os resultados, as fontes e as limitações ficam associados à tua conta.</p></div> : <div className="investigationList">{rows.map((row) => <Link className="investigationRow" key={row.id} href={"/investigations/" + row.id}><div><strong>{row.kind === "message" ? "Mensagem suspeita" : row.domain}</strong><p className="muted">{dateLabel(row.created_at)}{row.is_demo ? " · Dados demonstrativos" : ""}</p></div><span className={"status neutral state-" + row.status}>{statusLabel(row.status)}</span><span aria-hidden="true">↗</span></Link>)}</div>}
    </section>
  </main>;
}
export default function InvestigationsPage() { return <AuthGuard><Workspace /></AuthGuard>; }
