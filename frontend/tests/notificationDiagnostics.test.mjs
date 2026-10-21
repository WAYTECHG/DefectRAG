import test from 'node:test';
import assert from 'node:assert/strict';
import {handleRequest} from '../../deployment/supabase/functions/staff-notifications/worker.mjs';
const event='11111111-1111-4111-8111-111111111111';
const env={DEFECTRAG_NOTIFICATIONS_ENABLED:'0',DEFECTRAG_NOTIFICATION_WORKER_SECRET:'private-worker-'.repeat(4),
 SUPABASE_URL:'https://private-project.example.invalid',SUPABASE_SERVICE_ROLE_KEY:'private-service-key',
 DEFECTRAG_NOTIFICATION_TRANSPORT:'resend',DEFECTRAG_RESEND_API_KEY:'private-provider-key',
 DEFECTRAG_EMAIL_FROM:'onboarding@resend.dev',DEFECTRAG_EMAIL_SANDBOX:'1',
 DEFECTRAG_EMAIL_QA_RECIPIENT:'private-developer@example.invalid',DEFECTRAG_EMAIL_QA_EVENT_ID:event};
const noNetwork=()=>assert.fail('Diagnostic must not claim, prepare, finish, or call a provider');
const request=(headers={})=>new Request('https://fixture.invalid',{method:'POST',headers:{
 Authorization:'Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET,'X-DefectRAG-Check-Event':event,...headers}});
test('authenticated disabled configuration check reports only booleans without network or secret values',async()=>{
 const response=await handleRequest(request(),{env,fetcher:noNetwork});assert.equal(response.status,200);
 const body=await response.json();assert.equal(body.ready_for_qa,true);assert.equal(body.delivery_disabled,true);
 assert.ok(Object.values(body.checks).every(v=>typeof v==='boolean'));
 const text=JSON.stringify(body);
 for(const key of ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','DEFECTRAG_RESEND_API_KEY',
  'DEFECTRAG_NOTIFICATION_WORKER_SECRET','DEFECTRAG_EMAIL_QA_RECIPIENT','DEFECTRAG_EMAIL_QA_EVENT_ID'])assert.ok(!text.includes(env[key]));
 assert.equal(response.headers.get('Cache-Control'),'no-store');
});
for(const bearer of ['', 'Bearer wrong', 'Bearer '+env.SUPABASE_SERVICE_ROLE_KEY])test('diagnostic denies wrong bearer '+bearer.length,async()=>{
 const r=await handleRequest(request({Authorization:bearer}),{env,fetcher:noNetwork});assert.equal(r.status,401);assert.deepEqual(await r.json(),{error:'unauthorized'});
});
test('diagnostic requires configured worker secret',async()=>{
 const r=await handleRequest(request(),{env:{...env,DEFECTRAG_NOTIFICATION_WORKER_SECRET:''},fetcher:noNetwork});assert.equal(r.status,401);
});
for(const gate of ['1',undefined,'false'])test('diagnostic refuses nonzero or unknown gate '+gate,async()=>{
 const r=await handleRequest(request(),{env:{...env,DEFECTRAG_NOTIFICATIONS_ENABLED:gate},fetcher:noNetwork});
 assert.equal(r.status,409);assert.deepEqual(await r.json(),{error:'diagnostics_require_delivery_disabled'});
});
for(const value of ['', 'not-a-uuid'])test('malformed explicit diagnostic cannot dispatch '+value,async()=>{
 const r=await handleRequest(request({'X-DefectRAG-Check-Event':value}),{env,fetcher:noNetwork});assert.equal(r.status,400);
});
for(const [key,value,check] of [
 ['DEFECTRAG_NOTIFICATION_TRANSPORT',undefined,'transport_resend'],
 ['DEFECTRAG_EMAIL_SANDBOX','0','sandbox_enabled'],
 ['SUPABASE_URL','http://fixture.invalid','supabase_url_https'],
 ['SUPABASE_SERVICE_ROLE_KEY','','service_role_key_present'],
 ['DEFECTRAG_RESEND_API_KEY','','resend_key_present'],
 ['DEFECTRAG_EMAIL_FROM','wrong@example.invalid','test_sender'],
 ['DEFECTRAG_EMAIL_QA_RECIPIENT','bad\naddress','developer_recipient_format'],
 ['DEFECTRAG_EMAIL_QA_EVENT_ID','22222222-2222-4222-8222-222222222222','qa_event_matches']
])test('diagnostic identifies misconfiguration without sending: '+key,async()=>{
 const r=await handleRequest(request(),{env:{...env,[key]:value},fetcher:noNetwork});assert.equal(r.status,200);
 const body=await r.json();assert.equal(body.ready_for_qa,false);assert.equal(body.checks[check],false);
});
test('ordinary disabled POST remains503 and has no configuration output',async()=>{
 const r=await handleRequest(new Request('https://fixture.invalid',{method:'POST'}),{env,fetcher:noNetwork});
 assert.equal(r.status,503);assert.deepEqual(await r.json(),{error:'notifications_disabled'});
});
