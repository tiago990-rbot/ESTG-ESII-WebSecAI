import {request,API_BASE,getToken} from './api';
export type LabFile={path:string;content:string;lines:number;sha256:string;redacted:boolean};
export type LabFinding={id:string;tool:string;origin:string;retained_from_earlier_attempt?:boolean;rule:string;title:string;description:string;severity:string;confidence:string;path:string;line:number;end_line:number;line_known:boolean;snippet:string;recommendation:string;regression_test:string;related_paths:string[];review:{sequence:number;status:string;note:string;actor_id?:number}};
export type LabRun={id:string;tool:string;version:string;status:string;created_at:string;report:{findings?:LabFinding[];summary?:string;message?:string;limitations?:string[];provenance?:string;selection?:{path:string;included_lines:number;total_lines:number}[];priorities?:string[];correlations?:{finding_ids:string[];explanation:string;validation:string}[]}};
export type LabProject={id:string;name:string;revision:string;source_digest:string;created_at:string;files:LabFile[];runs:LabRun[];findings:LabFinding[];synthesis:(LabRun&{is_current?:boolean})|null;limitations:string[]};
export type LabListItem={id:string;name:string;revision:string;source_digest:string;created_at:string;file_count:number};
export type LabConfiguration={enabled:boolean;ai_configured:boolean;runner:string;note:string};
export const lab={
 configuration:(signal?:AbortSignal)=>request<LabConfiguration>('/api/v1/lab/configuration',{signal}),
 list:(signal?:AbortSignal)=>request<LabListItem[]>('/api/v1/lab',{signal,cache:'no-store'}),
 run:(id:string,runId:string)=>request<LabRun>('/api/v1/lab/'+id+'/runs/'+runId),
 get:(id:string,signal?:AbortSignal)=>request<LabProject>('/api/v1/lab/'+id,{signal,cache:'no-store'}),
 create:(data:{name:string;revision:string;authorized:boolean;files:{path:string;content:string}[];zip_base64:string})=>request<LabProject>('/api/v1/lab',{method:'POST',body:JSON.stringify(data)}),
 import:(id:string,tool:string,version:string,digest:string,report:string)=>request<LabProject>('/api/v1/lab/'+id+'/imports',{method:'POST',body:JSON.stringify({tool,version,source_digest:digest,report_json:report})}),
 analyze:(id:string,task:'review'|'synthesis')=>request('/api/v1/lab/'+id+'/ai/'+task,{method:'POST',body:JSON.stringify({consent_external_ai:true})}),
 review:(id:string,finding:LabFinding,status:string,note:string)=>request<LabProject>('/api/v1/lab/'+id+'/findings/'+finding.id+'/reviews',{method:'POST',body:JSON.stringify({status,note,previous_sequence:finding.review.sequence})}),
 cancel:(id:string,runId:string)=>request('/api/v1/lab/'+id+'/runs/'+runId+'/cancel',{method:'POST'}),
 remove:(id:string)=>request<void>('/api/v1/lab/'+id,{method:'DELETE'}),
};
export async function downloadLab(id:string){
 const response=await fetch(API_BASE+'/api/v1/lab/'+id+'/report',{headers:{Authorization:'Bearer '+(getToken()||'')}});
 if(!response.ok)throw new Error('Não foi possível gerar o PDF.');
 const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='websecai-code-'+id+'.pdf';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
}
