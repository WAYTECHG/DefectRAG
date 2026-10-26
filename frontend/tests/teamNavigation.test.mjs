import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {caseInterfaceEnabled,sharedAssistantAvailable,focusInspectionDetails} from '../src/teamNavigation.mjs';
import {teamFixture} from './fixtures/teamWorkspaceClient.mjs';
import {reviewBody} from '../src/workflow.mjs';

const require=createRequire(new URL('../package.json',import.meta.url));
const React=require('react');
const tick=()=>new Promise(r=>setImmediate(r));
const compiled={};
async function component(name){
 if(compiled[name])return compiled[name];
 const out=await build({entryPoints:[fileURLToPath(new URL('../src/'+name+'.jsx',import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',external:['react'],logLevel:'silent',plugins:[{name:'fixture-cloud-and-poll',setup(b){
  b.onResolve({filter:/^\.\/cloud\.js$/},a=>a.importer.includes('node_modules')?undefined:({path:'cloud',namespace:'fixture'}));
  b.onResolve({filter:/^\.\/workspace\.mjs$/},()=>({path:'poll',namespace:'fixture'}));
  b.onLoad({filter:/.*/,namespace:'fixture'},a=>({contents:a.path==='cloud'?
   'export const cloudConfigured=()=>true; export const cloudClient=async()=>globalThis.__teamFixture.client; export const currentStaff=()=>globalThis.__teamFixture.currentStaff(); export function workspaceChanged(){}':
   'export function startPolling(load,{onState=()=>{}}={}){let stopped=false;const refresh=()=>Promise.resolve().then(load).then(()=>{if(!stopped)onState({state:"synced",at:Date.now()})}).catch(e=>{if(!stopped)onState({error:e.message})});refresh();return {refresh,stop(){stopped=true}}}'}));
 }}]});
 compiled[name]=out.outputFiles[0].text;return compiled[name];
}
function nodes(tree,predicate){
 if(tree===null||tree===undefined||typeof tree==='boolean')return [];
 if(Array.isArray(tree))return tree.flatMap(t=>nodes(t,predicate));
 if(typeof tree!=='object')return [];
 return [...(predicate(tree)?[tree]:[]),...nodes(tree.props?.children,predicate)];
}
const text=node=>typeof node==='string'||typeof node==='number'?String(node):Array.isArray(node)?node.map(text).join(''):node&&typeof node==='object'?text(node.props?.children):'';
async function mount(name,props,f){
 globalThis.__teamFixture=f;
 globalThis.window=new EventTarget();window.DEFECTRAG_PUBLIC_CONFIG={authWorkflowEnabled:true};window.matchMedia=()=>({matches:true});
 const slots=[];let cursor=0,dirty=true,effects=[],tree;
 const fake={...React,createElement(type,props,...children){const n={type,props:{...props,children}};if(typeof type==='string'&&props?.ref)props.ref.current={focus(){f.focused=type},scrollIntoView(){f.scrolled=true}};return n},
  useState(initial){const i=cursor++;if(!(i in slots))slots[i]=typeof initial==='function'?initial():initial;return [slots[i],v=>{const next=typeof v==='function'?v(slots[i]):v;if(!Object.is(next,slots[i])){slots[i]=next;dirty=true}}]},
  useRef(initial){const i=cursor++;slots[i]||={current:initial};return slots[i]},
  useEffect(fn,deps){const i=cursor++,old=slots[i];if(!old||!deps||deps.some((x,j)=>!Object.is(x,old.deps?.[j]))){slots[i]={deps,cleanup:old?.cleanup};effects.push(()=>{old?.cleanup?.();slots[i].cleanup=fn()})}}};
 const mod={exports:{}};new Function('require','module','exports',await component(name))(id=>id==='react'?fake:require(id),mod,mod.exports);
 async function settle(){for(let round=0;round<40;round++){if(dirty){cursor=0;dirty=false;tree=mod.exports.default(props)}while(effects.length)effects.shift()();await tick();if(!dirty&&!effects.length)return tree}throw Error('Fixture failed to settle')}
 await settle();return {settle,tree:()=>tree,find:predicate=>nodes(tree,predicate),button:label=>nodes(tree,n=>n.type==='button'&&text(n).trim()===label)[0],text:()=>text(tree),close(){slots.forEach(s=>s?.cleanup?.())}};
}

