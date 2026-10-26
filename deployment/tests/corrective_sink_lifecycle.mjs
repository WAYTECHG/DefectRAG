// Temporary loopback QA tooling only. No secrets, direct writes or auto-retries.
export const QA_DESCRIPTION='QA sink-only disposable callback verification; no real product diagnosis.';
const next={Open:'Assigned',Assigned:'In Progress','In Progress':'Resolved',Resolved:'Closed'};
const check=(value,message)=>{if(!value)throw Error(message)};
const ok=async promise=>{const r=await promise;if(r.error)throw Error('API_'+(r.error.code||'failure'));return r.data};
export async function inspectSinkCase(c,plan,userId){
 check(plan.case_id&&plan.review_id&&plan.inspection&&plan.event_id,'Prepare the new QA case first');
 const row=await ok(c.from('corrective_actions').select('id,inspection_id,review_id,confirmed_by,description,state,version,resolved_at,closed_at').eq('id',plan.case_id).single());
 check(row.id===plan.case_id&&row.inspection_id===plan.inspection&&row.review_id===plan.review_id&&row.confirmed_by===userId&&row.description===QA_DESCRIPTION,'Only this Developer-confirmed disposable QA case is permitted');
 const events=await ok(c.from('corrective_action_events').select('id,case_id,version,kind,status,attempts').eq('case_id',row.id).order('version'));
 const created=events.find(e=>e.id===plan.event_id&&e.case_id===row.id&&e.version===(plan.event_version||1)&&e.kind===(plan.event_kind||'created'));
 check(created,'Exact planned QA event required');
 const effects=await ok(c.from('corrective_action_effects').select('event_id,effect,state').eq('event_id',plan.event_id));
 const history=await ok(c.from('corrective_action_history').select('version,state,actor_id,created_at').eq('case_id',row.id).order('version'));
 return {row,events,history,effects,sink_complete:created.status==='sent'&&effects.some(e=>e.effect==='notification'&&e.state==='done')};
}
export async function prepareReplacementEvent(c,plan,userId,persist){
 check(!plan.replacement_prepared,'Only one separately approved replacement is supported');
 const before=await inspectSinkCase(c,plan,userId),old=before.events.find(e=>e.id===plan.event_id);
 const grant=await ok(c.from('corrective_action_qa_runs').select('event_id,finished_at').eq('event_id',plan.event_id).single());
 check(old.status==='dead'&&old.attempts===1&&before.effects.length===0&&grant.finished_at&&before.row.state==='Open',
  'Reconcile the failed no-effect run first; never replace a pending, sent or ambiguous run');
 if(!plan.pending_replacement){plan.pending_replacement={from:before.row.version,to:before.row.version+1,
  note:'QA callback authentication corrected; separately approved replacement sink event '+crypto.randomUUID()};persist()}
 const intent=plan.pending_replacement;
 if(before.row.version===intent.from){
  const version=await ok(c.rpc('defectrag_update_corrective_action',{p_id:plan.case_id,p_version:intent.from,p_state:'Open',p_note:intent.note}));
  check(version===intent.to,'Uncertain replacement; inspect status before continuing');
 }else{
  check(before.row.version===intent.to,'Case changed outside the replacement intent');
  const audit=await ok(c.from('corrective_action_history').select('note,actor_id').eq('case_id',plan.case_id).eq('version',intent.to).single());
  check(audit.note===intent.note&&audit.actor_id===userId,'Replacement response cannot be recovered safely');
 }
 const event=await ok(c.from('corrective_action_events').select('id,status,attempts').eq('case_id',plan.case_id).eq('version',intent.to).eq('kind','updated').single());
 check(event.status==='queued'&&event.attempts===0,'Replacement event already attempted; never reset');
 plan.previous_event_id=plan.event_id;plan.event_id=event.id;plan.event_version=intent.to;plan.event_kind='updated';plan.replacement_prepared=true;persist();
 return {case_id:plan.case_id,event_id:plan.event_id,version:intent.to,kind:'updated',status:'queued',attempts:0,
  original_event_preserved:true,new_case_created:false,qa_grant_issued:false};
}
export async function advanceSinkCase(c,plan,userId,target){
 const before=await inspectSinkCase(c,plan,userId);
 check(before.sink_complete,'Complete and reconcile the one-event sink test before lifecycle changes');
 check(next[before.row.state]===target,'Choose only the next lifecycle state; closed cases cannot be reopened');
 const expectedVersion=before.row.version;
 const version=await ok(c.rpc('defectrag_update_corrective_action',{p_id:before.row.id,p_version:expectedVersion,p_state:target,p_note:'QA lifecycle '+target+'; synthetic verification only.'}));
 check(version===expectedVersion+1,'Uncertain update; read status before any further action');
 return {case_id:before.row.id,state:target,version,notification_sent_by_this_action:false,staff_permissions_changed:false};
}

