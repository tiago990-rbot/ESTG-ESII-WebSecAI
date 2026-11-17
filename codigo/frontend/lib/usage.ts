import { request } from "./api";
export type InternalLimit = { provider:string; period:string; window:string; base_limit:number; extra:number; hard_limit:number; effective_limit:number; reserved:number; remaining:number; reset_at:string; can_grant:boolean; grants:{id:string;actor_id:number;reason:string;created_at:string}[] };
export type ExternalUsage = {scope:string;observed_at:string;last_success_at:string|null;http_status:number;blocked_until:string|null;stale:boolean;dimensions:{unit:string;window:string;observed_at?:string;used?:number|null;limit:number|null;remaining:number|null;reset_at:string|null;source:string}[]};
export type UsageOverview = {observed_at:string;admin:boolean;tavily_sync_enabled:boolean;metadata_usage:{reserved_today:number;daily_limit:number;daily_reset_at:string;reserved_this_window:number;window_limit:number;window_reset_at:string};note:string;infrastructure:{id:string;name:string;usage:null;limit:null;reset_at:null;console_url:string}[];providers:{id:string;provider:string;name:string;purpose:string;configured:boolean;ready:boolean;implemented:boolean;internal:InternalLimit[];external:ExternalUsage|null;blocked_reasons:string[];acceptance:{id:string;limit:number;reserved:number;reset_at:null}|null}[]};
export const usage = {
 syncTavily:()=>request("/api/v1/usage/tavily/sync",{method:"POST"}),
 get:(signal?:AbortSignal)=>request<UsageOverview>("/api/v1/usage",{signal,cache:"no-store"}),
 grant:(provider:string,period:string,reason:string,requestId:string)=>request("/api/v1/usage/grants",{method:"POST",body:JSON.stringify({provider,period,reason,request_id:requestId})}),
};
