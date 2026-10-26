import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {inspectionReadiness,teamInspectionGuidance,loadInspectionAccess,watchInspectionAccess} from '../src/inspectionReadiness.mjs';
import {createRequestScope} from '../src/workflow.mjs';

const file=new File(['fixture image bytes'],'fixture.jpg',{type:'image/jpeg'});
const healthy={status:'ok',mode:'cloud_session_workspace',personal_workspace_enabled:true,auth_workflow_enabled:true,encoder_configured:true};
const base={health:healthy,workspace:'personal',access:{state:'authorized'},files:[file],categoryValid:true};
const readiness=values=>inspectionReadiness({...base,...values});
const tick=()=>new Promise(resolve=>setImmediate(resolve));

test('Team inspection is deliberately blocked; Personal keeps explicit-sharing semantics',()=>{
 assert.equal(readiness({workspace:'team'}).reason,teamInspectionGuidance);
 assert.equal(readiness({workspace:'team',files:[]}).code,'team');
 assert.equal(readiness({}).disabled,false);
 assert.equal(readiness({health:{...healthy,personal_workspace_enabled:false},workspace:'team'}).disabled,false,'Legacy cloud mode has no Personal routing restriction');
});

const cases=[
 [{busy:true},'processing'],[{ragBusy:true},'evidence_processing'],[{recordLoading:true},'record_loading'],
 [{health:null},'connecting'],[{health:{...healthy,status:'error'}},'service'],[{health:{...healthy,encoder_configured:false}},'service'],
 [{connectionFailed:true},'service'],[{offline:true},'offline'],[{access:{state:'checking'}},'checking'],
 [{access:{state:'pending'}},'pending'],[{access:{state:'mfa'}},'mfa'],[{access:{state:'revoked'}},'revoked'],
 [{access:{state:'rejected'}},'rejected'],[{access:{state:'denied'}},'denied'],[{access:{state:'unavailable'}},'unavailable'],
 [{files:[]},'images'],[{files:[new File([],'empty.jpg',{type:'image/jpeg'})]},'size'],
 [{files:[{name:'large.jpg',type:'image/jpeg',size:11*1024*1024}]},'size'],
 [{files:[{name:'note.txt',type:'text/plain',size:20}]},'format'],[{categoryValid:false},'category'],
 [{files:[file,file]},'single'],[{multiple:true,batch:''},'batch'],[{batch:'x'.repeat(81)},'batch_length'],
 [{multiple:true,batch:'B',files:Array(21).fill(file)},'count'],
 [{multiple:true,batch:'B',files:Array(3).fill({name:'a.png',type:'image/png',size:8*1024*1024})},'total'],
];
for(const [input,code]of cases)test(`disabled inspection explains ${code}: ${JSON.stringify(input)}`,()=>{
 const actual=readiness(input);assert.equal(actual.code,code);assert.equal(actual.disabled,true);assert.ok(actual.reason.length>15);
});
test('guest demo and offline local inference remain available; batch retry still enforces authorization',()=>{
 assert.equal(readiness({access:{state:'guest'}}).disabled,false);
 assert.equal(readiness({offline:true,health:{status:'ok',mode:'local_single_user'},access:{state:'pending'}}).disabled,false);
 assert.equal(readiness({multiple:true,retry:true,files:[]}).disabled,false);
 assert.equal(readiness({multiple:true,retry:true,files:[],access:{state:'mfa'}}).code,'mfa');
 assert.equal(readiness({files:[{name:'camera.JPG',type:'',size:5}]}).disabled,false);
});

const posture={approved:true,revoked:false,authorized:true,aal2:true,mfa_required:true,role:'developer'};
const client=p=>({auth:{getSession:async()=>({data:{session:{}}})},rpc:async()=>({data:p})});
test('native Supabase posture, not browser metadata, decides signed-in readiness',async()=>{
 assert.equal((await loadInspectionAccess(client(posture))).state,'authorized');
 assert.equal((await loadInspectionAccess(client({...posture,role:'staff'}))).state,'authorized');
 for(const role of ['applicant','admin',null])assert.equal((await loadInspectionAccess(client({...posture,role}))).state,'denied');
 assert.equal((await loadInspectionAccess(client({...posture,aal2:false}))).state,'mfa');
 assert.equal((await loadInspectionAccess(client({...posture,approved:false,request_status:'pending'}))).state,'pending');
 assert.equal((await loadInspectionAccess(client({...posture,revoked:true}))).state,'revoked');
 assert.equal((await loadInspectionAccess(client({...posture,approved:false,request_status:'rejected'}))).state,'rejected');
 assert.equal((await loadInspectionAccess(client({...posture,mfa_required:undefined}))).state,'unavailable');
 assert.equal((await loadInspectionAccess(client({...posture,authorized:false}))).state,'denied');
 const guest={auth:{getSession:async()=>({data:{session:null}})},rpc:()=>assert.fail('Guest must not call private RPC')};
 assert.equal((await loadInspectionAccess(guest)).state,'guest');
 await assert.rejects(loadInspectionAccess({auth:{getSession:async()=>({error:new Error('Expired session')})}}),/Expired/);
 await assert.rejects(loadInspectionAccess(client(null)));
});

