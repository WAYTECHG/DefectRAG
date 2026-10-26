// Dependency-free Edge worker. Tests inject fetch/env; nothing starts on import.
import {emailConfiguration,emailMessage} from './direct-email.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const KINDS=new Set(['requested','approved','rejected','revoked']);
export const LIMITS=Object.freeze({events:2,budgetMs:100000,rpcMs:15000,webhookMs:20000,reserveMs:52000});
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
function sameSecret(a,b){
 if(typeof a!=='string'||typeof b!=='string'||!b||a.length!==b.length)return false;
 let different=0;for(let i=0;i<a.length;i++)different|=a.charCodeAt(i)^b.charCodeAt(i);return different===0;
}
function httpsUrl(value){const url=new URL(value);if(url.protocol!=='https:'||url.username||url.password||url.hash)throw new Error('invalid_endpoint');return url}
function configurationCheck(env,expectedEvent){
 const present=value=>typeof value==='string'&&value.trim().length>0;
 let urlValid=false,emailValid=false;
 try{httpsUrl(env.SUPABASE_URL);urlValid=true}catch{}
 try{emailConfiguration(env);emailValid=true}catch{}
 const checks={
  transport_resend:env.DEFECTRAG_NOTIFICATION_TRANSPORT==='resend',
  sandbox_enabled:env.DEFECTRAG_EMAIL_SANDBOX==='1',
  supabase_url_https:urlValid,
  service_role_key_present:present(env.SUPABASE_SERVICE_ROLE_KEY),
  resend_key_present:present(env.DEFECTRAG_RESEND_API_KEY),
  test_sender:env.DEFECTRAG_EMAIL_FROM==='onboarding@resend.dev',
  developer_recipient_format:typeof env.DEFECTRAG_EMAIL_QA_RECIPIENT==='string'
   &&env.DEFECTRAG_EMAIL_QA_RECIPIENT.length<=254
   &&/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(env.DEFECTRAG_EMAIL_QA_RECIPIENT),
  qa_event_matches:env.DEFECTRAG_EMAIL_QA_EVENT_ID===expectedEvent,
  email_configuration_valid:emailValid
 };
 const developerChecks={developer_only:env.DEFECTRAG_EMAIL_DEVELOPER_ONLY==='1',
  sandbox_off:env.DEFECTRAG_EMAIL_SANDBOX==='0',transport_resend:checks.transport_resend,
  supabase_url_https:checks.supabase_url_https,service_role_key_present:checks.service_role_key_present,
  resend_key_present:checks.resend_key_present,test_sender:checks.test_sender,
  developer_recipient_format:checks.developer_recipient_format,email_configuration_valid:emailValid};
 return {diagnostic:'configuration_only_no_network',delivery_disabled:true,
  ready_for_qa:env.DEFECTRAG_EMAIL_DEVELOPER_ONLY!=='1'&&Object.values(checks).every(Boolean),checks,
  ready_for_developer_only:Object.values(developerChecks).every(Boolean),developer_checks:developerChecks};
}
function safeJob(job){
 return UUID.test(job.event_id)&&UUID.test(job.lease_token)&&UUID.test(job.request_id)&&KINDS.has(job.kind)
  &&Number.isInteger(job.version)&&job.version>0&&typeof job.recipient_email==='string'
  &&job.recipient_email.length<=254&&!/[\r\n]/.test(job.recipient_email)&&/^[^@\s]+@[^@\s]+$/.test(job.recipient_email)
  &&typeof job.display_name==='string'&&job.display_name.length<=80;
}
export async function dispatchNotifications({env,fetcher=fetch,now=()=>performance.now(),budgetMs=LIMITS.budgetMs}){
 // A monotonic invocation deadline bounds fetch AND response-body consumption.
 // Test budgets may be smaller; callers cannot raise the production ceiling.
 const deadline=now()+Math.min(Math.max(budgetMs,1),LIMITS.budgetMs);
 async function boundedJson(url,options,limit){
  const duration=Math.min(limit,deadline-now());
  if(duration<=0)throw new Error('invocation_deadline');
  const controller=new AbortController();let timer;
  const timeout=new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(new Error('request_timeout'))},duration)});
  try{return await Promise.race([(async()=>{
   const response=await fetcher(url,{...options,signal:controller.signal});
   return {ok:response.ok,status:response.status,body:response.ok?await response.json():null};
  })(),timeout])}finally{clearTimeout(timer)}
 }
 const base=httpsUrl(env.SUPABASE_URL).origin;
 const direct=env.DEFECTRAG_NOTIFICATION_TRANSPORT==='resend';
 if(env.DEFECTRAG_NOTIFICATION_TRANSPORT&&!['resend','n8n'].includes(env.DEFECTRAG_NOTIFICATION_TRANSPORT))throw new Error('invalid_transport');
 const hook=direct?'https://api.resend.com/emails':httpsUrl(env.DEFECTRAG_N8N_WEBHOOK_URL).href;
 const mailConfig=direct?emailConfiguration(env):null;
 if(!direct&&env.DEFECTRAG_EMAIL_DEVELOPER_ONLY==='1')throw new Error('developer_mode_requires_resend');
 if(!env.SUPABASE_SERVICE_ROLE_KEY||(!direct&&(!env.DEFECTRAG_N8N_WEBHOOK_SECRET||env.DEFECTRAG_N8N_WEBHOOK_SECRET.length<32)))throw new Error('missing_configuration');
 const headers={'apikey':env.SUPABASE_SERVICE_ROLE_KEY,'Authorization':'Bearer '+env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'};
 async function rpc(name,payload){
  const response=await boundedJson(base+'/rest/v1/rpc/'+name,{method:'POST',headers,body:JSON.stringify(payload),redirect:'error'},LIMITS.rpcMs);
  if(!response.ok)throw new Error('outbox_unavailable');return response.body;
 }
 const result={claimed:0,accepted:0,retried:0,leaseLost:0};
 const processed=new Set();
 for(let index=0;index<LIMITS.events;index++){
  // Reserve claim + send + finish + overhead BEFORE claiming. Unstarted rows
  // remain queued, without a consumed attempt or five-minute lease delay.
  if(deadline-now()<LIMITS.reserveMs+(direct?LIMITS.rpcMs:0)){result.budgetLimited=true;break}
  const jobs=await rpc(mailConfig?.developerOnly?'defectrag_claim_developer_notifications':direct?'defectrag_claim_direct_notifications':'defectrag_claim_notifications',
   mailConfig?.developerOnly?{p_recipient:env.DEFECTRAG_EMAIL_QA_RECIPIENT}:
    {p_limit:1,...(direct?{p_event:env.DEFECTRAG_EMAIL_SANDBOX==='1'?env.DEFECTRAG_EMAIL_QA_EVENT_ID:null}:{})});
  if(!Array.isArray(jobs)||jobs.length>1)throw new Error('invalid_outbox_response');
  if(!jobs.length)break;
  const job=jobs[0];result.claimed++;
  if(processed.has(job.event_id))throw new Error('duplicate_outbox_response');
  processed.add(job.event_id);
  let accepted=false,error='delivery_failed';
  if(!safeJob(job)){
   // Only acknowledge identifiable leased rows. No arbitrary database IDs.
   if(!UUID.test(job.event_id)||!UUID.test(job.lease_token))throw new Error('invalid_outbox_response');
   error='invalid_notification';
  }else{
   try{
    if(direct){
     // Persist the exact provider body BEFORE dispatch. Retries reuse the same
     // body/key; SQL quarantines ambiguity after 23h, within provider's 24h TTL.
     const proposed=emailMessage(job,env);
     const prepared=await rpc('defectrag_prepare_email',{p_id:job.event_id,p_lease:job.lease_token,p_payload:proposed});
     if(!prepared||typeof prepared.payload!=='object'||prepared.payload===null)throw new Error('email_quarantined');
     const response=await boundedJson(hook,{method:'POST',headers:{'Content-Type':'application/json',
      Authorization:'Bearer '+env.DEFECTRAG_RESEND_API_KEY,'Idempotency-Key':'defectrag/'+job.event_id},
      body:JSON.stringify(prepared.payload),redirect:'error'},LIMITS.webhookMs);
     accepted=response.ok&&typeof response.body?.id==='string'&&response.body.id.length>0;
     error=response.ok?'invalid_receipt':'notification_http_'+response.status;
    }else{
    // Explicit allowlist: never forward the lease, keys, JWT, images or records.
    const payload={event_id:job.event_id,request_id:job.request_id,version:job.version,kind:job.kind,
     recipient_email:job.recipient_email,display_name:job.display_name,
     ...(job.kind==='requested'?{applicant_email:job.applicant_email}:{})};
    const response=await boundedJson(hook,{method:'POST',headers:{'Content-Type':'application/json',
     'X-DefectRAG-Webhook-Key':env.DEFECTRAG_N8N_WEBHOOK_SECRET,'X-DefectRAG-Event-ID':job.event_id,
     'Idempotency-Key':job.event_id},body:JSON.stringify(payload),redirect:'error'},LIMITS.webhookMs);
    if(response.ok){const receipt=response.body;accepted=receipt.delivered===true&&receipt.event_id===job.event_id;error='invalid_receipt'}
    else error='notification_http_'+response.status;
    }
   }catch{error='notification_unavailable'}
  }
  const finished=await rpc('defectrag_finish_notification',{p_id:job.event_id,p_lease:job.lease_token,p_delivered:accepted,p_error:accepted?'':error});
  if(finished!==true)result.leaseLost++;else if(accepted)result.accepted++;else result.retried++;
 }
 return result;
}
export async function handleRequest(request,{env,fetcher=fetch,...timing}){
 if(request.method!=='POST')return json({error:'method_not_allowed'},405);
 // Explicit diagnostic mode can NEVER fall through to dispatch, even if malformed.
 // Require the dedicated bearer and delivery0; expose booleans, never env values.
 const expectedEvent=request.headers.get('X-DefectRAG-Check-Event');
 if(expectedEvent!==null){
  if(!env.DEFECTRAG_NOTIFICATION_WORKER_SECRET||env.DEFECTRAG_NOTIFICATION_WORKER_SECRET.length<32
   ||!sameSecret(request.headers.get('Authorization'),'Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET))return json({error:'unauthorized'},401);
  if(env.DEFECTRAG_NOTIFICATIONS_ENABLED!=='0')return json({error:'diagnostics_require_delivery_disabled'},409);
  if(!UUID.test(expectedEvent))return json({error:'invalid_diagnostic_event'},400);
  return json(configurationCheck(env,expectedEvent));
 }
 if(env.DEFECTRAG_NOTIFICATIONS_ENABLED!=='1')return json({error:'notifications_disabled'},503);
 if(!env.DEFECTRAG_NOTIFICATION_WORKER_SECRET||env.DEFECTRAG_NOTIFICATION_WORKER_SECRET.length<32
  ||!sameSecret(request.headers.get('Authorization'),'Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET))return json({error:'unauthorized'},401);
 try{return json(await dispatchNotifications({env,fetcher,...timing}))}catch{return json({error:'dispatch_unavailable'},503)}
}
