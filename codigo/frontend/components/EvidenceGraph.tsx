"use client";
import { useState } from "react";
import EyeMark from "./EyeMark";
import { Evidence, externalLink, statusLabel } from "@/lib/investigations";
import { evidenceGraph, providerNames, relationNames, relationOf } from "@/lib/evidence-view";

export default function EvidenceGraph({ target, entries, numberOf, onEvidence }: { target: string; entries: Evidence[]; numberOf: (id: string) => number; onEvidence: (id: string) => void }) {
  const [selectedId, setSelectedId] = useState("");
  const graph = evidenceGraph(entries);
  const selected = graph.entries.find((entry) => entry.id === selectedId) || graph.entries[0];
  const height = Math.max(340, graph.entries.length * 56 + 64);
  const positions = new Map(graph.entries.map((entry, index) => [entry.id, 52 + index * 56]));
  const providerY = (provider: string) => {
    const nodes = graph.entries.filter((entry) => entry.provider === provider);
    return nodes.reduce((total, entry) => total + (positions.get(entry.id) || 0), 0) / nodes.length;
  };
  const source = selected && externalLink(selected.source_url);
  return <section aria-labelledby="graph-heading"><div className="sectionHeading"><div><span className="eyebrow">Mapa de proveniência</span><h2 id="graph-heading">Segue o caminho até à fonte.</h2></div><span className="wb-tag">Interativo · {graph.entries.length} evidências</span></div>
    <p className="muted">As linhas mostram a recolha: dossiê → módulo → evidência. Não representam ataques, responsáveis ou incidentes confirmados. Seleciona uma evidência para examinar a sua origem.</p>
    {!entries.length ? <div className="emptyState"><h3>Sem relações para mostrar.</h3><p className="muted">Limpa ou altera os filtros para reconstruir o mapa.</p></div> : <div className="wb-graphLayout"><div className="wb-graphCanvas"><div className="wb-graphLabels"><span>Dossiê</span><span>Módulo de recolha</span><span>Evidência</span></div><svg className="wb-graph" viewBox={"0 0 800 " + height} role="group" aria-labelledby="map-title map-description"><title id="map-title">Mapa de recolha de {target}</title><desc id="map-description">{graph.providers.length} módulos ligados a {graph.entries.length} evidências. Os mesmos nós podem ser selecionados nos botões da lista abaixo.</desc>
      {graph.providers.map((provider) => <path className="wb-graphLine" key={provider} d={`M140 ${height / 2} C225 ${height / 2} 205 ${providerY(provider)} 300 ${providerY(provider)}`} />)}
      {graph.edges.map((edge) => <path key={edge.evidenceId} className={"wb-graphLine " + (selected?.id === edge.evidenceId ? "is-selected" : "")} d={`M420 ${providerY(edge.provider)} C495 ${providerY(edge.provider)} 465 ${positions.get(edge.evidenceId)} 548 ${positions.get(edge.evidenceId)}`} />)}
      <circle cx="108" cy={height / 2} r="42" className="wb-targetHalo" /><circle cx="108" cy={height / 2} r="29" className="wb-targetNode" /><text x="108" y={height / 2 + 5} textAnchor="middle" className="wb-targetText">◎</text><text x="108" y={height / 2 + 67} textAnchor="middle" className="wb-mapLabel">{target.length > 23 ? target.slice(0, 20) + "…" : target}</text>
      {graph.providers.map((provider) => <g key={provider}><rect x="300" y={providerY(provider) - 18} width="120" height="36" rx="18" className="wb-providerNode" /><text x="360" y={providerY(provider) + 4} textAnchor="middle" className="wb-mapLabel">{providerNames[provider] || provider}</text></g>)}
      {graph.entries.map((entry) => <g key={entry.id} className={"wb-evidenceNode relation-" + relationOf(entry) + (selected?.id === entry.id ? " is-selected" : "")} role="button" tabIndex={0} aria-label={"Selecionar E" + numberOf(entry.id) + ": " + entry.title} aria-pressed={selected?.id === entry.id} onClick={() => setSelectedId(entry.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setSelectedId(entry.id); } }}><rect x="548" y={(positions.get(entry.id) || 0) - 20} width="236" height="40" rx="9" /><text x="560" y={(positions.get(entry.id) || 0) + 4}>E{numberOf(entry.id)} · {entry.title.length > 27 ? entry.title.slice(0, 24) + "…" : entry.title}</text></g>)}
    </svg><details className="wb-disclosure wb-mapList"><summary>Selecionar pela lista acessível</summary><div className="wb-nodeList">{graph.entries.map((entry) => <button key={entry.id} type="button" aria-pressed={selected?.id === entry.id} onClick={() => setSelectedId(entry.id)}>E{numberOf(entry.id)} · {entry.title}</button>)}</div></details></div>
    {selected ? <aside className="wb-inspector" aria-label="Evidência selecionada" aria-live="polite"><EyeMark /><span className="eyebrow">E{numberOf(selected.id)} · {providerNames[selected.provider] || selected.provider}</span><h3>{selected.title}</h3><span className={"wb-tag relation-" + relationOf(selected)}>{relationNames[relationOf(selected)]}</span><span className="wb-tag">{statusLabel(selected.confirmation)}</span><p>{selected.description}</p><p className="muted smallNote">Ligação representada: este módulo devolveu esta evidência para o dossiê. A relação com o alvo continua sujeita à validação do conteúdo.</p><button className="btn primary" type="button" onClick={() => onEvidence(selected.id)}>Examinar E{numberOf(selected.id)} →</button>{source ? <a className="sourceLink" href={source} target="_blank" rel="noopener noreferrer">Fonte original ↗</a> : <span className="muted smallNote">Sem URL de origem.</span>}</aside> : null}</div>}
    {graph.omitted > 0 ? <p className="notice">O mapa mostra as primeiras 24 evidências dos filtros atuais. Mais {graph.omitted} estão disponíveis na vista de evidências; filtra por módulo para explorar o restante.</p> : null}
    <div className="wb-legend"><span><i className="wb-legendDot" />Referência recolhida</span><span><i className="wb-legendDot review" />Relação por verificar / produto</span><span><i className="wb-legendDot general" />Alerta geral</span></div>
  </section>;
}
