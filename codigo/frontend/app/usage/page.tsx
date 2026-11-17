"use client";
import {FormEvent,useCallback,useEffect,useState} from "react";
import AuthGuard from "@/components/AuthGuard";
import {usage,UsageOverview,InternalLimit} from "@/lib/usage";
import {dateLabel,errorMessage} from "@/lib/investigations";

function GrantForm({limit,onSaved}:{limit:InternalLimit;onSaved:()=>void}) {
 const [reason,setReason]=useState("");const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [requestId,setRequestId]=useState("");
 async function submit(event:FormEvent){
  event.preventDefault();setBusy(true);setError("");const id=requestId||crypto.randomUUID();setRequestId(id);
  try{await usage.grant(limit.provider,limit.period,reason,id);setReason("");setRequestId("");onSaved();}
  catch(e){setError(errorMessage(e));}finally{setBusy(false);}
 }
 return <form className="quotaGrant" onSubmit={submit}>
  <label htmlFor={"reason-"+limit.provider}>Motivo da exceção</label><input className="input" id={"reason-"+limit.provider} minLength={8} maxLength={300} required value={reason} onChange={e=>{setReason(e.target.value);setRequestId("");}} disabled={busy} placeholder="Porquê mais uma chamada neste período?"/>
  <button className="btn" disabled={busy}>{busy?"A registar…":"Autorizar +1 neste período"}</button><small className="muted">Máximo de três exceções por período. Não altera o plano nem desbloqueia o fornecedor.</small>{error?<p role="alert" className="error">{error}</p>:null}
 </form>;
}
function Overview(){
 const [syncBusy,setSyncBusy]=useState(false);
 const [data,setData]=useState<UsageOverview|null>(null);const [error,setError]=useState("");const [loading,setLoading]=useState(true);
 const refresh=useCallback(async(signal?:AbortSignal)=>{setLoading(true);setError("");try{const result=await usage.get(signal);if(!signal?.aborted)setData(result);}catch(e){if(!signal?.aborted)setError(errorMessage(e));}finally{if(!signal?.aborted)setLoading(false);}},[]);
 useEffect(()=>{const c=new AbortController();void refresh(c.signal);return()=>c.abort();},[refresh]);
 async function syncTavily(){setSyncBusy(true);setError('');try{await usage.syncTavily();await refresh();}catch(e){setError(errorMessage(e));}finally{setSyncBusy(false);}}
 return <main className="container quotaPage">
  <div className="sectionHeader"><div><span className="eyebrow">CENTRO DE CONTROLO</span><h1>Utilização e limites</h1><p className="muted">O orçamento do grupo, com origem e hora de cada observação.</p></div><button className="btn" onClick={()=>void refresh()} disabled={loading}>{loading?"A atualizar…":"Atualizar painel"}</button></div>
  <p className="notice">Atualizar este painel consulta apenas o WebSecAI. Não faz pesquisas nem chamadas IA.</p>{error?<p className="error" role="alert">{error}</p>:null}
  {data?<><p className="muted">{data.note} · Painel consultado em {dateLabel(data.observed_at)}.</p><div className="quotaGrid">{data.providers.map(p=><article className="card quotaCard" key={p.id}>
   <header><div><h2>{p.name}</h2><p className="muted">{p.purpose}</p></div><span className={"badge "+(p.ready?"info":"medium")}>{!p.implemented?"Futuro":p.ready?"Sem bloqueio conhecido":"Indisponível"}</span></header>
   <div className="quotaStatus"><span>{p.configured?"Configuração presente":"Configuração em falta / desativada"}</span><span>{p.external?.last_success_at?"Último HTTP 200: "+dateLabel(p.external.last_success_at):"Sem consulta bem-sucedida observada"}</span></div>
   <h3>Limites internos · partilhados</h3>{p.internal.length?p.internal.map(l=><section className="quotaWindow" key={l.provider}>
    <div className="quotaNumbers"><strong>{l.reserved}<small> / {l.effective_limit} reservas</small></strong><span>{l.remaining} disponíveis</span></div><progress aria-label={"Reservas "+l.provider} max={Math.max(1,l.effective_limit)} value={Math.min(l.reserved,Math.max(1,l.effective_limit))}/>
    <p className="muted">Limite nosso: {l.base_limit}{l.extra?" + "+l.extra+" exceção(ões) temporária(s)":""}. Teto de segurança: {l.hard_limit}. Janela: {({day:"dia UTC",month:"mês UTC",minute:"minuto UTC"} as Record<string,string>)[l.window]}.</p><p>Renova: <time dateTime={l.reset_at}>{dateLabel(l.reset_at)}</time> (Lisboa)</p>
    {l.can_grant?<details><summary>Autorizar uma reserva adicional</summary><GrantForm limit={l} onSaved={()=>void refresh()}/></details>:null}
    {l.grants.length?<details><summary>Auditoria · {l.grants.length} exceção(ões)</summary><ul>{l.grants.map(g=><li key={g.id}>Administrador #{g.actor_id} · {dateLabel(g.created_at)} · {g.reason}</li>)}</ul></details>:null}
   </section>):<p className="muted">Sem contador operacional neste adaptador. Aplicam-se disponibilidade, cache e condições da fonte.</p>}
   {p.acceptance?<p className="notice">Janela de aceitação {p.acceptance.id}: {p.acceptance.reserved}/{p.acceptance.limit} reservas. Não renova automaticamente e não admite +1.</p>:null}
   <h3>Limites comunicados pelo fornecedor</h3>{p.external?<><p className="muted">Observado em {dateLabel(p.external.observed_at)} · âmbito: {p.external.scope} · HTTP {p.external.http_status}{p.external.stale?" · Informação antiga; o saldo pode ter mudado.":""}</p>
    {p.external.dimensions.length?p.external.dimensions.map(d=><div className="quotaExternal" key={d.unit}><strong>{({requests:'Pedidos / dia',tokens:'Tokens / minuto',credits_account:'Créditos · plano da conta',credits_key:'Créditos · limite da chave'} as Record<string,string>)[d.unit]||d.unit}</strong><span>{d.remaining??"Desconhecido"} restantes / {d.limit??"limite desconhecido"}{d.used!==undefined?' · '+d.used+' consumidos':''}</span><small>Observado: {dateLabel(d.observed_at||p.external!.observed_at)} · Renovação comunicada: {d.reset_at?dateLabel(d.reset_at):"Não disponível"} · Fonte: {d.source==='usage_endpoint'?'endpoint de utilização':'headers da resposta'}</small></div>):<p className="muted">O fornecedor não comunicou totais nesta resposta. Consulta o painel da conta para os valores em falta.</p>}
    {p.external.blocked_until?<p>Espera comunicada até {dateLabel(p.external.blocked_until)}.</p>:null}</>:<p className="muted">Não disponível. Sem observação de quota; não foi inventado um limite externo.</p>}
   {p.provider==='tavily'&&data.tavily_sync_enabled?<div><button className="btn" disabled={loading||syncBusy} onClick={()=>void syncTavily()}>{syncBusy?'A consultar fornecedor…':'Consultar saldo Tavily'}</button><p className="muted">Esta ação administrativa contacta o endpoint de utilização Tavily, sem fazer pesquisas. Não altera o plano nem os limites. Reservas de metadados: {data.metadata_usage.reserved_today}/{data.metadata_usage.daily_limit} hoje (renova {dateLabel(data.metadata_usage.daily_reset_at)}); {data.metadata_usage.reserved_this_window}/{data.metadata_usage.window_limit} nesta janela (renova {dateLabel(data.metadata_usage.window_reset_at)}).</p></div>:null}
   {p.blocked_reasons.length?<ul className="quotaReasons">{p.blocked_reasons.map(r=><li key={r}>{r}</li>)}</ul>:null}
  </article>)}</div><section className="card labFinding"><h2>Alojamento e base de dados</h2><p className="muted">Os consumos do alojamento ainda não estão ligados ao painel. Não é possível bloquear centralmente todas as quotas de alojamento a partir da aplicação. O responsável deve manter os planos gratuitos e alertas nos serviços.</p><div className="grid three">{data.infrastructure.map(service=><div key={service.id}><h3>{service.name}</h3><p className="muted">Consumo, limite e renovação: não disponíveis nesta instalação.</p><a className="sourceLink" href={service.console_url} target="_blank" rel="noopener noreferrer">Consultar consola oficial ↗</a></div>)}</div></section></>:loading?<p role="status">A consultar os contadores…</p>:null}
 </main>;
}
export default function UsagePage(){return <AuthGuard><Overview/></AuthGuard>;}
