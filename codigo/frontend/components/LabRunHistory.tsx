"use client";
import {useState} from 'react';
import {lab,LabRun} from '@/lib/lab';
import {dateLabel,errorMessage,statusLabel} from '@/lib/investigations';
export default function LabRunHistory({project,run,onCancel,disabled}:{project:string;run:LabRun;onCancel:()=>void;disabled:boolean}){
 const [detail,setDetail]=useState<LabRun|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function load(){setBusy(true);setError('');try{setDetail(await lab.run(project,run.id));}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 return <div className="quotaWindow"><strong>{run.tool} · {statusLabel(run.status)}</strong><p className="muted">{dateLabel(run.created_at)} · {run.version} · {run.report.provenance||'Processamento local'}</p><p>{run.report.summary||run.report.message}</p>
  {run.report.selection?<p className="muted">Código lido: {run.report.selection.map(s=>s.path+' ('+s.included_lines+'/'+s.total_lines+' linhas)').join('; ')}</p>:null}{run.report.limitations?.map((note,i)=><p className="muted" key={i}>{note}</p>)}
  {run.status==='running'?<button className="btn" onClick={onCancel} disabled={disabled}>Cancelar resultado</button>:<button className="linkButton" onClick={()=>void load()} disabled={busy}>{busy?'A carregar…':'Consultar registo e achados desta execução'}</button>}
  {detail?<details open><summary>Registo histórico · {detail.report.findings?.length??0} achado(s)</summary><p className="muted">Resultados desta execução; a seleção atual e as revisões humanas aparecem no painel principal.</p>{detail.report.findings?.map(f=><div key={f.id}><h4>{f.title}</h4><p><code>{f.path}{f.line_known?' : '+f.line:''}</code> · {f.severity}</p><p>{f.description}</p></div>)}{detail.report.summary?<p>{detail.report.summary}</p>:null}</details>:null}
  {error?<p role="alert" className="error">{error}</p>:null}
 </div>;
}
