// Local operator console only. Uses the existing native Developer SDK session.
// No privileged key, automatic writes, account approvals, lease reads or emails.
import {QA_DESCRIPTION,inspectSinkCase,advanceSinkCase,prepareReplacementEvent,prepareExpiredUnclaimedEvent} from './sink-lifecycle.mjs';
const $=id=>document.getElementById(id),cfg=window.DEFECTRAG_PUBLIC_CONFIG||{};
if(cfg.supabaseUrl!=='https://zrzqpbcomlorfzszolrs.supabase.co')throw Error('Intended project required');
let publicKey=cfg.supabasePublishableKey?.startsWith('sb_publishable_');
if(!publicKey){try{publicKey=JSON.parse(atob(cfg.supabasePublishableKey.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).role==='anon'}catch{}}
if(!publicKey)throw Error('Public key only');
const c=window.supabase.createClient(cfg.supabaseUrl,cfg.supabasePublishableKey,{auth:{storageKey:'defectrag-ca-live-developer',detectSessionInUrl:false}});
const key='defectrag-ca-single-sink-plan-v1';let plan=JSON.parse(localStorage.getItem(key)||'{}');
const save=()=>localStorage.setItem(key,JSON.stringify(plan));
const check=(b,message)=>{if(!b)throw Error(message)};
const ok=async promise=>{const r=await promise;if(r.error)throw Error('API_'+(r.error.code||r.error.status||'failure'));return r.data};
async function developer(){
 const user=(await c.auth.getUser()).data.user;check(user,'Complete Developer sign-in/MFA on the account page');
 const p=await ok(c.rpc('defectrag_auth_status'));check(p.role==='developer'&&p.approved&&p.authorized&&p.aal2,'Existing approved Developer with native TOTP AAL2 required');
 check(await ok(c.rpc('defectrag_ca_qa_readiness'))===true,'Keep global automation OFF');return user;
}
async function run(action){
 document.querySelectorAll('button').forEach(b=>b.disabled=true);
 try{const r=await action();$('result').textContent=JSON.stringify(r,null,2)}
 catch(e){$('result').textContent=String(e.message).slice(0,180)}
 finally{document.querySelectorAll('button').forEach(b=>b.disabled=false)}
}
$('status').onclick=()=>run(async()=>{await developer();$('posture').textContent='Developer MFA verified; global automation OFF.';return {ready:true}});
$('inspection').value=plan.inspection||'';
$('prepare').onclick=()=>run(async()=>{
 const user=await developer();check($('confirm').checked,'Explicit disposable QA confirmation required');
 const id=$('inspection').value.trim();check(/^[0-9a-f]{32}$/.test(id),'Exact QA inspection ID required');
 check(!plan.inspection||plan.inspection===id,'Do not replace an existing QA plan');
 const inspection=await ok(c.from('shared_inspections').select('payload,archived_at').eq('id',id).single());
 check(!inspection.archived_at&&inspection.payload?.model_id==='QA-SYNTHETIC-NO-INFERENCE','Only the known synthetic QA fixture is permitted');
 plan.inspection=id;save();
 if(!plan.review_id){const row=await ok(c.from('staff_notes').insert({inspection_id:id,author_id:user.id,body:'DEFECTRAG_REVIEW_V1:'+JSON.stringify({status:'Reviewed',decision:'Reject',note:'Synthetic sink-only QA attestation, not a real defect diagnosis.'})}).select('id').single());plan.review_id=row.id;save()}
 const found=await ok(c.from('corrective_actions').select('id,confirmed_by').eq('review_id',plan.review_id));
 if(found.length){check(found[0].confirmed_by===user.id,'QA plan belongs to another Developer');plan.case_id=found[0].id}
 else plan.case_id=await ok(c.rpc('defectrag_create_corrective_action',{p_inspection:id,p_review:plan.review_id,p_confirmed:true,p_owner:user.id,p_supervisor:user.id,p_priority:'Normal',p_description:QA_DESCRIPTION,p_due:new Date(Date.now()+86400000).toISOString()}));
 save();
 const event=await ok(c.from('corrective_action_events').select('id,status,attempts').eq('case_id',plan.case_id).eq('version',1).eq('kind','created').single());
 check(event.status==='queued'&&event.attempts===0,'Existing event already attempted; do not reset');plan.event_id=event.id;save();
 return {prepared:true,case_id:plan.case_id,event_id:plan.event_id,status:event.status,attempts:event.attempts,approved_for_qa:false};
});
$('approve').onclick=()=>run(async()=>{
 await developer();check(plan.event_id&&$('confirm').checked,'Review the prepared disposable event and confirm first');
 await ok(c.rpc('defectrag_ca_qa_approve',{p_event:plan.event_id,p_confirm_disposable:true}));
 return {event_id:plan.event_id,qa_authorization:'Approved for 15 minutes; one claim; local sink only',staff_permissions_changed:false};
});
$('revoke').onclick=()=>run(async()=>{
 await developer();check(plan.event_id,'Exact prepared QA event required');
 await ok(c.rpc('defectrag_ca_qa_revoke',{p_event:plan.event_id}));return {event_id:plan.event_id,qa_authorization:'Revoked; no Staff membership changed'};
});
$('lifecycle-status').onclick=()=>run(async()=>{
 const user=await developer(),s=await inspectSinkCase(c,plan,user.id);
 return {case_id:s.row.id,state:s.row.state,version:s.row.version,sink_complete:s.sink_complete,
  resolved_timestamp_present:!!s.row.resolved_at,closed_timestamp_present:!!s.row.closed_at,
  history:s.history.map(h=>({version:h.version,state:h.state,actor_is_current_developer:h.actor_id===user.id})),
  events:s.events.map(e=>({id:e.id,version:e.version,kind:e.kind,status:e.status,attempts:e.attempts}))};
});
$('lifecycle-next').onclick=()=>run(async()=>{
 const user=await developer();return advanceSinkCase(c,plan,user.id,$('lifecycle-state').value);
});
$('replacement').onclick=()=>run(async()=>{
 const user=await developer();check($('replacement-confirm').checked,'Separate owner approval for one replacement sink attempt is required');
 return prepareReplacementEvent(c,plan,user.id,save);
});
$('expiry-recovery').onclick=()=>run(async()=>{
 const user=await developer();check($('expiry-confirm').checked,'Separate owner approval for the exact unused expired event is required');
 return prepareExpiredUnclaimedEvent(c,plan,user.id,save);
});
