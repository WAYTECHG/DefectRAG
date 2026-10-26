import test from 'node:test';
import assert from 'node:assert/strict';
import {QA_DESCRIPTION,advanceSinkCase,inspectSinkCase,prepareReplacementEvent,prepareExpiredUnclaimedEvent} from './corrective_sink_lifecycle.mjs';
const plan={case_id:'new-qa',inspection:'synthetic',review_id:'review',event_id:'event'};
function fixture(overrides={}){
 const calls=[],row={id:'new-qa',inspection_id:'synthetic',review_id:'review',confirmed_by:'dev',description:QA_DESCRIPTION,state:'Open',version:1,...overrides};
 const tables={corrective_actions:row,corrective_action_events:[{id:'event',case_id:'new-qa',version:1,kind:'created',status:'sent',attempts:1}],corrective_action_effects:[{event_id:'event',effect:'notification',state:'done'}],corrective_action_history:[{version:1,state:'Open'}]};
 const c={from(name){const q={select(){return q},eq(){return q},single(){return Promise.resolve({data:tables[name]})},order(){return Promise.resolve({data:tables[name]})},then(resolve){return Promise.resolve({data:tables[name]}).then(resolve)}};return q},async rpc(name,args){calls.push({name,args});return {data:row.version+1}}};
 return {c,calls,tables};
}
test('one version-checked transition has no assignment/permission or email parameters',async()=>{
 const f=fixture();assert.equal((await advanceSinkCase(f.c,plan,'dev','Assigned')).version,2);
 assert.deepEqual(Object.keys(f.calls[0].args).sort(),['p_id','p_note','p_state','p_version']);
 assert.equal(f.calls[0].name,'defectrag_update_corrective_action');
});
test('another case, review, owner attestation or description cannot be used',async()=>{
 for(const override of [{id:'old-case'},{review_id:'old-review'},{confirmed_by:'someone-else'},{description:'Production case'}]){
  const f=fixture(override);await assert.rejects(advanceSinkCase(f.c,plan,'dev','Assigned'));assert.equal(f.calls.length,0);
 }
});
test('skipped, repeated and terminal transitions never submit another mutation',async()=>{
 for(const [state,target] of [['Open','Closed'],['Assigned','Assigned'],['Closed','In Progress']]){
  const f=fixture({state});await assert.rejects(advanceSinkCase(f.c,plan,'dev',target));assert.equal(f.calls.length,0);
 }
});
test('delivery must be sent and its actual effect done before lifecycle mutation',async()=>{
 for(const broken of ['event','effect']){const f=fixture();if(broken==='event')f.tables.corrective_action_events[0].status='dead';else f.tables.corrective_action_effects[0].state='uncertain';await assert.rejects(advanceSinkCase(f.c,plan,'dev','Assigned'));assert.equal(f.calls.length,0)}
});
test('read status never invokes a write and rejects a mismatched original event',async()=>{
 const f=fixture();assert.equal((await inspectSinkCase(f.c,plan,'dev')).sink_complete,true);assert.equal(f.calls.length,0);
 f.tables.corrective_action_events[0].id='other-event';await assert.rejects(inspectSinkCase(f.c,plan,'dev'));
});
function replacementFixture(){
 const f=fixture(),row=f.tables.corrective_actions,calls=[],p={...plan};
 const t={...f.tables,corrective_action_events:[{id:'event',case_id:'new-qa',version:1,kind:'created',status:'dead',attempts:1}],
  corrective_action_effects:[],corrective_action_history:[],corrective_action_qa_runs:{event_id:'event',finished_at:'fixture-finished'}};
 let loseResponse=false;
 const c={from(name){const filters=[];const data=()=>{const v=t[name];return Array.isArray(v)?v.filter(e=>filters.every(([k,x])=>e[k]===x)):v};const q={select(){return q},eq(k,v){filters.push([k,v]);return q},single(){const v=data();return Promise.resolve({data:Array.isArray(v)?v[0]:v})},order(){return Promise.resolve({data:data()})},then(resolve){return Promise.resolve({data:data()}).then(resolve)}};return q},async rpc(name,args){
  calls.push({name,args});assert.equal(args.p_version,row.version);row.version++;row.state=args.p_state;
  t.corrective_action_events.push({id:'replacement-'+row.version,case_id:row.id,version:row.version,kind:'updated',status:'queued',attempts:0});
  t.corrective_action_history.push({case_id:row.id,version:row.version,note:args.p_note,actor_id:'dev',state:row.state});
  if(loseResponse){loseResponse=false;return {error:{code:'LOST_FIXTURE_RESPONSE'}}}return {data:row.version};
 }};
 return {c,t,p,calls,persist:()=>{},loseNextResponse:()=>{loseResponse=true}};
}
test('replacement creates one versioned event on the same case, never resets old grant/event',async()=>{
 const f=replacementFixture(),old=JSON.stringify(f.t.corrective_action_events[0]);
 const r=await prepareReplacementEvent(f.c,f.p,'dev',f.persist);
 assert.equal(r.new_case_created,false);assert.equal(r.qa_grant_issued,false);assert.equal(r.version,2);
 assert.equal(f.p.case_id,plan.case_id);assert.equal(f.p.event_kind,'updated');
 assert.equal(JSON.stringify(f.t.corrective_action_events[0]),old);assert.equal(f.calls.length,1);
 await assert.rejects(prepareReplacementEvent(f.c,f.p,'dev',f.persist));assert.equal(f.calls.length,1);
});
test('queued, sent, ambiguous and unfinished attempts cannot generate a replacement',async()=>{
 for(const mode of ['queued','sent','effect','unfinished']){const f=replacementFixture();
  if(mode==='effect')f.t.corrective_action_effects.push({event_id:'event',state:'uncertain'});
  else if(mode==='unfinished')f.t.corrective_action_qa_runs.finished_at=null;
  else f.t.corrective_action_events[0].status=mode;
  await assert.rejects(prepareReplacementEvent(f.c,f.p,'dev',f.persist));assert.equal(f.calls.length,0);
 }
});
test('lost version-update response recovers its exact audit intent without a second write',async()=>{
 const f=replacementFixture();f.loseNextResponse();await assert.rejects(prepareReplacementEvent(f.c,f.p,'dev',f.persist));
 assert.equal(f.calls.length,1);assert.equal(f.p.event_id,'event');
 assert.equal((await prepareReplacementEvent(f.c,f.p,'dev',f.persist)).version,2);assert.equal(f.calls.length,1);
});
test('lost response cannot recover an audit record written by another actor',async()=>{
 const f=replacementFixture();f.loseNextResponse();await assert.rejects(prepareReplacementEvent(f.c,f.p,'dev',f.persist));
 f.t.corrective_action_history[0].actor_id='other';await assert.rejects(prepareReplacementEvent(f.c,f.p,'dev',f.persist));assert.equal(f.calls.length,1);
});
test('lifecycle accepts only the exact successful replacement event/version',async()=>{
 const f=replacementFixture();await prepareReplacementEvent(f.c,f.p,'dev',f.persist);
 f.t.corrective_action_events[1].status='sent';f.t.corrective_action_effects.push({event_id:f.p.event_id,effect:'notification',state:'done'});
 assert.equal((await inspectSinkCase(f.c,f.p,'dev')).sink_complete,true);
 assert.equal((await advanceSinkCase(f.c,f.p,'dev','Assigned')).version,3);
});