test('late authorization cannot enable inspection after identity change or unmount',async()=>{
 const target=new EventTarget(),doc=new EventTarget();target.navigator={onLine:true};doc.hidden=false;
 const states=[];let release,calls=0;
 const stop=watchInspectionAccess(async()=>{if(++calls===1)return new Promise(resolve=>release=resolve);return {state:'pending'}},s=>states.push(s.state),{target,documentTarget:doc,interval:100000});
 try{
  target.dispatchEvent(new Event('defectrag-auth-change'));release({state:'authorized'});await tick();
  assert.deepEqual(states,['checking','pending']);assert.equal(calls,2);
 }finally{stop()}
 const late=[];let finish;
 const stopLate=watchInspectionAccess(()=>new Promise(resolve=>finish=resolve),v=>late.push(v),{target,documentTarget:doc,interval:100000});
 stopLate();finish({state:'authorized'});await tick();assert.deepEqual(late,[]);
});
test('authorization outage blocks inspection; reconnect refreshes and can recover',async()=>{
 const target=new EventTarget(),doc=new EventTarget();target.navigator={onLine:true};doc.hidden=false;
 const states=[];let fail=true;
 const stop=watchInspectionAccess(async()=>{if(fail)throw new Error('Provider down');return {state:'authorized'}},s=>states.push(s.state),{target,documentTarget:doc,interval:100000});
 try{
  await tick();assert.equal(states.at(-1),'unavailable');
  target.navigator.onLine=false;target.dispatchEvent(new Event('offline'));assert.equal(states.at(-1),'unavailable');
  fail=false;target.navigator.onLine=true;target.dispatchEvent(new Event('online'));await tick();assert.equal(states.at(-1),'authorized');
 }finally{stop()}
});

const root=fileURLToPath(new URL('..',import.meta.url));
const built=await build({stdin:{contents:"export {default} from './src/InspectionAction.jsx';",resolveDir:root,loader:'jsx'},bundle:true,write:false,platform:'node',format:'cjs',external:['react']});
const require=createRequire(new URL('../package.json',import.meta.url));
const module={exports:{}};new Function('require','module','exports',built.outputFiles[0].text)(require,module,module.exports);
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),Component=module.exports.default;
const render=state=>renderToStaticMarkup(React.createElement(Component,{readiness:state,onRun(){},onSwitch(){}}));
test('real action JSX explains the disabled Team button and exposes an accessible switch',()=>{
 const html=render(readiness({workspace:'team'}));
 for(const phrase of [teamInspectionGuidance,'Switch to Personal Workspace','aria-describedby="inspection-run-reason"','id="inspection-run-reason"','role="status"','secondary wide'])assert.ok(html.includes(phrase),phrase);
 assert.ok(/disabled=""[^>]*>/.test(html));
 const enabled=render(readiness({}));assert.ok(!enabled.includes('disabled=""'));assert.ok(!enabled.includes('Switch to Personal Workspace'));
 for(const [input]of cases){const h=render(readiness(input));assert.ok(h.includes('inspection-run-reason'));assert.ok(h.includes('role="status"'))}
});

const source=(await readFile(new URL('../src/main.jsx',import.meta.url),'utf8')).replaceAll('\r\n','\n');
function actualSwitch({workspace='team',busy=false,ragBusy=false,recordLoading=false}={}){
 const draft={files:[file],category:'capsules',batch:'PRIVATE-DRAFT',result:{id:'old'},messages:['private evidence'],rows:[{id:'old'}],scope:workspace};
 const scope=createRequestScope(),old=scope.capture();
 const declaration=source.slice(source.indexOf(' function changeWorkspace('),source.indexOf(' function openTeamRecord('));
 const handlers=new Function('workspace','busy','ragBusy','recordLoading','setWorkspace','setWorkspaceState','clearWorkspace','resetInspection','setFiles','setFilter',declaration+';return {changeWorkspace,switchToPersonalWorkspace}')(
  workspace,busy,ragBusy,recordLoading,value=>draft.scope=value,()=>{},()=>{draft.rows=[]},()=>{scope.invalidate();draft.result=null;draft.messages=[]},value=>draft.files=value,()=>{});
 return {draft,handlers,old};
}
test('actual Team-to-Personal handler keeps File identity/category/batch but invalidates saved private context',()=>{
 const {draft,handlers,old}=actualSwitch();handlers.switchToPersonalWorkspace();
 assert.equal(draft.scope,'personal');assert.equal(draft.files[0],file);assert.equal(draft.category,'capsules');assert.equal(draft.batch,'PRIVATE-DRAFT');
 assert.equal(draft.result,null);assert.deepEqual(draft.messages,[]);assert.deepEqual(draft.rows,[]);assert.equal(old(),false);
});
test('scope changes never move an existing result or send/upload/share a draft',()=>{
 const {draft,handlers}=actualSwitch({workspace:'personal'});handlers.changeWorkspace('team');
 assert.equal(draft.scope,'team');assert.deepEqual(draft.files,[]);assert.equal(draft.result,null);
 // The actual handler is evaluated without any API/upload/sharing globals.
 for(const flag of ['busy','ragBusy','recordLoading']){
  const state=actualSwitch({[flag]:true});state.handlers.switchToPersonalWorkspace();assert.equal(state.draft.scope,'team');assert.equal(state.old(),true);
 }
});
test('actual submit handler rejects Team/pending/MFA/unavailable before API or inference',async()=>{
 const body=source.slice(source.indexOf(' async function inspect('),source.indexOf(' async function ask('));
 for(const code of ['team','pending','mfa','unavailable']){
  const errors=[];const inspect=new Function('busy','currentReadiness','setError',body+';return inspect')(false,()=>({disabled:true,reason:code}),value=>errors.push(value));
  await inspect();assert.deepEqual(errors,[code]);
 }
});
