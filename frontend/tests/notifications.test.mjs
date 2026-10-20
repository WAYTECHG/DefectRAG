import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {handleRequest,LIMITS} from '../../deployment/supabase/functions/staff-notifications/worker.mjs';
const event={event_id:'11111111-1111-4111-8111-111111111111',request_id:'22222222-2222-4222-8222-222222222222',
 lease_token:'33333333-3333-4333-8333-333333333333',kind:'requested',version:1,
 recipient_email:'developer@example.invalid',applicant_email:'applicant@example.invalid',display_name:'Applicant'};
const env={DEFECTRAG_NOTIFICATIONS_ENABLED:'1',DEFECTRAG_NOTIFICATION_WORKER_SECRET:'worker-fixture-secret-32-characters-minimum',
 DEFECTRAG_N8N_WEBHOOK_SECRET:'webhook-fixture-secret-32-characters-minimum',DEFECTRAG_N8N_WEBHOOK_URL:'https://n8n.example.invalid/webhook/defectrag',
 SUPABASE_URL:'https://db.example.invalid',SUPABASE_SERVICE_ROLE_KEY:'server-only-fixture'};
function request(secret=env.DEFECTRAG_NOTIFICATION_WORKER_SECRET){return new Request('https://edge.example.invalid',{method:'POST',headers:{Authorization:'Bearer '+secret}})}
function fixture(handler){
 const calls=[];let claimed=false;
 return {calls,fetcher:async(url,options)=>{
  const body=JSON.parse(options.body);calls.push({url,options,body});
  if(url.endsWith('/defectrag_claim_notifications')){const jobs=claimed?[]:[event];claimed=true;return Response.json(jobs)}
  if(url.endsWith('/defectrag_finish_notification'))return Response.json(true);
  return handler?handler({url,options,body}):Response.json({event_id:event.event_id,delivered:true});
 }};
}
test('disabled and unauthorized workers do not touch database or n8n',async()=>{
 for(const [settings,key,status] of [[{...env,DEFECTRAG_NOTIFICATIONS_ENABLED:'0'},'',503],[env,'public-key',401]]){
  const response=await handleRequest(request(key),{env:settings,fetcher:()=>assert.fail('No network')});assert.equal(response.status,status);
 }
 assert.equal((await handleRequest(new Request('https://edge.invalid'),{env,fetcher:()=>assert.fail()})).status,405);
});
test('successful delivery keeps privileged credentials out of webhook payload and returns only counts',async()=>{
 const f=fixture();const response=await handleRequest(request(),{env,fetcher:f.fetcher});
 assert.deepEqual(await response.json(),{claimed:1,accepted:1,retried:0,leaseLost:0});
 const webhook=f.calls[1];assert.equal(webhook.options.headers['X-DefectRAG-Webhook-Key'],env.DEFECTRAG_N8N_WEBHOOK_SECRET);
 assert.equal(webhook.options.redirect,'error');assert.equal(webhook.body.lease_token,undefined);
 assert.ok(!JSON.stringify(webhook).includes(env.SUPABASE_SERVICE_ROLE_KEY));
 assert.deepEqual(f.calls[2].body,{p_id:event.event_id,p_lease:event.lease_token,p_delivered:true,p_error:''});
});
for(const status of [401,429,500,503])test(`n8n HTTP ${status} schedules retry without reporting delivery`,async()=>{
 const f=fixture(()=>new Response('failure',{status}));const response=await handleRequest(request(),{env,fetcher:f.fetcher});
 assert.equal((await response.json()).retried,1);assert.equal(f.calls[2].body.p_delivered,false);
 assert.equal(f.calls[2].body.p_error,'notification_http_'+status);
});
test('offline n8n retains durable retry and never exposes error secrets',async()=>{
 const f=fixture(()=>{throw new Error('smtp-private-secret')});const response=await handleRequest(request(),{env,fetcher:f.fetcher});
 assert.equal((await response.json()).retried,1);assert.equal(f.calls[2].body.p_error,'notification_unavailable');
});
for(const receipt of [{message:'Workflow started'},{event_id:event.event_id,delivered:false},{event_id:'foreign-event',delivered:true}])test('only matching provider-acceptance receipts count as delivered',async()=>{
 const f=fixture(()=>Response.json(receipt));assert.equal((await (await handleRequest(request(),{env,fetcher:f.fetcher})).json()).accepted,0);
});
test('database outage is safe and sanitized; stale leases cannot report delivery',async()=>{
 const unavailable=await handleRequest(request(),{env,fetcher:async()=>new Response('secret',{status:500})});
 assert.equal(unavailable.status,503);assert.deepEqual(await unavailable.json(),{error:'dispatch_unavailable'});
 const f=fixture();const fetcher=(url,options)=>url.endsWith('/defectrag_finish_notification')?Response.json(false):f.fetcher(url,options);
 assert.equal((await (await handleRequest(request(),{env,fetcher})).json()).leaseLost,1);
});
test('leased outbox avoids resending acknowledged events on subsequent invocation',async()=>{
 let sent=false,hooks=0;
 const fetcher=async(url)=>{
  if(url.endsWith('/defectrag_claim_notifications'))return Response.json(sent?[]:[event]);
  if(url.endsWith('/defectrag_finish_notification')){sent=true;return Response.json(true)}
  hooks++;return Response.json({event_id:event.event_id,delivered:true});
 };
 await handleRequest(request(),{env,fetcher});await handleRequest(request(),{env,fetcher});assert.equal(hooks,1);
});
test('applicant notifications exclude applicant email and no HTTPS downgrade is allowed',async()=>{
 let webhook;
 const fetcher=async(url,options)=>{
  if(url.endsWith('/defectrag_claim_notifications'))return Response.json([{...event,kind:'approved'}]);
  if(url.endsWith('/defectrag_finish_notification'))return Response.json(true);
  webhook=JSON.parse(options.body);return Response.json({event_id:event.event_id,delivered:true});
 };
 await handleRequest(request(),{env,fetcher});assert.equal(webhook.applicant_email,undefined);
 const bad=await handleRequest(request(),{env:{...env,DEFECTRAG_N8N_WEBHOOK_URL:'http://n8n.invalid'},fetcher:()=>assert.fail()});assert.equal(bad.status,503);
});
test('inactive n8n template validates events and never acknowledges before SMTP acceptance',async()=>{
 const workflow=JSON.parse(await readFile(new URL('../../deployment/n8n/staff-notifications.json',import.meta.url),'utf8'));
 assert.equal(workflow.active,false);
 const webhook=workflow.nodes.find(n=>n.type.endsWith('.webhook'));assert.equal(webhook.parameters.authentication,'headerAuth');assert.equal(webhook.parameters.responseMode,'responseNode');
 assert.equal(workflow.connections['Send notification'].main[0][0].node,'Verify SMTP acceptance');
 const validator=workflow.nodes.find(n=>n.name==='Validate notification').parameters.jsCode;
 const evaluate=new Function('$input',validator);
 const good=evaluate({first:()=>({json:{body:event}})});assert.equal(good[0].json.recipient_email,event.recipient_email);
 for(const malformed of [{...event,kind:'approve'}, {...event,recipient_email:'victim@example.invalid\r\nBcc: leak@example.invalid'}])assert.throws(()=>evaluate({first:()=>({json:{body:malformed}})}));
 const accept=new Function('$input','$',workflow.nodes.find(n=>n.name==='Verify SMTP acceptance').parameters.jsCode);
 const selector=()=>({first:()=>good[0]});assert.equal(accept({first:()=>({json:{accepted:[event.recipient_email],rejected:[]}})},selector)[0].json.delivered,true);
 assert.throws(()=>accept({first:()=>({json:{accepted:[],rejected:[event.recipient_email]}})},selector));
});

