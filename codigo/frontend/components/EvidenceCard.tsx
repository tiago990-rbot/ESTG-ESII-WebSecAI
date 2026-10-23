import { Evidence, dateLabel, externalLink, statusLabel } from "@/lib/investigations";
import { categoryNames, providerNames, relationNames, relationOf } from "@/lib/evidence-view";

export default function EvidenceCard({ entry, number }: { entry: Evidence; number: number }) {
  const source = externalLink(entry.source_url);
  const relation = relationOf(entry);
  return <article className="evidenceItem wb-evidence" id={"evidence-" + entry.id} tabIndex={-1}>
    <div className="evidenceHeading"><span className="evidenceNumber">E{number}</span><div><span className="eyebrow">{providerNames[entry.provider] || entry.provider} · {categoryNames[entry.category] || entry.category}</span><h3>{entry.title}</h3></div></div>
    <div className="wb-tags"><span className={"wb-tag relation-" + relation}>{relationNames[relation]}</span><span className="wb-tag">{statusLabel(entry.confirmation)}</span></div>
    <p>{entry.description}</p>
    {entry.meta.not_returned_in_latest_success ? <p className="notice">Recolha anterior: não voltou a ser devolvida na última consulta concluída. Não integra os resultados atuais nem comprova que a ameaça desapareceu.</p> : entry.meta.retained_from_earlier_attempt ? <p className="notice">Resultado anterior conservado: a última tentativa desta fonte falhou ou ficou incompleta. Verifica a data de consulta e a cobertura.</p> : null}
    {relation === "general" ? <p className="notice">Alerta geral: não foi associado ao alvo investigado.</p> : null}
    {relation === "product" ? <p className="notice">A versão e as condições da vulnerabilidade não foram confirmadas neste website.</p> : null}
    {relation === "review" ? <p className="notice">Relação com a organização por verificar. {entry.meta.matched_by === "organization_name" ? "Coincidência apenas pelo nome; pode ser outra organização. O domínio do alvo não foi identificado nesta referência." : "Esta referência pode ser irrelevante."}</p> : null}
    <dl className="evidenceDates"><div><dt>Publicação</dt><dd>{dateLabel(entry.published_at)}</dd></div><div><dt>Incidente</dt><dd>{dateLabel(entry.event_at)}</dd></div><div><dt>Consulta</dt><dd>{dateLabel(entry.observed_at)}</dd></div></dl>
    {typeof entry.meta.catalog_added_at === "string" ? <p className="muted smallNote">Entrada no catálogo KEV: {entry.meta.catalog_added_at}. Esta data não é a do último ataque.</p> : null}
    {source ? <a className="sourceLink" href={source} target="_blank" rel="noopener noreferrer">Consultar fonte original ↗</a> : <span className="muted smallNote">Sem ligação externa associada.</span>}
  </article>;
}
