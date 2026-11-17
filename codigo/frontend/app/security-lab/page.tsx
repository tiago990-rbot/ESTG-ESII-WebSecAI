"use client";
import {useEffect,useState,FormEvent} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';
import {lab,LabListItem,LabConfiguration} from '@/lib/lab';
import {errorMessage,dateLabel} from '@/lib/investigations';
const EXAMPLE="from flask import Flask, request\nimport sqlite3\napp = Flask(__name__)\n\n@app.get('/search')\ndef search():\n    name = request.args.get('name', '')\n    db = sqlite3.connect(':memory:')\n    return str(db.execute(\"SELECT name FROM users WHERE name = '\" + name + \"'\").fetchall())\n";

function Workspace(){
 const router=useRouter();const [config,setConfig]=useState<LabConfiguration|null>(null);const [rows,setRows]=useState<LabListItem[]>([]);const [name,setName]=useState('');const [revision,setRevision]=useState('');const [path,setPath]=useState('app.py');const [code,setCode]=useState('');const [zip,setZip]=useState('');const [zipName,setZipName]=useState('');const [files,setFiles]=useState<{path:string;content:string}[]>([]);const [authorized,setAuthorized]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 useEffect(()=>{const c=new AbortController();void(async()=>{try{const conf=await lab.configuration(c.signal);if(c.signal.aborted)return;setConfig(conf);if(conf.enabled){const list=await lab.list(c.signal);if(!c.signal.aborted)setRows(list);}}catch(e){if(!c.signal.aborted)setError(errorMessage(e));}})();return()=>c.abort();},[]);
 async function upload(file:File|undefined){
  if(!file)return;setError('');if(file.size>1_000_000){setError('ZIP acima de 1 MB.');return;}
  try{const bytes=new Uint8Array(await file.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);setZip(btoa(raw));setZipName(file.name);setFiles([]);setCode('');}catch(e){setError(errorMessage(e));}
 }
 function addFile(){setError('');if(!code.trim()){setError('Introduz código primeiro.');return;}if(files.some(f=>f.path===path)){setError('Caminho já adicionado.');return;}setFiles(previous=>[...previous,{path,content:code}]);setCode('');setPath('');}
 async function create(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{const all=code.trim()?[...files,{path,content:code}]:files;const result=await lab.create({name,revision,authorized,files:all,zip_base64:zip});router.push('/security-lab/'+result.id);}catch(e){setError(errorMessage(e));setBusy(false);}}
 return <main className="container"><span className="eyebrow">LABORATÓRIO ESTÁTICO</span><h1>Security Lab <span className="brandAI">AI</span></h1><p className="muted">Do código às hipóteses verificáveis. Python, JavaScript e TypeScript.</p>
  <div className="labFlow"><span>Código autorizado</span><b>→</b><span>Ferramentas estáticas + revisão IA</span><b>→</b><span>Correlação e revisão humana</span><b>→</b><span>Relatório</span></div>
  <p className="notice">Este módulo não executa o código nem ataca websites. Envia apenas ficheiros revistos e sem credenciais. A IA só recebe código após consentimento separado.</p>
  {error?<p className="error" role="alert">{error}</p>:null}{!config?<p role="status">A consultar o módulo…</p>:!config.enabled?<section className="card"><h2>Módulo ainda desativado</h2><p>O administrador deve ativar SECURITY_LAB_ENABLED no backend depois de rever os limites e as condições de envio de código. As investigações TI continuam independentes.</p></section>:<div className="labGrid">
   <section className="card"><h2>Nova revisão de código</h2><form className="form" onSubmit={create}>
    <label>Nome do projeto<input className="input" required maxLength={100} value={name} onChange={e=>setName(e.target.value)}/></label><label>Revisão / commit<input className="input" required maxLength={100} placeholder="Ex.: commit ou entrega-01" value={revision} onChange={e=>setRevision(e.target.value)}/></label>
    <label>ZIP UTF-8, até 1 MB<input className="input" type="file" accept=".zip" onChange={e=>void upload(e.target.files?.[0])} disabled={busy}/></label>
    {zip?<p>{zipName} · <button type="button" className="linkButton" onClick={()=>{setZip('');setZipName('');}}>Usar código em texto</button></p>:<>
     <label>Caminho relativo<input className="input" value={path} maxLength={180} placeholder="src/app.py" onChange={e=>setPath(e.target.value)}/></label><label>Código<textarea className="input labCode" maxLength={30000} value={code} onChange={e=>setCode(e.target.value)} spellCheck={false}/></label>
     <div className="actions"><button className="btn" type="button" onClick={addFile} disabled={busy||files.length>=39}>Adicionar outro ficheiro</button><button className="linkButton" type="button" onClick={()=>{setCode(EXAMPLE);setPath('app.py');setName('Exemplo fictício · SQL');setRevision('demo-vulneravel-01');}}>Carregar exemplo fictício</button></div>
     {files.length?<ul>{files.map((f,i)=><li key={f.path}>{f.path} <button className="linkButton" type="button" aria-label={'Remover '+f.path} onClick={()=>setFiles(previous=>previous.filter((_,n)=>n!==i))}>×</button></li>)}</ul>:null}
    </>}
    <p className="muted">Até 40 ficheiros, 30 KB por ficheiro e 150 KB no total. Sem .env, dependências instaladas, binários ou chaves privadas.</p><label><input type="checkbox" checked={authorized} onChange={e=>setAuthorized(e.target.checked)} required/> Tenho autoridade para analisar e guardar este código nesta instalação. Removi dados privados e segredos.</label><button className="btn primary" disabled={busy||!authorized}>{busy?'A guardar revisão…':'Guardar revisão'}</button>
   </form></section>
   <section className="card"><h2>Histórico de revisões</h2><p className="muted">Revisões imutáveis, isoladas por conta. A IA partilha o orçamento Groq da instalação.</p><div className="investigationList">{rows.map(row=><Link className="investigationRow" key={row.id} href={'/security-lab/'+row.id}><div><strong>{row.name}</strong><p className="muted">{row.revision} · {row.file_count} ficheiro(s)<br/>{dateLabel(row.created_at)}</p></div><span aria-hidden="true">↗</span></Link>)}</div>{!rows.length?<p className="muted">Ainda não há revisões de código.</p>:null}<p><Link className="sourceLink" href="/usage">Ver orçamento e limites →</Link></p><p className="muted">{config.note}</p></section>
  </div>}
 </main>;
}
export default function SecurityLabPage(){return <AuthGuard><Workspace/></AuthGuard>;}