test('case route availability respects explicit opt-out and supports existing configs without an added flag',()=>{
 assert.equal(caseInterfaceEnabled({}),true);assert.equal(caseInterfaceEnabled({correctiveActionsEnabled:false}),false);
 assert.equal(sharedAssistantAvailable({local_sync_enabled:true}),true);assert.equal(sharedAssistantAvailable({mode:'cloud_session_workspace'}),true);
 assert.equal(sharedAssistantAvailable({local_sync_enabled:true},true),false);assert.equal(sharedAssistantAvailable({mode:'local_single_user'}),false);
});
test('details receive focus and reduced-motion-compatible scrolling',()=>{
 globalThis.window=new EventTarget();window.matchMedia=()=>({matches:true});const calls=[];
 focusInspectionDetails({focus:o=>calls.push(o),scrollIntoView:o=>calls.push(o)});
 assert.deepEqual(calls,[{preventScroll:true},{block:'start',behavior:'auto'}]);focusInspectionDetails(null);
});
test('actual Staff Review handler loads authorized details, scrolls them into view and submits a structured review',async()=>{
 const f=teamFixture(),opened=[];const m=await mount('TeamWorkspace',{onOpenCorrectiveActions:row=>opened.push(row)},f);
 assert.ok(m.button('Review'));await m.button('Review').props.onClick();await m.settle();
 assert.match(m.text(),/Shared inspection/);assert.equal(f.scrolled,true);assert.equal(f.focused,'section');
 const form=m.find(n=>n.type?.name==='ReviewForm')[0];assert.ok(form);
 await form.props.onSave({status:'Reviewed',decision:'Reject',note:'Synthetic reviewed defect'});await m.settle();
 assert.equal(f.notes.at(-1).body,reviewBody('Reviewed','Reject','Synthetic reviewed defect'));
 m.button('Create or view corrective actions').props.onClick();assert.equal(opened[0].id,f.inspection.id);m.close();
});
test('case route retains the chosen Team inspection and mounts the existing case component, without account-page clutter',async()=>{
 const f=teamFixture();f.notes.push({id:'note',inspection_id:f.inspection.id,author_id:f.actor().id,created_at:'2026-10-26',body:reviewBody('Reviewed','Reject')});
 const m=await mount('TeamWorkspace',{casesView:true,initialInspectionId:f.inspection.id},f);
 const panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];assert.equal(panel.props.inspection.id,f.inspection.id);assert.equal(panel.props.notes.length,1);
 assert.equal(m.find(n=>n.type?.name==='AccountSecurity').length,0);assert.equal(m.button('Review'),undefined);assert.equal(f.scrolled,undefined,'case creation must not scroll past its form to the inspection below');m.close();
});
test('pending and password-only accounts cannot mount case data or review controls',async()=>{
 for(const role of ['pending','mfa','revoked','guest']){
  const f=teamFixture(role),m=await mount('TeamWorkspace',{casesView:true,initialInspectionId:f.inspection.id},f);
  assert.equal(m.find(n=>n.type?.name==='CorrectiveActions'||n.type?.name==='ReviewForm').length,0,role);
  assert.equal(f.requests.filter(x=>x.table==='shared_inspections'||x.table==='corrective_actions').length,0,role);m.close();
 }
});
test('explicit configuration disable explains unavailable interface without touching backend permissions',async()=>{
 const f=teamFixture(),m=await mount('TeamWorkspace',{casesView:true},f);
 window.DEFECTRAG_PUBLIC_CONFIG.correctiveActionsEnabled=false;
 m.button('Refresh').props.onClick();await m.settle();
 assert.match(m.text(),/turned off for this app/);assert.equal(m.find(n=>n.type?.name==='CorrectiveActions').length,0);m.close();
});
test('native CA denial occurs before case table reads and hides creation controls',async()=>{
 const f=teamFixture('mfa'),m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[]},f);
 assert.equal(f.requests.filter(x=>x.table).length,0);assert.ok(f.requests.some(x=>x.rpc==='defectrag_ca_staff'));
 assert.equal(m.find(n=>n.type==='form').length,0);assert.match(m.text(),/security code/);m.close();
});
test('eligible human review reaches the original create RPC only with explicit confirmation',async()=>{
 const f=teamFixture('owner');f.notes.push({body:reviewBody('Reviewed','Reject'),inspection_id:f.inspection.id,id:'note',created_at:'2026-10-26'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:f.notes},f);
 assert.ok(m.button('Create corrective action').props.disabled);assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,0);
 m.close();
});
test('unassigned Staff see cases and audited details but not role-protected update controls',async()=>{
 for(const role of ['owner','supervisor','developer','unassigned']){
  const f=teamFixture(role);f.setRole(role);f.cases.push({id:'case',inspection_id:f.inspection.id,owner_id:f.inspection.owner_id,supervisor_id:'22222222-2222-4222-8222-222222222222',state:'Assigned',version:1,priority:'Normal',due_at:'2027-01-01',created_at:'2026-10-26'});
  const m=await mount('CorrectiveActions',{user:f.actor(),onEvidence(){}},f);m.button('Details').props.onClick();await m.settle();
  assert.equal(Boolean(m.button('Save case update')),role!=='unassigned');assert.equal(f.scrolled,true);
  if(role==='unassigned')assert.match(m.text(),/Only the person responsible/);m.close();
 }
});

