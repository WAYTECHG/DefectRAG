import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {workspaceRefreshGate,readRefreshSections} from '../src/workspaceRefresh.mjs';
import {createRequestScope} from '../src/workflow.mjs';
import {startPolling} from '../src/workspace.mjs';

const health={mode:'cloud_session_workspace',personal_workspace_enabled:true,auth_workflow_enabled:true};
const source=(await readFile(new URL('../src/main.jsx',import.meta.url),'utf8')).replaceAll('\r\n','\n');
const declaration=source.slice(source.indexOf(' async function refresh('),source.indexOf(' function retryRefresh('));
const tick=()=>new Promise(resolve=>setImmediate(resolve));

// Execute the actual React refresh handler with injected network/SDK/state edges.
// No model calls, real sessions, Supabase writes or notification delivery.
function harness(options={}){
 const state={records:['existing-private'],alerts:['existing-alert'],stats:{total:1},errors:[],calls:[],block:null,resets:0};
 const scope=createRequestScope();let configured=options.configured??true;
 const setters={setStats:'stats',setRecords:'records',setAlerts:'alerts',setArchived:'archived',setWorkspaceStatus:'workspace',setHealth:'health',setSamples:'samples',setEvaluation:'evaluation',setOfficial:'official',setInspectionAccess:'access',setWorkspaceBlock:'block'};
 const env={
  refreshContext:{current:scope},health:options.health===undefined?health:options.health,
  SHOWCASE:options.showcase??false,metadataLoaded:{current:!options.full},
  readRefreshSections,workspaceRefreshGate,configureLocalSync(){},setLocalSyncStatus(){},personalEnabled:()=>configured,configureWorkspace:v=>{configured=v},
  activeWorkspace:()=>configured?(options.workspace||'personal'):'team',setWorkspaceState(){},
  setSectionErrors:value=>{state.errors=typeof value==='function'?value(state.errors):value},
  clearWorkspace(){scope.invalidate();state.records=[];state.alerts=[];state.stats={total:0};state.workspace=null;state.errors=state.errors.filter(n=>['Connection','Samples','Performance','Benchmark'].includes(n))},
  resetInspection(){state.resets++},cloudClient:async()=>({}),
  loadInspectionAccess:async()=>{state.calls.push('native-account-check');if(options.accessError)throw Error('SDK failed');if(options.accessLoader)return options.accessLoader();return {state:options.access||'authorized'}},
  api:async path=>{state.calls.push(path);return options.api?options.api(path):path==='/api/health'?health:[{id:'fresh'}]},
  page:'batch',result:null,busy:false,ragBusy:false,artifactRefresh:{current:0},setMessages(){},setReview(){},setResult(){}
 };
 for(const [setter,key]of Object.entries(setters))env[setter]=value=>{state[key]=value};
 const refresh=new Function(...Object.keys(env),declaration+';return refresh')(...Object.values(env));
 return {state,refresh,scope,env};
}

test('cold startup resolves public routing before sending any private request',async()=>{
 const h=harness({health:null,configured:false,full:true});
 assert.equal(await h.refresh(true),false,'routing change restarts the polling generation');
 assert.deepEqual(h.state.calls,['/api/health','/api/samples','/api/evaluation','/api/benchmark/official']);
 assert.deepEqual(h.state.errors,[]);assert.equal(h.state.health.personal_workspace_enabled,true);
});

for(const access of ['pending','rejected','revoked','mfa','denied','checking','unavailable'])test(`${access} cannot fetch or retain private workspace data`,async()=>{
 const h=harness({access});const result=await h.refresh();
 assert.equal(result.state,'blocked');assert.deepEqual(h.state.calls,['native-account-check']);
 assert.deepEqual(h.state.records,[]);assert.deepEqual(h.state.alerts,[]);assert.equal(h.state.workspace,null);
 assert.equal(h.state.resets,1);assert.deepEqual(h.state.errors,[]);assert.ok(h.state.block.reason);
});

test('failed account verification never falls back to guest Demo requests',async()=>{
 const h=harness({accessError:true});await h.refresh();
 assert.equal(h.state.access.state,'unavailable');assert.equal(h.state.block.failed,true);
 assert.deepEqual(h.state.calls,['native-account-check']);
});

test('native approved access loads private data; guest Demo remains isolated and available',async()=>{
 for(const access of ['authorized','guest']){
  const h=harness({access});await h.refresh();
  assert.equal(h.state.block,null);assert.deepEqual(h.state.records,[{id:'fresh'}]);
  assert.equal(h.state.calls[0],'native-account-check');assert.equal(h.state.calls.length,6);
 }
 const team=harness({access:'guest',workspace:'team'});await team.refresh();
 assert.equal(team.state.block.action,'personal');assert.deepEqual(team.state.calls,['native-account-check']);
});

test('local and saved-showcase refreshes retain their existing API paths without Supabase checks',async()=>{
 for(const options of [{health:{mode:'local_single_user'}},{showcase:true,health:{mode:'saved_examples'}}]){
  const h=harness(options);await h.refresh();
  assert.equal(h.state.calls.length,4);assert.ok(!h.state.calls.includes('native-account-check'));
  assert.deepEqual(h.state.records,[{id:'fresh'}]);
 }
});

test('server permission denial after a successful SDK check clears all private data',async()=>{
 const h=harness({api:async path=>{if(path==='/api/alerts')throw Object.assign(Error('Revoked'),{status:403});return [{id:'must-not-apply'}]}});
 assert.equal((await h.refresh()).state,'blocked');assert.deepEqual(h.state.records,[]);
 assert.equal(h.state.access.state,'denied');assert.equal(h.state.block.action,'account');
});

