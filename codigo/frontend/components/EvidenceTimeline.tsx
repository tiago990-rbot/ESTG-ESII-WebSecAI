"use client";
import { useState } from "react";
import { Evidence, dateLabel } from "@/lib/investigations";
import { TimelineField, providerNames, timelineEvidence, timelineNames } from "@/lib/evidence-view";

export default function EvidenceTimeline({ entries, numberOf, onEvidence }: { entries: Evidence[]; numberOf: (id: string) => number; onEvidence: (id: string) => void }) {
  const [field, setField] = useState<TimelineField>("published_at");
  const { dated, undated } = timelineEvidence(entries, field);
  return <section aria-labelledby="timeline-heading">
    <div className="sectionHeading"><div><span className="eyebrow">Explorar no tempo</span><h2 id="timeline-heading">Cada data no seu contexto.</h2></div><label className="wb-selectLabel">Ordenar por<select aria-label="Ordenar por" className="input" value={field} onChange={(e) => setField(e.target.value as TimelineField)}>{Object.entries(timelineNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label></div>
    <p className="muted">Mais recentes primeiro. A data de publicação, a do incidente e a da consulta são independentes. Uma data desconhecida fica fora do eixo temporal.</p>
    <div className="wb-timeline">{dated.map(({ entry }) => <article className="wb-timeEntry" key={entry.id}><div className="wb-timeDate"><span>{timelineNames[field]}</span><strong>{dateLabel(entry[field])}</strong></div><button type="button" className="wb-timeCard" onClick={() => onEvidence(entry.id)}><span className="eyebrow">E{numberOf(entry.id)} · {providerNames[entry.provider] || entry.provider}</span><strong>{entry.title}</strong><span className="sourceLink">Abrir evidência →</span></button></article>)}</div>
    {!dated.length ? <div className="emptyState"><h3>Sem datas válidas neste eixo.</h3><p className="muted">As referências mantêm-se disponíveis abaixo. Não inferimos datas a partir de notícias ou de entradas num catálogo.</p></div> : null}
    {undated.length ? <details className="wb-disclosure" open><summary>{undated.length} referência(s) sem data de {timelineNames[field].toLocaleLowerCase("pt-PT")}</summary><div className="wb-undated">{undated.map((entry) => <button type="button" key={entry.id} onClick={() => onEvidence(entry.id)}><span className="evidenceNumber">E{numberOf(entry.id)}</span><span>{entry.title}</span><span aria-hidden="true">↗</span></button>)}</div></details> : null}
    {!entries.length ? <p className="muted">Altera os filtros para mostrar evidências nesta vista.</p> : null}
  </section>;
}