test('mounted case forms preserve explicit confirmation, audited updates and revocation clearing',async()=>{
 const f=teamFixture('owner');f.notes.push({body:reviewBody('Reviewed','Reject'),inspection_id:f.inspection.id,id:'note',created_at:'2026-10-26'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:f.notes},f);
 async function field(label,value){const target=m.find(n=>n.type==='label'&&text(n).startsWith(label))[0];const input=nodes(target,n=>['select','textarea','input'].includes(n.type))[0];input.props.onChange({target:{value}});await m.settle()}
 await field('What needs fixing?','Synthetic confirmed defect for navigation QA');
 await field('Person responsible',f.actor().id);await field('Supervisor','22222222-2222-4222-8222-222222222222');await field('Due date and time','2027-01-01T12:00');
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 assert.equal(m.button('Create corrective action').props.disabled,false);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.cases.length,1);assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,1);assert.ok(m.button('Save case update'));
 await field('Case status','Assigned');await field('What changed or was fixed?','Synthetic assignment checked');
 const update=m.find(n=>n.type==='form'&&text(n).includes('Save case update'))[0];await update.props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.cases[0].state,'Assigned');assert.equal(f.history.at(-1).note,'Synthetic assignment checked');assert.match(m.text(),/Status history/);
 f.setRole('revoked');window.dispatchEvent(new Event('defectrag-auth-change'));await m.settle();
 assert.equal(m.button('Save case update'),undefined);assert.doesNotMatch(m.text(),/Synthetic confirmed defect for navigation QA/);m.close();
});
test('actual app exposes sidebar/hash route and connects local History Review and case-selection callbacks',async()=>{
 const s=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.ok(s.includes("['cases','Corrective Actions',ClipboardCheck]"));assert.ok(s.includes("casesView={page==='cases'}"));
 assert.ok(s.indexOf("['alerts','Review alerts'")<s.indexOf("['cases','Corrective Actions'"));assert.ok(s.indexOf("['cases','Corrective Actions'")<s.indexOf("['performance','Model performance'"));
 assert.ok(s.includes('onOpenInspection={sharedAssistantAvailable(health,SHOWCASE)?openTeamRecord:undefined}'));
 assert.ok(s.includes('initialInspectionId={sharedSelectionId}'));assert.ok(s.includes('?openSharedReview:openRecord'));
 const calls=[],go=p=>calls.push(p),setSharedSelectionId=id=>calls.push(id);
 for(const [name,arg,expected]of [['openSharedReview',{id:'shared'},['shared','team']],['openCorrectiveActions',{id:'shared'},['shared','cases']],['chooseTeamInspection',undefined,[null,'team']]]){
  calls.length=0;const body=s.match(new RegExp('function '+name+'\\([^)]*\\)\\{([^}]+)\\}'))[0];new Function('go','setSharedSelectionId','arg',body+';return '+name+'(arg)')(go,setSharedSelectionId,arg);assert.deepEqual(calls,expected);
 }
});
