import test from 'node:test';
import assert from 'node:assert/strict';
import {handleCAQA} from '../../deployment/supabase/functions/corrective-actions-qa/worker.mjs';
const event='11111111-1111-4111-8111-111111111111',lease='22222222-2222-4222-8222-222222222222',caseId='33333333-3333-4333-8333-333333333333';
const env={DEFECTRAG_CA_QA_ENABLED:'1',DEFECTRAG_CA_QA_EVENT_ID:event,DEFECTRAG_CA_QA_WORKER_SECRET:'W'.repeat(40),DEFECTRAG_CA_QA_CALLBACK_SECRET:'C'.repeat(40),SUPABASE_URL:'https://zrzqpbcomlorfzszolrs.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'SERVER-ONLY-FIXTURE'};
const request=(op='claim',body={event_id:event},key=op==='effect'?env.DEFECTRAG_CA_QA_CALLBACK_SECRET:env.DEFECTRAG_CA_QA_WORKER_SECRET)=>new Request('https://fixture.invalid',{method:'POST',headers:{Authorization:'Bearer '+key,'X-DefectRAG-Operation':op},body:JSON.stringify(body)});
const no=()=>assert.fail('No outbound call allowed');
test('QA default disabled, independent from production flag',async()=>{
 assert.equal((await handleCAQA(request(),{fetcher:no})).status,503);
 assert.equal((await handleCAQA(request(),{env:{...env,DEFECTRAG_CA_QA_ENABLED:undefined,DEFECTRAG_CA_AUTOMATION_ENABLED:'1'},fetcher:no})).status,503);
 assert.equal((await handleCAQA(request(),{env:{...env,DEFECTRAG_CA_QA_CALLBACK_SECRET:env.DEFECTRAG_CA_QA_WORKER_SECRET},fetcher:no})).status,503);
});
test('wrong role key, wrong event and foreign project rejected before RPC',async()=>{
 assert.equal((await handleCAQA(request('effect',{event_id:event},env.DEFECTRAG_CA_QA_WORKER_SECRET),{env,fetcher:no})).status,401);
 assert.equal((await handleCAQA(request('claim',{event_id:lease}),{env,fetcher:no})).status,403);
 assert.equal((await handleCAQA(request(),{env:{...env,SUPABASE_URL:'https://other.invalid'},fetcher:no})).status,503);
});
test('strict body/size and receipt validation',async()=>{
 for(const b of [{event_id:event,table:'staff_members'},{event_id:event,pad:'x'.repeat(3000)}])assert.equal((await handleCAQA(request('claim',b),{env,fetcher:no})).status,400);
 assert.equal((await handleCAQA(request('effect',{event_id:event,lease_token:lease,operation:'finish',receipt:'bad\nreceipt'}),{env,fetcher:no})).status,400);
});
test('claim targets exactly one QA RPC and projects capability only',async()=>{
 let calls=0;
 const r=await handleCAQA(request(),{env,fetcher:async(url,o)=>{
  calls++;assert.ok(url.endsWith('/defectrag_ca_qa_claim'));assert.deepEqual(JSON.parse(o.body),{p_event:event});assert.equal(o.redirect,'error');
  return Response.json({event_id:event,lease_token:lease,case_id:caseId,kind:'created',version:1,private:'DO NOT FORWARD'});
 }});
 const body=await r.json();assert.equal(calls,1);assert.deepEqual(Object.keys(body).sort(),['case_id','event_id','kind','lease_token','version']);assert.ok(!JSON.stringify(body).includes('SERVER-ONLY'));
});
test('QA effect can only return reserved sink recipient and safe metadata',async()=>{
 const r=await handleCAQA(request('effect',{event_id:event,lease_token:lease,operation:'begin'}),{env,fetcher:async(url,o)=>{
  assert.ok(url.endsWith('/defectrag_ca_qa_effect'));assert.equal(JSON.parse(o.body).p_finish,false);
  return Response.json({execute:true,done:false,recipient_email:'private@private.invalid',cc_email:'owner@private.invalid',case_id:caseId,kind:'created',state:'Open',priority:'High',due_at:'2030-01-01T00:00:00Z',image:'private'});
 }});
 const b=await r.json();assert.equal(b.recipient_email,'supervisor@example.invalid');assert.ok(!JSON.stringify(b).includes('private'));assert.ok(!('cc_email' in b),'QA never forwards a copy address');
});
test('finish and ambiguity are projected without new send; failures are sanitized',async()=>{
 const r=await handleCAQA(request('effect',{event_id:event,lease_token:lease,operation:'begin'}),{env,fetcher:async()=>Response.json({done:false,execute:false,manual_review:true,private:'secret'})});
 assert.deepEqual(await r.json(),{done:false,execute:false,manual_review:true});
 const denied=await handleCAQA(request(),{env,fetcher:async()=>{throw Error('sensitive backend response')}});
 assert.deepEqual(await denied.json(),{error:'qa_request_denied_or_unavailable'});
});
test('finalize forwards authoritative boolean, no fabricated success',async()=>{
 const r=await handleCAQA(request('finalize',{event_id:event,lease_token:lease,completed:false}),{env,fetcher:async(url,o)=>{
  assert.ok(url.endsWith('/defectrag_ca_qa_finish'));assert.equal(JSON.parse(o.body).p_success,false);return Response.json(false);
 }});assert.deepEqual(await r.json(),{acknowledged:false});
});