function expiredFixture(){
 const f=replacementFixture(),caseId='fb462978-af2b-4b4f-a280-2c9803dc4bb1',eventId='5f58829c-e8ca-42ba-ad8d-0ec5cc0b09d8';
 Object.assign(f.p,{case_id:caseId,event_id:eventId,event_version:2,event_kind:'updated',replacement_prepared:true});
 Object.assign(f.t.corrective_actions,{id:caseId,version:2});
 Object.assign(f.t.corrective_action_events[0],{id:eventId,case_id:caseId,version:2,kind:'updated',status:'queued',attempts:0});
 f.t.corrective_action_qa_runs={event_id:eventId,expires_at:'2026-10-25T00:00:00Z',claimed_at:null,finished_at:null,revoked_at:null};
 return f;
}
const recoveryNow=Date.parse('2026-10-26T00:00:00Z');
test('expired unused recovery preserves the old event and grant, creates no grant or new case',async()=>{
 const f=expiredFixture(),oldEvent=JSON.stringify(f.t.corrective_action_events[0]),oldGrant=JSON.stringify(f.t.corrective_action_qa_runs);
 const r=await prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow);
 assert.equal(r.version,3);assert.equal(r.qa_grant_issued,false);assert.equal(r.new_case_created,false);
 assert.equal(JSON.stringify(f.t.corrective_action_events[0]),oldEvent);assert.equal(JSON.stringify(f.t.corrective_action_qa_runs),oldGrant);
 assert.equal(f.calls.length,1);assert.deepEqual(Object.keys(f.calls[0].args).sort(),['p_id','p_note','p_state','p_version']);
 await assert.rejects(prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow));assert.equal(f.calls.length,1);
});
test('recovery denies unexpired, claimed, finished, revoked, attempted or ambiguous events',async()=>{
 for(const mode of ['future','invalid-date','claimed','finished','revoked','attempted','sent','effect','case','event','version']){
  const f=expiredFixture(),g=f.t.corrective_action_qa_runs;
  if(mode==='future')g.expires_at='2026-10-27T00:00:00Z';
  if(mode==='invalid-date')g.expires_at='invalid';
  if(mode==='claimed')g.claimed_at='present';if(mode==='finished')g.finished_at='present';if(mode==='revoked')g.revoked_at='present';
  if(mode==='attempted')f.t.corrective_action_events[0].attempts=1;if(mode==='sent')f.t.corrective_action_events[0].status='sent';
  if(mode==='effect')f.t.corrective_action_effects.push({event_id:f.p.event_id,state:'uncertain'});
  if(mode==='case')f.p.case_id='another';if(mode==='event')f.p.event_id='another';if(mode==='version')f.t.corrective_actions.version=4;
  await assert.rejects(prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow),mode);assert.equal(f.calls.length,0,mode);
 }
});
test('expired recovery reconciles a lost response without another version write',async()=>{
 const f=expiredFixture();f.loseNextResponse();await assert.rejects(prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow));
 assert.equal(f.calls.length,1);assert.equal((await prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow)).version,3);assert.equal(f.calls.length,1);
});
test('expired recovery rejects changed audit attribution after a lost response',async()=>{
 const f=expiredFixture();f.loseNextResponse();await assert.rejects(prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow));
 f.t.corrective_action_history[0].actor_id='other';await assert.rejects(prepareExpiredUnclaimedEvent(f.c,f.p,'dev',f.persist,recoveryNow));assert.equal(f.calls.length,1);
});