// One owner-approved recovery of the exact expired, NEVER claimed replacement.
// Creates a new audit version through the existing RPC; never resets a grant.
export async function prepareExpiredUnclaimedEvent(c,plan,userId,persist,now=Date.now()){
 check(!plan.expired_recovery_prepared,'Only one separately approved expiry recovery is supported');
 check(plan.case_id==='fb462978-af2b-4b4f-a280-2c9803dc4bb1'&&plan.event_id==='5f58829c-e8ca-42ba-ad8d-0ec5cc0b09d8'&&plan.event_version===2,
  'Only the exact owner-approved expired QA event is permitted');
 const before=await inspectSinkCase(c,plan,userId),old=before.events.find(e=>e.id===plan.event_id);
 const grant=await ok(c.from('corrective_action_qa_runs').select('event_id,expires_at,claimed_at,finished_at,revoked_at').eq('event_id',plan.event_id).single());
 check(old.status==='queued'&&old.attempts===0&&before.effects.length===0&&before.row.state==='Open'&&grant?.event_id===plan.event_id&&
  Number.isFinite(Date.parse(grant.expires_at))&&Date.parse(grant.expires_at)<=now&&!grant.claimed_at&&!grant.finished_at&&!grant.revoked_at,
  'Require the expired, unclaimed, unfinished, unrevoked zero-effect event; never retry a send');
 if(!plan.pending_expired_recovery){
  check(before.row.version===2,'Case changed before expiry recovery');
  plan.pending_expired_recovery={from:2,to:3,note:'QA unused grant expired; separately approved fresh sink-only event '+crypto.randomUUID()};persist();
 }
 const intent=plan.pending_expired_recovery;
 check(intent.from===2&&intent.to===3&&typeof intent.note==='string'&&intent.note.startsWith('QA unused grant expired; separately approved fresh sink-only event '),'Exact recovery intent required');
 if(before.row.version===intent.from){
  const version=await ok(c.rpc('defectrag_update_corrective_action',{p_id:plan.case_id,p_version:intent.from,p_state:'Open',p_note:intent.note}));
  check(version===intent.to,'Uncertain expiry recovery; inspect status before continuing');
 }else{
  check(before.row.version===intent.to,'Case changed outside expiry recovery');
  const audit=await ok(c.from('corrective_action_history').select('note,actor_id').eq('case_id',plan.case_id).eq('version',intent.to).single());
  check(audit.note===intent.note&&audit.actor_id===userId,'Expiry recovery response cannot be recovered safely');
 }
 const event=await ok(c.from('corrective_action_events').select('id,status,attempts').eq('case_id',plan.case_id).eq('version',intent.to).eq('kind','updated').single());
 check(event?.status==='queued'&&event.attempts===0,'Fresh recovery event already attempted; never reset');
 plan.expired_event_id=plan.event_id;plan.event_id=event.id;plan.event_version=intent.to;plan.event_kind='updated';plan.expired_recovery_prepared=true;persist();
 return {case_id:plan.case_id,event_id:event.id,version:intent.to,status:event.status,attempts:0,earlier_events_preserved:true,new_case_created:false,qa_grant_issued:false};
}
