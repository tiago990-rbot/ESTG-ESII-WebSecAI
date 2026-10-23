import { Evidence, IntelligenceAnalysis } from "@/lib/investigations";

export const intelligenceQuestions = {
  history: "Há referências a incidentes anteriores?",
  identity: "As referências dizem respeito à mesma organização?",
  current_signals: "Existem sinais atuais de ameaça?",
  technical: "Que fragilidades técnicas foram observadas?",
  correlation: "O histórico e a configuração atual estão relacionados?",
  priorities: "O que deve ser feito primeiro?",
};
const confidenceNames = { low: "Baixa", medium: "Moderada", high: "Elevada" };
const judgementNames = { observation: "Observação", inference: "Inferência", hypothesis: "Hipótese" };
const correlationNames = { contextual_link: "Contexto em comum", possible_link: "Relação possível", contradiction: "Divergência entre referências" };
const assessmentNames = { supported: "Resposta fundamentada", hypothesis: "Hipótese", insufficient: "Informação insuficiente" };

function References({ ids, evidence, onEvidence }: { ids: string[]; evidence: Evidence[]; onEvidence: (id: string) => void }) {
  return <div className="citationLinks">{ids.map((id) => {
    const index = evidence.findIndex((entry) => entry.id === id);
    return index >= 0 ? <a key={id} href={"#evidence-" + id} onClick={(event) => { event.preventDefault(); onEvidence(id); }}>E{index + 1}</a> : <span key={id} className="muted smallNote">Referência indisponível</span>;
  })}</div>;
}
export default function IntelligenceBrief({ analysis, evidence, onEvidence }: { analysis: IntelligenceAnalysis; evidence: Evidence[]; onEvidence: (id: string) => void }) {
  return <div className="wb-intelligence">
    <p className="notice">Confiança qualitativa, sujeita a revisão. As referências permitem rastrear o texto; não confirmam automaticamente o conteúdo de uma alegação.</p>
    <section aria-labelledby="judgements-heading"><span className="eyebrow">O que a análise permite concluir</span><h3 id="judgements-heading">Conclusões fundamentadas</h3><div className="wb-judgements">{analysis.conclusions.map((item, index) => <article key={index}><div className="wb-tags"><span className="wb-tag">{judgementNames[item.kind]}</span><span className="wb-tag">Confiança {confidenceNames[item.confidence].toLocaleLowerCase("pt-PT")}</span></div><p>{item.text}</p><References ids={item.evidence_ids} evidence={evidence} onEvidence={onEvidence} /><p className="muted smallNote">Limite: {item.caveat}</p></article>)}</div>{!analysis.conclusions.length ? <p className="muted">As evidências não permitem formular conclusões sustentadas nesta recolha.</p> : null}</section>
    <section aria-labelledby="correlations-heading"><span className="eyebrow">Cruzar sem inventar ligações</span><h3 id="correlations-heading">Correlações e divergências</h3>{analysis.correlations.map((item, index) => <article className="wb-correlation" key={index}><div className="wb-tags"><span className="wb-tag">{correlationNames[item.kind]}</span><span className="wb-tag">Confiança {confidenceNames[item.confidence].toLocaleLowerCase("pt-PT")}</span></div><p>{item.text}</p><References ids={item.evidence_ids} evidence={evidence} onEvidence={onEvidence} /><p className="muted smallNote">Por confirmar: {item.caveat}</p></article>)}{!analysis.correlations.length ? <p className="muted">Não há critérios suficientes para propor correlações. Os sinais mantêm-se separados.</p> : null}</section>
    <section aria-labelledby="intelligence-questions-heading"><span className="eyebrow">Seis perguntas para orientar a decisão</span><h3 id="intelligence-questions-heading">Perguntas essenciais</h3>{analysis.questions.map((answer) => <details className="wb-disclosure wb-answer" key={answer.key}><summary>{intelligenceQuestions[answer.key]}<span className={"wb-tag " + (answer.assessment === "insufficient" ? "relation-review" : "")}>{assessmentNames[answer.assessment]}</span></summary><p>{answer.answer}</p><div className="wb-tags"><span className="wb-tag">Confiança {confidenceNames[answer.confidence].toLocaleLowerCase("pt-PT")}</span></div><References ids={answer.evidence_ids} evidence={evidence} onEvidence={onEvidence} /><p className="muted smallNote">Limite: {answer.caveat}</p></details>)}</section>
    <section aria-labelledby="priority-actions-heading"><span className="eyebrow">Da análise à ação</span><h3 id="priority-actions-heading">Prioridades e critérios de conclusão</h3><p className="muted smallNote">P1: tratar primeiro · P2: curto prazo · P3: planeamento. São prioridades de acompanhamento e correção, sem estimativa da probabilidade de ataque.</p>{[...analysis.actions].sort((a, b) => a.priority.localeCompare(b.priority)).map((item, index) => <article className="wb-priority" key={index}><span className="wb-priorityCode">{item.priority}</span><div><h4>{item.action}</h4><p>{item.reason}</p><References ids={item.evidence_ids} evidence={evidence} onEvidence={onEvidence} /><p className="muted smallNote"><strong>Como verificar a conclusão:</strong> {item.validation}</p></div></article>)}{!analysis.actions.length ? <p className="muted">Sem prioridades específicas sustentadas nesta análise.</p> : null}</section>
    <section><h3>Lacunas que impedem conclusões mais fortes</h3><ul className="muted wb-readableList">{analysis.gaps.map((gap, index) => <li key={index}>{gap}</li>)}</ul></section>
  </div>;
}
