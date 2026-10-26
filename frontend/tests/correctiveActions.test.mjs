import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {caseCanEdit,caseMetrics,latestDefectReview,nextCaseStates,caseRpc} from '../src/correctiveActions.mjs';
import {reviewBody} from '../src/workflow.mjs';
import {handleCA} from '../../deployment/supabase/functions/corrective-actions/worker.mjs';
const uuid='11111111-1111-4111-8111-111111111111',lease='22222222-2222-4222-8222-222222222222';
const event={event_id:uuid,lease_token:lease,case_id:'33333333-3333-4333-8333-333333333333',kind:'created',version:1,state:'Open',priority:'High',due_at:'2026-10-21T00:00:00Z'};
const env={DEFECTRAG_CA_AUTOMATION_ENABLED:'1',DEFECTRAG_CA_WORKER_SECRET:'w'.repeat(32),DEFECTRAG_CA_CALLBACK_SECRET:'c'.repeat(32),DEFECTRAG_CA_N8N_SECRET:'h'.repeat(32),DEFECTRAG_CA_N8N_URL:'https://n8n.invalid/webhook/ca',SUPABASE_URL:'https://db.invalid',SUPABASE_SERVICE_ROLE_KEY:'service-fixture'};
const request=(callback=false,b={})=>new Request('https://edge.invalid',{method:'POST',headers:{Authorization:'Bearer '+(callback?env.DEFECTRAG_CA_CALLBACK_SECRET:env.DEFECTRAG_CA_WORKER_SECRET),...(callback?{'X-DefectRAG-Operation':'effect'}:{})},body:JSON.stringify(b)});

