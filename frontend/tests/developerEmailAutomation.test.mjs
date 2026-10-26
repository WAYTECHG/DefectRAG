import test from 'node:test';
import assert from 'node:assert/strict';
import {emailMessage,emailConfiguration} from '../../deployment/supabase/functions/staff-notifications/direct-email.mjs';
import {handleRequest} from '../../deployment/supabase/functions/staff-notifications/worker.mjs';
const job={event_id:'11111111-1111-4111-8111-111111111111',lease_token:'22222222-2222-4222-8222-222222222222',request_id:'33333333-3333-4333-8333-333333333333',kind:'requested',version:1,display_name:'QA',applicant_email:'applicant@example.invalid',recipient_email:'developer@example.invalid',requested_at:'2026-10-22T00:00:00Z'};
const env={DEFECTRAG_NOTIFICATIONS_ENABLED:'1',DEFECTRAG_NOTIFICATION_WORKER_SECRET:'w'.repeat(32),SUPABASE_URL:'https://db.example.invalid',SUPABASE_SERVICE_ROLE_KEY:'fixture-service',DEFECTRAG_NOTIFICATION_TRANSPORT:'resend',DEFECTRAG_RESEND_API_KEY:'fixture-provider',DEFECTRAG_EMAIL_FROM:'onboarding@resend.dev',DEFECTRAG_EMAIL_SANDBOX:'0',DEFECTRAG_EMAIL_DEVELOPER_ONLY:'1',DEFECTRAG_EMAIL_QA_RECIPIENT:job.recipient_email};
const request=(key=env.DEFECTRAG_NOTIFICATION_WORKER_SECRET)=>new Request('https://fixture.invalid',{method:'POST',headers:{Authorization:'Bearer '+key}});