test('genuine service failure remains visible; next successful retry replaces data and clears failure',async()=>{
 let fail=true;
 const h=harness({api:async path=>{if(fail&&path.startsWith('/api/inspections'))throw Object.assign(Error('Unavailable'),{status:503});return [{id:'fresh'}]}});
 await assert.rejects(h.refresh(),/could not synchronize/);
 assert.deepEqual(h.state.errors,['History']);assert.deepEqual(h.state.records,['existing-private']);
 fail=false;await h.refresh();assert.deepEqual(h.state.errors,[]);assert.deepEqual(h.state.records,[{id:'fresh'}]);
});

test('unreachable public health stops private requests and cannot be mislabeled as MFA',async()=>{
 const h=harness({full:true,api:async path=>{if(path==='/api/health')throw Error('Offline');return []}});
 await assert.rejects(h.refresh(true),/could not be reached/);
 assert.ok(h.state.errors.includes('Connection'));assert.equal(h.state.calls.length,4);
 assert.ok(!h.state.calls.includes('native-account-check'));
});

test('account/workspace changes discard late data and late SDK authorization',async()=>{
 let release;
 const h=harness({api:path=>path.startsWith('/api/inspections')?new Promise(resolve=>{release=resolve}):[]});
 const work=h.refresh();await tick();h.scope.invalidate();release([{id:'old-account'}]);
 assert.equal(await work,false);assert.deepEqual(h.state.records,['existing-private']);
 const scope=createRequestScope(),current=scope.capture();let finish;
 const read=readRefreshSections([['History','/private',()=>assert.fail('Stale apply')]],()=>new Promise(resolve=>{finish=resolve}),current);
 scope.invalidate();finish([]);assert.equal(await read,null);
 let authorize;
 const late=harness({accessLoader:()=>new Promise(resolve=>{authorize=resolve})});
 const authWork=late.refresh();await tick();late.scope.invalidate();authorize({state:'authorized'});
 assert.equal(await authWork,false);assert.deepEqual(late.state.calls,['native-account-check']);
 assert.equal(late.state.access,undefined);
});

test('real API boundary preserves 401/403 HTTP status for permission-specific guidance',async()=>{
 const apiSource=source.slice(source.indexOf('async function api('),source.indexOf(' function Badge('));
 for(const status of [401,403,503]){
  const api=new Function('SHOWCASE','request','showcaseApi','practiceActive','practiceApi',apiSource+';return api')(false,async()=>Response.json({error:{message:'Denied'}},{status}),()=>{},()=>false,()=>assert.fail('normal work never uses the lesson store'));
  await assert.rejects(api('/private'),error=>error.status===status);
 }
});

test('manual Retry uses the current coalesced poll and forces fresh metadata',()=>{
 const retrySource=source.slice(source.indexOf(' function retryRefresh('),source.indexOf(' async function loadBatch('));
 const metadataLoaded={current:true};let calls=0;
 new Function('metadataLoaded','refreshPoll',retrySource+';return retryRefresh')(
  metadataLoaded,{current:{refresh(){calls++}}})();
 assert.equal(metadataLoaded.current,false);assert.equal(calls,1);
 assert.ok(source.includes('refreshPoll.current?.refresh();'),'Auth listener uses the live poll, not a mount-time stale refresh closure');
});

test('poll reports a blocked account distinctly, then refreshes successfully after verification',async()=>{
 const target=new EventTarget(),doc=new EventTarget();target.navigator={onLine:true};doc.hidden=false;
 let block=true,release;const states=[];
 const poll=startPolling(async()=>{if(block)return {state:'blocked',reason:'MFA required'};await new Promise(resolve=>{release=resolve})},{target,documentTarget:doc,interval:100000,onState:s=>states.push(s.state)});
 try{
  await tick();assert.equal(states.at(-1),'blocked');block=false;
  const pending=poll.refresh();assert.equal(states.at(-1),'refreshing');
  poll.refresh();release();await pending;await tick();release();await tick();
  assert.equal(states.at(-1),'synced');
 }finally{poll.stop()}
});

const root=fileURLToPath(new URL('..',import.meta.url));
const built=await build({stdin:{contents:"export {default} from './src/RefreshNotice.jsx';",resolveDir:root,loader:'jsx'},bundle:true,write:false,platform:'node',format:'cjs',external:['react']});
const require=createRequire(new URL('../package.json',import.meta.url));
const module={exports:{}};new Function('require','module','exports',built.outputFiles[0].text)(require,module,module.exports);
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
const render=props=>renderToStaticMarkup(React.createElement(module.exports.default,props));

test('real refresh notice is absent when healthy, actionable for MFA, and announces busy Retry',()=>{
 assert.equal(render({}), '');
 const mfa=render({block:workspaceRefreshGate(health,{state:'mfa'},'personal')});
 assert.ok(mfa.includes('role="status"'));assert.ok(mfa.includes('Open Staff workspace'));assert.ok(!mfa.includes('Could not refresh'));
 assert.equal(render({block:workspaceRefreshGate(health,{state:'mfa'},'personal'),showAccess:false}),'');
 const retry=render({errors:['History'],refreshing:true});
 assert.ok(retry.includes('Refreshing…'));assert.ok(retry.includes('disabled=""'));assert.ok(retry.includes('aria-busy="true"'));
 const failed=render({errors:['History'],refreshing:false});assert.ok(failed.includes('Retry refresh'));assert.ok(!failed.includes('disabled=""'));
 assert.ok(render({block:workspaceRefreshGate(health,{state:'unavailable'},'personal')}).includes('role="alert"'));
});
