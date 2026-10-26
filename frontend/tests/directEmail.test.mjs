import test from 'node:test';
import assert from 'node:assert/strict';
import {emailMessage} from '../../deployment/supabase/functions/staff-notifications/direct-email.mjs';
import {handleRequest} from '../../deployment/supabase/functions/staff-notifications/worker.mjs';
const job={event_id:'11111111-1111-4111-8111-111111111111',lease_token:'22222222-2222-4222-8222-222222222222',request_id:'33333333-3333-4333-8333-333333333333',kind:'requested',version:1,display_name:'QA\nApplicant',applicant_email:'applicant@example.invalid',recipient_email:'developer@example.invalid',requested_at:'2026-10-20T00:00:00Z'};
const env={DEFECTRAG_NOTIFICATIONS_ENABLED:'1',DEFECTRAG_NOTIFICATION_WORKER_SECRET:'w'.repeat(32),SUPABASE_URL:'https://db.example.invalid',SUPABASE_SERVICE_ROLE_KEY:'fixture-service',DEFECTRAG_NOTIFICATION_TRANSPORT:'resend',DEFECTRAG_RESEND_API_KEY:'fixture-provider',DEFECTRAG_EMAIL_FROM:'onboarding@resend.dev',DEFECTRAG_EMAIL_SANDBOX:'1',DEFECTRAG_EMAIL_QA_RECIPIENT:job.recipient_email,DEFECTRAG_EMAIL_QA_EVENT_ID:job.event_id};
const request=()=>new Request('https://edge.invalid',{method:'POST',headers:{Authorization:'Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET}});
test('developer body is plain text, redacted, dated and contains only fixed authenticated link',()=>{
 const m=emailMessage(job,env);assert.ok(m.text.includes('Status: Pending'));assert.ok(m.text.includes(job.requested_at));assert.ok(m.text.includes('https://wizzas-defectrag.hf.space/#team'));assert.ok(!m.text.includes(job.applicant_email));assert.ok(!m.text.includes(job.request_id));assert.ok(m.text.includes('a***@example.invalid'));
});
test('no-domain mode blocks all applicant mail and unapproved destinations',()=>{
 for(const change of [{kind:'approved'},{recipient_email:'thirdparty@example.invalid'},{event_id:'44444444-4444-4444-8444-444444444444'}])assert.throws(()=>emailMessage({...job,...change},env));
 assert.throws(()=>emailMessage(job,{...env,DEFECTRAG_EMAIL_QA_EVENT_ID:undefined}));
 assert.throws(()=>emailMessage(job,{...env,DEFECTRAG_EMAIL_SANDBOX:'0'}));
 const approved=emailMessage({...job,kind:'approved'},{...env,DEFECTRAG_EMAIL_SANDBOX:'0',DEFECTRAG_EMAIL_FROM:'notify@example.invalid'});assert.ok(!approved.text.includes('a***@'));
});
test('direct cloud path needs no n8n, persists exact snapshot and sends stable provider key',async()=>{
 let claimed=false,snapshot,calls=[];
 const fetcher=async(url,options)=>{
  const b=JSON.parse(options.body);calls.push({url,options,b});
  if(url.endsWith('/defectrag_claim_direct_notifications')){assert.equal(b.p_event,job.event_id);if(claimed)return Response.json([]);claimed=true;return Response.json([job])}
  if(url.endsWith('/defectrag_prepare_email')){snapshot=b.p_payload;return Response.json({payload:snapshot})}
  if(url.endsWith('/defectrag_finish_notification'))return Response.json(true);
  assert.equal(url,'https://api.resend.com/emails');assert.equal(options.headers['Idempotency-Key'],'defectrag/'+job.event_id);assert.deepEqual(b,snapshot);assert.ok(!options.body.includes(env.SUPABASE_SERVICE_ROLE_KEY));return Response.json({id:'provider-id'});
 };
 const result=await (await handleRequest(request(),{env,fetcher})).json();assert.equal(result.accepted,1);assert.equal(calls.filter(c=>c.url.includes('api.resend')).length,1);
});
for(const mode of ['timeout','http','receipt','quarantine'])test('direct delivery '+mode+' never reports success',async()=>{
 let claimed=false,finish;
 const fetcher=async(url,options)=>{
  if(url.endsWith('/defectrag_claim_direct_notifications')){if(claimed)return Response.json([]);claimed=true;return Response.json([job])}
  if(url.endsWith('/defectrag_prepare_email'))return Response.json(mode==='quarantine'?null:{payload:emailMessage(job,env)});
  if(url.endsWith('/defectrag_finish_notification')){finish=JSON.parse(options.body);return Response.json(true)}
  if(mode==='timeout')throw new Error('provider-secret');
  return mode==='http'?new Response('',{status:429}):Response.json({});
 };
 const r=await (await handleRequest(request(),{env,fetcher})).json();assert.equal(r.accepted,0);assert.equal(finish.p_delivered,false);assert.ok(!finish.p_error.includes('secret'));
});
test('lost database acknowledgment retries the immutable body/key without a second provider acceptance',async()=>{
 let snapshot,accepted=0,acknowledged=false,claimed=false,failAck=true;const receipts=new Map();
 const bodies=[];
 const fetcher=async(url,o)=>{
  if(url.endsWith('/defectrag_claim_direct_notifications')){if(claimed||acknowledged)return Response.json([]);claimed=true;return Response.json([job])}
  if(url.endsWith('/defectrag_prepare_email')){snapshot ||= JSON.parse(o.body).p_payload;return Response.json({payload:snapshot})}
  if(url.endsWith('/defectrag_finish_notification')){if(failAck){failAck=false;throw Error('lost ack')}acknowledged=true;return Response.json(true)}
  const key=o.headers['Idempotency-Key'];bodies.push(o.body);if(!receipts.has(key)){accepted++;receipts.set(key,{id:'stable-provider-id'})}return Response.json(receipts.get(key));
 };
 assert.equal((await handleRequest(request(),{env,fetcher})).status,503);claimed=false;
 const r=await (await handleRequest(request(),{env,fetcher})).json();assert.equal(r.accepted,1);assert.equal(accepted,1);assert.equal(bodies[0],bodies[1]);
});