test('automatic developer mode handles new event IDs without unlocking arbitrary recipients',()=>{
 assert.equal(emailConfiguration(env).developerOnly,true);
 const other={...job,event_id:'44444444-4444-4444-8444-444444444444'};
 assert.equal(emailMessage(other,env).to[0],job.recipient_email);
 for(const kind of ['approved','rejected','revoked'])assert.throws(()=>emailMessage({...job,kind},env));
 assert.throws(()=>emailMessage({...job,recipient_email:'outsider@example.invalid'},env));
 assert.equal(emailMessage({...job,recipient_email:job.recipient_email.toUpperCase()},env).to.length,1);
});
for(const changes of [
 {DEFECTRAG_EMAIL_SANDBOX:'1'}, {DEFECTRAG_EMAIL_QA_RECIPIENT:''},
 {DEFECTRAG_EMAIL_FROM:'notify@example.invalid'}, {DEFECTRAG_EMAIL_DEVELOPER_ONLY:'true'},
 {DEFECTRAG_NOTIFICATION_TRANSPORT:'n8n'}
])test('invalid automatic mode fails closed before any claim '+JSON.stringify(Object.keys(changes)),async()=>{
 const r=await handleRequest(request(),{env:{...env,...changes},fetcher:()=>assert.fail('No network allowed')});
 assert.equal(r.status,503);
});
test('disabled and unauthorized automatic workers never contact database/provider',async()=>{
 assert.equal((await handleRequest(request(),{env:{...env,DEFECTRAG_NOTIFICATIONS_ENABLED:'0'},fetcher:()=>assert.fail()})).status,503);
 assert.equal((await handleRequest(request('wrong'),{env,fetcher:()=>assert.fail()})).status,401);
});
function fixture({jobOverride,providerFailure=false,ackFailure=false}={}){
 let leased=false,finished=false;const calls=[];
 return {calls,resetLease:()=>{leased=false},fetcher:async(url,options)=>{
  const b=JSON.parse(options.body);calls.push({url,body:b,headers:options.headers});
  if(url.endsWith('/defectrag_claim_developer_notifications')){
   assert.deepEqual(b,{p_recipient:env.DEFECTRAG_EMAIL_QA_RECIPIENT});
   if(leased||finished)return Response.json([]);leased=true;return Response.json([{...job,...jobOverride}]);
  }
  if(url.endsWith('/defectrag_prepare_email'))return Response.json({payload:b.p_payload});
  if(url.endsWith('/defectrag_finish_notification')){if(ackFailure)throw Error('lost acknowledgment');finished=b.p_delivered;return Response.json(true)}
  assert.equal(url,'https://api.resend.com/emails');
  assert.equal(options.headers['Idempotency-Key'],'defectrag/'+job.event_id);
  return providerFailure?new Response('',{status:429}):Response.json({id:'receipt'});
 }};
}
test('automatic worker uses filtered RPC and immutable snapshot, not unrestricted outbox claim',async()=>{
 const f=fixture();assert.deepEqual(await (await handleRequest(request(),{env,fetcher:f.fetcher})).json(),{claimed:1,accepted:1,retried:0,leaseLost:0});
 assert.equal(f.calls.filter(c=>c.url.endsWith('/defectrag_prepare_email')).length,1);
 assert.equal(f.calls.filter(c=>c.url.includes('api.resend')).length,1);
 assert.ok(!f.calls.some(c=>c.url.endsWith('/defectrag_claim_direct_notifications')));
 f.resetLease();await handleRequest(request(),{env,fetcher:f.fetcher});
 assert.equal(f.calls.filter(c=>c.url.includes('api.resend')).length,1);
});
for(const jobOverride of [{kind:'approved'},{recipient_email:'outsider@example.invalid'}])test('unexpected database job cannot reach email provider',async()=>{
 const f=fixture({jobOverride});const body=await (await handleRequest(request(),{env,fetcher:f.fetcher})).json();
 assert.equal(body.accepted,0);assert.equal(f.calls.filter(c=>c.url.includes('api.resend')).length,0);
 assert.equal(f.calls.filter(c=>c.url.endsWith('/defectrag_prepare_email')).length,0);
});
test('provider 429 records retry; disabled gate blocks its next invocation',async()=>{
 const f=fixture({providerFailure:true});const body=await (await handleRequest(request(),{env,fetcher:f.fetcher})).json();assert.equal(body.retried,1);
 const ack=f.calls.find(c=>c.url.endsWith('/defectrag_finish_notification'));assert.equal(ack.body.p_delivered,false);assert.equal(ack.body.p_error,'notification_http_429');
 const count=f.calls.length;await handleRequest(request(),{env:{...env,DEFECTRAG_NOTIFICATIONS_ENABLED:'0'},fetcher:f.fetcher});assert.equal(f.calls.length,count);
});
test('lost acknowledgment stops invocation without repeating provider send',async()=>{
 const f=fixture({ackFailure:true});assert.equal((await handleRequest(request(),{env,fetcher:f.fetcher})).status,503);
 assert.equal(f.calls.filter(c=>c.url.includes('api.resend')).length,1);
});
test('disabled/capped/no-due-row RPC result never prepares or sends',async()=>{
 let calls=0;const fetcher=async url=>{calls++;assert.ok(url.endsWith('/defectrag_claim_developer_notifications'));return Response.json([])};
 assert.deepEqual(await (await handleRequest(request(),{env,fetcher})).json(),{claimed:0,accepted:0,retried:0,leaseLost:0});assert.equal(calls,1);
});
test('developer configuration diagnostic verifies restricted mode without network or secret output',async()=>{
 const req=new Request('https://fixture.invalid',{method:'POST',headers:{Authorization:'Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET,'X-DefectRAG-Check-Event':job.event_id}});
 const r=await handleRequest(req,{env:{...env,DEFECTRAG_NOTIFICATIONS_ENABLED:'0'},fetcher:()=>assert.fail('No diagnostic network')});
 const body=await r.json();assert.equal(body.ready_for_developer_only,true);assert.equal(body.ready_for_qa,false);
 assert.ok(Object.values(body.developer_checks).every(v=>typeof v==='boolean'));
 for(const key of ['DEFECTRAG_EMAIL_QA_RECIPIENT','DEFECTRAG_RESEND_API_KEY','SUPABASE_SERVICE_ROLE_KEY','DEFECTRAG_NOTIFICATION_WORKER_SECRET'])assert.ok(!JSON.stringify(body).includes(env[key]));
});
