import type {LabProject} from '@/lib/lab';

export default function LabSynthesisPanel({data,onNavigate}:{data:LabProject;onNavigate:()=>void}){
 const synthesis=data.synthesis;if(!synthesis)return null;
 const findings=new Map(data.findings.map(f=>[f.id,f]));
 function reference(id:string){const f=findings.get(id);return f?<a className="sourceLink" href={'#finding-'+id} onClick={onNavigate}>{f.title}</a>:<span>Achado de uma versão anterior · {id.slice(0,10)}</span>;}
 return <section className="card labFinding"><span className="eyebrow">INTELIGÊNCIA / IA</span><h2>O que os achados sugerem</h2>
  {synthesis.is_current===false?<p className="notice">A síntese ficou desatualizada. Os achados ou revisões humanas mudaram.</p>:null}<p>{synthesis.report.summary}</p>
  {synthesis.report.priorities?.length?<><h3>Ordem sugerida de acompanhamento</h3><ol>{synthesis.report.priorities.map(id=><li key={id}>{reference(id)}</li>)}</ol></>:null}
  {synthesis.report.correlations?.map((relation,i)=><div key={i}><h3>Correlação {i+1}</h3><p>{relation.explanation}</p><ul>{relation.finding_ids.map(id=><li key={id}>{reference(id)}</li>)}</ul><p className="muted">Como validar: {relation.validation}</p></div>)}
  {synthesis.report.limitations?.map((note,i)=><p className="muted" key={i}>{note}</p>)}
 </section>;
}