test('case editor feedback uses current assignments or a verified directory Developer role',()=>{
 const row={owner_id:uuid,supervisor_id:lease,confirmed_by:'creator'};
 assert.equal(caseCanEdit(row,uuid),true);assert.equal(caseCanEdit(row,lease),true);
 assert.equal(caseCanEdit(row,'developer',true),true);
 for(const actor of ['unassigned','creator','',null,undefined])assert.equal(caseCanEdit(row,actor),false);
 assert.equal(caseCanEdit(row,'unassigned','developer'),false);
 assert.equal(caseCanEdit(null,uuid,true),false);
 assert.equal(caseCanEdit({...row,owner_id:'replacement'},uuid),false);
});
test('AI anomaly, incomplete review and accepted disposition never qualify as confirmed-defect review',()=>{
 assert.equal(latestDefectReview([]),null);
 const row={id:uuid,created_at:'2026-10-20T00:00:00Z',body:reviewBody('Reviewed','Reject','Confirmed review')};
 assert.equal(latestDefectReview([row]),row);
 for(const body of [reviewBody('In review','Pending'),reviewBody('Reviewed','Accept')])assert.equal(latestDefectReview([row,{...row,id:lease,created_at:'2026-10-21T00:00:00Z',body}]),null);
});
test('case states enforce progression, audited progress, reopen and terminal boundaries',()=>{
 for(const [a,b] of [['Open','Assigned'],['Assigned','In Progress'],['In Progress','Resolved'],['Resolved','Closed'],['Resolved','In Progress']])assert.ok(nextCaseStates(a).includes(b));
 assert.ok(!nextCaseStates('Open').includes('Closed'));assert.deepEqual(nextCaseStates('Closed'),[]);assert.deepEqual(nextCaseStates('Cancelled'),[]);
});
test('metrics use actual resolved timestamps, no fake defaults or reopened resolutions',()=>{
 assert.equal(caseMetrics([]).averageResolutionHours,null);
 const rows=[{state:'Closed',created_at:'2026-10-20T00:00:00Z',resolved_at:'2026-10-20T04:00:00Z'},
 {state:'Resolved',created_at:'2026-10-20T00:00:00Z',resolved_at:'2026-10-20T02:00:00Z'},
 {state:'In Progress',created_at:'2026-10-20T00:00:00Z',due_at:'2026-10-20T01:00:00Z',resolved_at:null}];
 assert.deepEqual(caseMetrics(rows,Date.parse('2026-10-20T05:00:00Z')),{open:1,resolved:2,overdue:1,averageResolutionHours:3});
});
test('server denial and optimistic-concurrency errors are never converted to successful UI writes',async()=>{
 await assert.rejects(()=>caseRpc({rpc:async()=>({error:new Error('AAL2 required')})},'test',{}),/AAL2/);
 await assert.rejects(()=>caseRpc({rpc:async()=>({error:new Error('refresh')})},'test',{}),/refresh/);
});
test('disabled/unauthorized bridge never contacts Supabase or n8n',async()=>{
 const no=()=>assert.fail('No network');assert.equal((await handleCA(request(),{env:{...env,DEFECTRAG_CA_AUTOMATION_ENABLED:'0'},fetcher:no})).status,503);
 assert.equal((await handleCA(request(),{env:{...env,DEFECTRAG_CA_WORKER_SECRET:'different-secret'.repeat(3)},fetcher:no})).status,401);
 assert.equal((await handleCA(request(true),{env:{...env,DEFECTRAG_CA_CALLBACK_SECRET:'wrong-secret'.repeat(4)},fetcher:no})).status,401);
});
test('dispatch projects event capability only, retains authoritative completion check',async()=>{
 let finished;
 const fetcher=async(url,o)=>{
  if(url.endsWith('defectrag_ca_schedule'))return Response.json(1);
  if(url.endsWith('defectrag_ca_claim'))return Response.json({...event,image:'private',token:'private'});
  if(url.endsWith('defectrag_ca_finish')){finished=JSON.parse(o.body);return Response.json(true)}
  assert.equal(o.headers['X-DefectRAG-CA-Key'],env.DEFECTRAG_CA_N8N_SECRET);assert.deepEqual(JSON.parse(o.body),event);assert.ok(!JSON.stringify(o).includes(env.SUPABASE_SERVICE_ROLE_KEY));
  return Response.json({event_id:uuid,completed:true});
 };
 const r=await (await handleCA(request(),{env,fetcher})).json();assert.equal(r.workflowCompleted,true);assert.equal(finished.p_success,true);
});
for(const failure of ['offline','rejected','mismatched'])test('workflow '+failure+' leaves SQL to retry/quarantine, no fake completion',async()=>{
 let finished;
 const fetcher=async(url,o)=>{
  if(url.endsWith('defectrag_ca_schedule'))return Response.json(0);
  if(url.endsWith('defectrag_ca_claim'))return Response.json(event);
  if(url.endsWith('defectrag_ca_finish')){finished=JSON.parse(o.body);return Response.json(true)}
  if(failure==='offline')throw Error('private-key');
  return failure==='rejected'?new Response('',{status:503}):Response.json({event_id:lease,completed:true});
 };
 const r=await (await handleCA(request(),{env,fetcher})).json();assert.equal(r.workflowCompleted,false);assert.equal(finished.p_success,false);
});
test('effect callback can only invoke bounded notification RPC with event lease',async()=>{
 let called;
 const r=await handleCA(request(true,{event_id:uuid,lease_token:lease,operation:'begin',effect:'ticket',arbitrary_table:'staff_members'}),{env,fetcher:async(url,o)=>{called={url,b:JSON.parse(o.body)};return Response.json({execute:true,recipient_email:'fixture@example.invalid'})}});
 assert.equal(r.status,200);assert.ok(called.url.endsWith('/defectrag_ca_effect'));assert.equal(called.b.p_effect,'notification');assert.equal(called.b.p_event,uuid);
 assert.equal((await handleCA(request(true,{event_id:'wrong',lease_token:lease,operation:'begin'}),{env,fetcher:()=>assert.fail()})).status,400);
});
test('insufficient deadline never schedules, claims or dispatches',async()=>{
 assert.deepEqual(await (await handleCA(request(),{env,budgetMs:89999,fetcher:()=>assert.fail()})).json(),{claimed:0,budgetLimited:true});
});
test('n8n template is inactive, header-authenticated, disables execution logs and blocks uncertain effects',async()=>{
 const w=JSON.parse(await readFile(new URL('../../deployment/n8n/corrective-actions.json',import.meta.url),'utf8'));
 assert.equal(w.active,false);assert.equal(w.settings.saveDataSuccessExecution,'none');assert.equal(w.nodes[0].parameters.authentication,'headerAuth');
 const code=name=>new Function('$input','$',w.nodes.find(n=>n.name===name).parameters.jsCode);
 assert.equal(code('Validate case event')({first:()=>({json:{body:event}})})[0].json.event_id,uuid);
 assert.throws(()=>code('Validate case event')({first:()=>({json:{body:{...event,kind:'AI_prediction'}}})}));
 const $=()=>({first:()=>({json:event})});
 assert.throws(()=>code('Require durable completion')({first:()=>({json:{done:false,manual_review:true}})},$));
 assert.equal(code('Require durable completion')({first:()=>({json:{done:true}})},$)[0].json.completed,true);
 assert.ok(!JSON.stringify(w).includes('service_role'));assert.ok(!w.nodes.some(n=>n.type.includes('trello')));
});
test('SQL source contracts require explicit confirmation, live Staff/TOTP, restricted grants and unique effects',async()=>{
 const sql=await readFile(new URL('../../deployment/supabase_corrective_actions.sql',import.meta.url),'utf8');
 for(const required of ['public.defectrag_is_staff() and public.defectrag_has_aal2()','p_confirmed is distinct from true',"review->>'decision' is distinct from 'Reject'",'p_version is distinct from c.version','unique(case_id,version,kind)','primary key(event_id,effect)',"state='uncertain'",'for update skip locked'])assert.ok(sql.includes(required),required);
 assert.ok(!/grant .*insert.* to authenticated/i.test(sql));
 assert.ok(sql.includes('auth.uid() is distinct from c.owner_id and auth.uid() is distinct from c.supervisor_id'));
 assert.ok(sql.indexOf('auth.uid() is distinct from c.owner_id')<sql.indexOf('if p_version is distinct from c.version'));
 // Contract checks are NOT an executed Postgres/RLS integration test.
});
test('new JSX compiles and retains existing-style labels, metrics and explicit confirmation',async()=>{
 const r=await build({entryPoints:[new URL('../src/CorrectiveActions.jsx',import.meta.url).pathname.replace(/^\/(.:)/,'$1')],bundle:true,write:false,platform:'browser',logLevel:'silent'});assert.ok(r.outputFiles[0].text.length>0);
 const source=await readFile(new URL('../src/CorrectiveActions.jsx',import.meta.url),'utf8');
 assert.ok(source.includes('disabled={busy||!confirmed}'));assert.ok(source.includes('defectrag_ca_staff'));assert.ok(source.includes('Open the linked photo and review'));
 assert.ok(source.includes('nextCaseStates(current.state).length>0&&canEdit&&<form'));
 assert.ok(source.includes('can change this case after verifying their security code.'));
});
test('real JSX renders existing card design but waits for native CA assurance before showing private forms',async()=>{
 const root=fileURLToPath(new URL('..',import.meta.url));
 const r=await build({stdin:{contents:"export {default} from './src/CorrectiveActions.jsx'",resolveDir:root,loader:'jsx'},bundle:true,write:false,platform:'node',format:'cjs',external:['react'],logLevel:'silent',plugins:[{name:'fixture-cloud',setup(b){b.onResolve({filter:/^\.\/cloud\.js$/},()=>({path:'cloud',namespace:'fixture'}));b.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:'export async function cloudClient(){throw Error("No network during rendering")} export function workspaceChanged(){}'}))}}]});
 const require=createRequire(new URL('../package.json',import.meta.url)),module={exports:{}};new Function('require','module','exports',r.outputFiles[0].text)(require,module,module.exports);
 const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
 const props={user:{id:uuid},inspection:{id:'a'.repeat(32)},notes:[{id:uuid,created_at:'2026-10-20',body:reviewBody('Reviewed','Reject')}],onEvidence(){}};
 const html=renderToStaticMarkup(React.createElement(module.exports.default,props));
 for(const text of ['Corrective Actions','class="card"','Staff review confirms a defect','Checking Staff access and the security code']){
  assert.ok(html.includes(text),text);
 }
 assert.ok(!html.includes('Create corrective action'));assert.ok(!html.includes('Save case update'));
});