test('maximum invocation budget stays below Free Edge limit and claims just in time',async()=>{
 assert.equal(LIMITS.events,2);assert.equal(LIMITS.budgetMs,100000);assert.ok(LIMITS.reserveMs>2*LIMITS.rpcMs+LIMITS.webhookMs);
 const events=[event,{...event,event_id:'44444444-4444-4444-8444-444444444444'}];let claims=0,hooks=0;
 const fetcher=async(url,options)=>{
  if(url.endsWith('/defectrag_claim_notifications')){assert.equal(JSON.parse(options.body).p_limit,1);return Response.json([events[claims++]])}
  if(url.endsWith('/defectrag_finish_notification'))return Response.json(true);
  assert.equal(options.headers['Idempotency-Key'],events[hooks].event_id);hooks++;return Response.json({event_id:events[hooks-1].event_id,delivered:true});
 };
 assert.equal((await (await handleRequest(request(),{env,fetcher})).json()).accepted,2);assert.equal(claims,2);assert.equal(hooks,2);
});
test('partial batch stops before leasing another event when reserved time is exhausted',async()=>{
 let clock=0,claims=0,hooks=0;
 const fetcher=async(url)=>{
  if(url.endsWith('/defectrag_claim_notifications')){claims++;clock+=14000;return Response.json([event])}
  if(url.endsWith('/defectrag_finish_notification')){clock+=15000;return Response.json(true)}
  clock+=20000;hooks++;return Response.json({event_id:event.event_id,delivered:true});
 };
 const response=await handleRequest(request(),{env,fetcher,now:()=>clock});
 assert.deepEqual(await response.json(),{claimed:1,accepted:1,retried:0,leaseLost:0,budgetLimited:true});
 assert.equal(claims,1);assert.equal(hooks,1);
});
test('insufficient overall budget makes no claim and leaves queued work untouched',async()=>{
 const response=await handleRequest(request(),{env,budgetMs:LIMITS.reserveMs-1,fetcher:()=>assert.fail('Must not lease unstarted work')});
 assert.equal((await response.json()).budgetLimited,true);
});
test('overall deadline aborts stalled response bodies without a false delivery acknowledgment',async()=>{
 let clock=0,aborted=false,finishes=0;
 const fetcher=async(url,options)=>{
  if(url.endsWith('/defectrag_claim_notifications')){clock=LIMITS.budgetMs-10;return Response.json([event])}
  if(url.endsWith('/defectrag_finish_notification')){finishes++;return Response.json(true)}
  options.signal.addEventListener('abort',()=>{aborted=true;clock=LIMITS.budgetMs});
  return {ok:true,status:200,json:()=>new Promise(()=>{})};
 };
 const result=await handleRequest(request(),{env,fetcher,now:()=>clock});
 assert.equal(result.status,503);assert.equal(aborted,true);assert.equal(finishes,0); // Lease expires for durable recovery.
});
test('failed first webhook does not prevent another event and retries reuse the event ID',async()=>{
 const later={...event,event_id:'44444444-4444-4444-8444-444444444444'};let claims=0,hookIds=[],finishes=[];
 const fetcher=async(url,options)=>{
  if(url.endsWith('/defectrag_claim_notifications'))return Response.json([claims++%2===0?event:later]);
  if(url.endsWith('/defectrag_finish_notification')){finishes.push(JSON.parse(options.body));return Response.json(true)}
  hookIds.push(options.headers['Idempotency-Key']);return hookIds.length===1?new Response('',{status:503}):Response.json({event_id:JSON.parse(options.body).event_id,delivered:true});
 };
 const result=await (await handleRequest(request(),{env,fetcher})).json();assert.equal(result.retried,1);assert.equal(result.accepted,1);
 assert.equal(finishes[0].p_delivered,false);
 await handleRequest(request(),{env,fetcher});assert.equal(hookIds[0],hookIds[2]);
});
test('a repeated outbox event in the same invocation cannot send a second notification',async()=>{
 let hooks=0;
 const fetcher=async(url)=>{
  if(url.endsWith('/defectrag_claim_notifications'))return Response.json([event]);
  if(url.endsWith('/defectrag_finish_notification'))return Response.json(true);
  hooks++;return Response.json({event_id:event.event_id,delivered:true});
 };
 assert.equal((await handleRequest(request(),{env,fetcher})).status,503);assert.equal(hooks,1);
});
test('lost post-send acknowledgment is not retried within the invocation',async()=>{
 let hooks=0;
 const fetcher=async(url)=>{
  if(url.endsWith('/defectrag_claim_notifications'))return Response.json([event]);
  if(url.endsWith('/defectrag_finish_notification'))throw new Error('acknowledgment unavailable');
  hooks++;return Response.json({event_id:event.event_id,delivered:true});
 };
 assert.equal((await handleRequest(request(),{env,fetcher})).status,503);assert.equal(hooks,1);
 // SMTP can still duplicate after an ambiguous crash/lease recovery; no exactly-once claim.
});
