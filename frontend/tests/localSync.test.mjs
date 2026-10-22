import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {configureLocalSync,localSyncEnabled,localSyncRequest,synchronizationText} from '../src/localSync.mjs';
import {workspaceRefreshGate} from '../src/workspaceRefresh.mjs';
import {inspectionReadiness} from '../src/inspectionReadiness.mjs';

globalThis.location={origin:'http://127.0.0.1:5173'};
const store=()=>{const values=new Map();return {getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)}};
const signed=(id='fixture-A')=>({auth:{getSession:async()=>({data:{session:{access_token:id}}})}});
test('local synchronization is opt-in and cannot enable itself from a token',()=>{
 assert.equal(localSyncEnabled(),false);configureLocalSync('1');assert.equal(localSyncEnabled(),false);
 configureLocalSync(true);assert.equal(localSyncEnabled(),true);configureLocalSync(false);
});
test('each local request gets the current identity and scope; auth failures never fall back to guest',async()=>{
 const storage=store(),calls=[];const fetcher=async(path,options)=>{calls.push({path,options});return Response.json({data:[]})};
 await localSyncRequest('/api/stats',{},signed(), 'personal',fetcher,storage);
 await localSyncRequest('/api/stats',{},signed('fixture-B'),'team',fetcher,storage);
 assert.equal(calls[0].options.headers.get('Authorization'),'Bearer fixture-A');
 assert.equal(calls[1].options.headers.get('Authorization'),'Bearer fixture-B');
 assert.equal(calls[1].options.headers.get('X-DefectRAG-Workspace'),'team');
 assert.match(calls[0].options.headers.get('X-DefectRAG-Session'),/^[a-f0-9]{64}$/);
 assert.equal(calls[0].options.headers.get('X-DefectRAG-Session'),calls[1].options.headers.get('X-DefectRAG-Session'));
 assert.equal(calls[0].options.cache,'no-store');
 await assert.rejects(localSyncRequest('/api/stats',{}, {auth:{getSession:async()=>({error:Error('Expired')})}},'personal',fetcher,storage),/session could not refresh/);
 assert.equal(calls.length,2);
});
test('public metadata loads without requesting credentials, so session trouble cannot hide health',async()=>{
 for(const path of ['/api/health','/api/samples','/api/evaluation','/api/gallery','/api/benchmark/official']){
  let called=false;
  await localSyncRequest(path,{}, {auth:{getSession:()=>assert.fail('Public route requested credentials')}},'personal',async()=>{called=true},store());
  assert.equal(called,true);
 }
});
test('local protected account operations retain native MFA/pending/revocation boundaries',()=>{
 const health={status:'ok',mode:'local_single_user',local_sync_enabled:true,personal_workspace_enabled:true,auth_workflow_enabled:true};
 for(const state of ['pending','mfa','revoked','denied','unavailable']){
  assert.ok(workspaceRefreshGate(health,{state},'personal'));
  assert.equal(inspectionReadiness({health,workspace:'personal',access:{state},files:[{type:'image/jpeg',size:100}]}).disabled,true);
 }
 assert.equal(workspaceRefreshGate(health,{state:'authorized'},'personal'),null);
});
test('synchronization copy never claims cloud success for queued, conflicting or incomplete scans',()=>{
 assert.match(synchronizationText({state:'pending',pending:2}),/waiting/);
 assert.match(synchronizationText({state:'conflict'}),/Both copies are retained/);
 assert.match(synchronizationText({scan_in_progress:true}),/continues this scan/);
 assert.match(synchronizationText({last_synchronized:'fixture'}),/synchronized/);
 assert.match(synchronizationText(null),/Sign in/);
});
const root=fileURLToPath(new URL('..',import.meta.url));
const built=await build({stdin:{contents:"export {default} from './src/LocalSyncPanel.jsx';",resolveDir:root,loader:'jsx'},bundle:true,write:false,platform:'node',format:'cjs',external:['react']});
const require=createRequire(new URL('../package.json',import.meta.url)),module={exports:{}};
new Function('require','module','exports',built.outputFiles[0].text)(require,module,module.exports);
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
test('existing styled notice renders queue/conflict actions and offers explicit import only to authorized accounts',()=>{
 const render=props=>renderToStaticMarkup(React.createElement(module.exports.default,props));
 const html=render({status:{state:'conflict',conflicts:[{inspection_id:'a'.repeat(32)}]},canImport:true});
 for(const phrase of ['class="note"','role="status"','Review conflict','Import existing local history'])assert.ok(html.includes(phrase));
 assert.ok(!render({canImport:false}).includes('Import existing local history'));
 assert.ok(render({refreshing:true}).includes('Synchronizing…'));
});
test('existing app sends local work through its account adapter and keeps synchronization separate from sharing',async()=>{
 const source=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.ok(source.includes('if(localSyncEnabled())return localSyncRequest'));
 assert.ok(source.includes("access.state==='authorized'&&activeWorkspace()==='personal'"));
 assert.ok(source.includes("api('/api/local-sync/run',{method:'POST'})"));
 const local=await readFile(new URL('../../backend/local_sync.py',import.meta.url),'utf8');
 assert.ok(local.includes("'local-sync'"));
 assert.ok(!local.includes('service_role'));
});
