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
const fieldControl=(m,label)=>nodes(m.find(n=>n.type==='label'&&text(n).startsWith(label))[0],n=>['select','textarea','input'].includes(n.type))[0];
async function enter(m,label,value,event='onChange'){fieldControl(m,label).props[event]({target:{value}});await m.settle()}
async function setDue(m,value){await enter(m,'Due date',value.slice(0,10));await enter(m,'Due time',value.slice(11,16))}
const futureDate=()=>new Date(Date.now()+7*86400000).toISOString().slice(0,16);
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
 await settle();return {settle,rerender(next){Object.assign(props,next);dirty=true;return settle()},tree:()=>tree,find:predicate=>nodes(tree,predicate),button:label=>nodes(tree,n=>n.type==='button'&&text(n).trim()===label)[0],text:()=>text(tree),close(){slots.forEach(s=>s?.cleanup?.())}};
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

test('case page selects a Team inspection inline and preserves the assignment panel above the evidence',async()=>{
 const f=teamFixture(),m=await mount('TeamWorkspace',{casesView:true},f);
 let panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];
 assert.equal(panel.props.inspection,null);assert.equal(panel.props.inspections[0].id,f.inspection.id);
 await panel.props.onSelectInspection(f.inspection.id);await m.settle();
 panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];
 assert.equal(panel.props.inspection.id,f.inspection.id);assert.equal(panel.props.inspectionLoading,false);
 assert.equal(f.scrolled,undefined,'picking an inspection should not jump past the assignment form');
 await panel.props.onEvidence(f.inspection.id);await m.settle();assert.equal(f.scrolled,true);m.close();
});

test('clearing the inspection picker removes its evidence and review instead of keeping a hidden selection',async()=>{
 const f=teamFixture(),m=await mount('TeamWorkspace',{casesView:true},f);
 let panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];await panel.props.onSelectInspection(f.inspection.id);await m.settle();
 panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];assert.ok(panel.props.inspection);
 panel.props.onSelectInspection('');await m.settle();panel=m.find(n=>n.type?.name==='CorrectiveActions')[0];
 assert.equal(panel.props.inspection,null);assert.equal(panel.props.inspectionLoading,false);assert.deepEqual(panel.props.notes,[]);
 assert.equal(m.find(n=>n.type?.name==='ReviewForm').length,0);m.close();
});

test('direct case visit shows assignment fields with guidance, without permitting an unreviewed or private case',async()=>{
 const f=teamFixture(),chosen=[];
 const m=await mount('CorrectiveActions',{user:f.actor(),inspections:[f.inspection],onSelectInspection:id=>chosen.push(id)},f);
 assert.match(m.text(),/Create and assign a case/);assert.match(m.text(),/Choose a shared Team inspection/);
 for(const label of ['Person responsible','Supervisor','Due date','Due time']){
  const node=m.find(n=>n.type==='label'&&text(n).startsWith(label))[0];assert.ok(node,label);
  assert.equal(nodes(node,n=>['select','input'].includes(n.type))[0].props.disabled,false,label);
 }
 assert.equal(m.button('Create corrective action').props.disabled,true);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,0);
 const picker=m.find(n=>n.type==='label'&&text(n).startsWith('Team inspection'))[0];
 nodes(picker,n=>n.type==='select')[0].props.onChange({target:{value:f.inspection.id}});assert.deepEqual(chosen,[f.inspection.id]);
 nodes(picker,n=>n.type==='select')[0].props.onChange({target:{value:''}});assert.deepEqual(chosen,[f.inspection.id,'']);
 assert.match(m.text(),/does not send an email by itself/);assert.match(m.text(),/targets the supervisor/);m.close();
});

test('review prerequisites, archived records and in-flight selection keep assignment blocked',async()=>{
 const f=teamFixture(),review={body:reviewBody('Reviewed','Reject'),id:'review',created_at:'2026-10-26'};
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[]},f);
 assert.match(m.text(),/No completed defect review is saved/);assert.equal(m.button('Create corrective action').props.disabled,true);
 await m.rerender({notes:[review],inspectionLoading:true});assert.match(m.text(),/Opening the selected inspection/);
 assert.equal(m.button('Create corrective action').props.disabled,true);
 await m.rerender({inspectionLoading:false,inspection:{...f.inspection,archived_at:'2026-10-26'}});
 assert.match(m.text(),/inspection is archived/);assert.equal(m.button('Create corrective action').props.disabled,true);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,0);m.close();
});

test('authorized Staff can type a draft before selection and keep it when the first inspection/review arrives',async()=>{
 const f=teamFixture(),m=await mount('CorrectiveActions',{user:f.actor(),notes:[]},f),due=futureDate();
 for(const [label,value]of [['What needs fixing?','Draft handover before choosing a photo'],['Person responsible',f.actor().id],['Supervisor','22222222-2222-4222-8222-222222222222'],['Priority','High']])await enter(m,label,value,label==='What needs fixing?'?'onInput':'onChange');
 await setDue(m,due);
 await m.rerender({inspection:f.inspection});
 assert.equal(fieldControl(m,'What needs fixing?').props.value,'Draft handover before choosing a photo');
 await m.rerender({notes:[{id:'review',created_at:'2026-10-26',body:reviewBody('Reviewed','Reject')}]});
 assert.equal(fieldControl(m,'Due date').props.value,due.slice(0,10));assert.equal(fieldControl(m,'Due time').props.value,due.slice(11,16));assert.equal(fieldControl(m,'Priority').props.value,'High');
 assert.equal(m.button('Create corrective action').props.disabled,true,'human confirmation still required');
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 assert.equal(m.button('Create corrective action').props.disabled,false);m.close();
});

test('an accepted or held inspection explains its actual review without disabling draft fields or authorizing a case',async()=>{
 for(const decision of ['Accept','Hold']){
  const f=teamFixture(),m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[{id:'review',created_at:'2026-10-26',body:reviewBody('Reviewed',decision)}]},f);
  assert.match(m.text(),new RegExp('Latest Staff review: Reviewed / '+decision));
  assert.match(m.text(),/Keep a valid Accept or Hold decision unchanged/);
  assert.equal(fieldControl(m,'What needs fixing?').props.disabled,false);await enter(m,'What needs fixing?','A local draft must not rewrite the human review','onInput');
  await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
  assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,0);m.close();
 }
});

test('refresh retains assignment and update drafts; concurrent case versions require explicit replacement',async()=>{
 const f=teamFixture();f.cases.push({id:'case',inspection_id:f.inspection.id,owner_id:f.actor().id,supervisor_id:'22222222-2222-4222-8222-222222222222',state:'Assigned',version:1,due_at:'2027-01-01'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[]},f);
 await enter(m,'What needs fixing?','Draft must survive background refresh','onInput');
 m.button('Details').props.onClick();await m.settle();await enter(m,'What changed or was fixed?','Unsaved progress note','onInput');
 await m.button('Refresh cases').props.onClick();await m.settle();
 assert.equal(fieldControl(m,'What needs fixing?').props.value,'Draft must survive background refresh');
 assert.equal(fieldControl(m,'What changed or was fixed?').props.value,'Unsaved progress note');
 f.cases[0].version=2;await m.button('Refresh cases').props.onClick();await m.settle();
 assert.match(m.text(),/case changed while the update was being drafted/);
 assert.equal(fieldControl(m,'What changed or was fixed?').props.value,'Unsaved progress note');assert.equal(m.button('Save case update').props.disabled,true);
 await m.find(n=>n.type==='form'&&text(n).includes('Save case update'))[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.requests.filter(x=>x.rpc==='defectrag_update_corrective_action').length,0);
 m.button('Load latest case and replace draft').props.onClick();await m.settle();
 assert.equal(fieldControl(m,'What changed or was fixed?').props.value,'');assert.equal(m.button('Save case update').props.disabled,false);m.close();
});

test('invalid assignment drafts explain missing values before the create RPC can run',async()=>{
 const f=teamFixture(),m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[{id:'review',created_at:'2026-10-26',body:reviewBody('Reviewed','Reject')}]},f);
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 assert.match(m.text(),/10 to 2,000/);await enter(m,'What needs fixing?','A valid description for testing');assert.match(m.text(),/Choose an active Staff member as the person responsible/);
 await enter(m,'Person responsible',f.actor().id);assert.match(m.text(),/Choose an active Staff member as the supervisor/);
 await enter(m,'Supervisor','22222222-2222-4222-8222-222222222222');assert.match(m.text(),/Choose a due date and time/);
 await setDue(m,'2000-01-01T00:00');assert.match(m.text(),/Choose a future due date/);
 await setDue(m,new Date(Date.now()+366*86400000).toISOString().slice(0,16));assert.match(m.text(),/within the next year/);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();assert.equal(f.cases.length,0);m.close();
});

test('double submission sends one create request; server failure keeps the draft and permits a deliberate retry',async()=>{
 const f=teamFixture(),m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[{id:'review',created_at:'2026-10-26',body:reviewBody('Reviewed','Reject')}]},f);
 for(const [label,value]of [['What needs fixing?','Save this draft after a server rejection'],['Person responsible',f.actor().id],['Supervisor','22222222-2222-4222-8222-222222222222']])await enter(m,label,value);
 await setDue(m,futureDate());
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 const original=f.client.rpc;let count=0,release;
 f.client.rpc=async(name,payload)=>{if(name==='defectrag_create_corrective_action'){count++;await new Promise(resolve=>release=resolve);return {error:new Error('Temporary service unavailable')}}return original(name,payload)};
 const submit=m.find(n=>n.type==='form')[0].props.onSubmit;const first=submit({preventDefault(){}}),second=submit({preventDefault(){}});
 await m.settle();assert.equal(count,1);release();await Promise.all([first,second]);await m.settle();
 assert.equal(f.cases.length,0);assert.equal(fieldControl(m,'What needs fixing?').props.value,'Save this draft after a server rejection');
 assert.equal(m.button('Create corrective action').props.disabled,false);assert.match(m.text(),/Temporary service unavailable/);m.close();
});

test('an existing review case opens its assignment rather than offering a duplicate creation',async()=>{
 const f=teamFixture();f.notes.push({body:reviewBody('Reviewed','Reject'),id:'review',created_at:'2026-10-26'});
 f.cases.push({id:'case',review_id:'review',inspection_id:f.inspection.id,owner_id:f.actor().id,supervisor_id:'22222222-2222-4222-8222-222222222222',state:'Assigned',version:1,due_at:'2027-01-01'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:f.notes},f);
 assert.match(m.text(),/already has a case/);assert.equal(m.button('Create corrective action').props.disabled,true);
 m.button('Open existing case').props.onClick();await m.settle();assert.ok(m.button('Save case update'));
 assert.match(m.text(),/Person responsible: QA owner/);m.close();
});

test('switching inspections clears the prior assignment draft and requires a new explicit confirmation',async()=>{
 const f=teamFixture(),review={body:reviewBody('Reviewed','Reject'),id:'review',created_at:'2026-10-26'};
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:[review]},f);
 const inputFor=label=>nodes(m.find(n=>n.type==='label'&&text(n).startsWith(label))[0],n=>['select','textarea','input'].includes(n.type))[0];
 for(const [label,value]of [['What needs fixing?','Prior product draft'],['Person responsible',f.actor().id],['Supervisor','22222222-2222-4222-8222-222222222222'],['Due date','2027-01-01']]){
  inputFor(label).props.onChange({target:{value}});await m.settle();
 }
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 await m.rerender({inspection:{...f.inspection,id:'b'.repeat(32)},notes:[{...review,id:'other-review'}]});
 for(const label of ['What needs fixing?','Person responsible','Supervisor','Due date'])assert.equal(inputFor(label).props.value,'',label);
 assert.equal(m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.checked,false);
 assert.equal(m.button('Create corrective action').props.disabled,true);assert.equal(f.cases.length,0);m.close();
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

test('background refresh keeps the open case history on screen instead of collapsing the panel',async()=>{
 const f=teamFixture('owner');f.notes.push({body:reviewBody('Reviewed','Reject'),inspection_id:f.inspection.id,id:'note',created_at:'2026-10-26'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:f.notes},f);
 for(const [label,value] of [['What needs fixing?','Synthetic defect for refresh stability'],['Person responsible',f.actor().id],['Supervisor','22222222-2222-4222-8222-222222222222'],['Due date','2027-01-01']])await enter(m,label,value);
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.match(m.text(),/Synthetic case created/);
 let release;f.historyGate=new Promise(r=>release=r);
 m.button('Refresh cases').props.onClick();await m.settle();
 assert.match(m.text(),/Synthetic case created/,'history must stay visible while the same case refreshes');
 release();f.historyGate=null;await m.settle();
 assert.match(m.text(),/Synthetic case created/);m.close();
});

test('mounted case forms preserve explicit confirmation, audited updates and revocation clearing',async()=>{
 const f=teamFixture('owner');f.notes.push({body:reviewBody('Reviewed','Reject'),inspection_id:f.inspection.id,id:'note',created_at:'2026-10-26'});
 const m=await mount('CorrectiveActions',{user:f.actor(),inspection:f.inspection,notes:f.notes},f);
 async function field(label,value){const target=m.find(n=>n.type==='label'&&text(n).startsWith(label))[0];const input=nodes(target,n=>['select','textarea','input'].includes(n.type))[0];input.props.onChange({target:{value}});await m.settle()}
 await field('What needs fixing?','Synthetic confirmed defect for navigation QA');
 await field('Person responsible',f.actor().id);await field('Supervisor','22222222-2222-4222-8222-222222222222');await field('Due date','2027-01-01');await field('Due time','12:00');
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});await m.settle();
 assert.equal(m.button('Create corrective action').props.disabled,false);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.equal(f.cases.length,1);assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,1);assert.ok(m.button('Save case update'));
 const created=f.requests.find(x=>x.rpc==='defectrag_create_corrective_action').payload;
 assert.equal(created.p_owner,f.actor().id);assert.equal(created.p_supervisor,'22222222-2222-4222-8222-222222222222');
 assert.equal(created.p_due,new Date('2027-01-01T12:00').toISOString());assert.equal(created.p_inspection,f.inspection.id);
 assert.equal(m.button('Create corrective action').props.disabled,true,'saved review cannot create a duplicate case');
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

test('case picker labels each Team inspection, lists ready ones first and explains the next step',async()=>{
 const f=teamFixture(),a=f.inspection,b={...a,id:'b'.repeat(32),created_at:'2026-10-27T08:00:00Z'},c={...a,id:'c'.repeat(32),payload:{...a.payload,category:'candle'}};
 f.notes.push({id:'n-ready',inspection_id:a.id,author_id:f.actor().id,body:reviewBody('Reviewed','Reject'),created_at:'2026-10-26T09:00:00Z'},
  {id:'n-accept',inspection_id:c.id,author_id:f.actor().id,body:reviewBody('Reviewed','Accept'),created_at:'2026-10-26T09:00:00Z'});
 const evidence=[],m=await mount('CorrectiveActions',{user:f.actor(),notes:[],inspections:[b,c,a],onSelectInspection(){},onEvidence:id=>evidence.push(id)},f);
 const options=m.find(n=>n.type==='option').map(text).filter(t=>t.includes(' — '));
 assert.equal(options.length,3);assert.match(options[0],/^PCB 1 · .* — Ready: defect confirmed$/);
 assert.ok(options.some(t=>/^Candle · .* — Accepted: no case needed$/.test(t)));assert.ok(options.some(t=>/— Needs review$/.test(t)));
 assert.match(m.text(),/1 inspection is ready, listed first/);assert.match(m.text(),/Step 1: choose a Team inspection/);
 const consent=m.find(n=>n.type==='label'&&String(n.props.className).includes('consent-check'))[0];
 assert.match(consent.props.className,/locked/);assert.match(text(consent),/Available after the review step/);
 await m.rerender({inspection:b,notes:[]});
 assert.match(m.text(),/Step 2 needed: confirm the defect in a Staff review/);
 m.button('Open this inspection’s review').props.onClick();assert.deepEqual(evidence,[b.id]);
 await m.rerender({inspection:a,notes:f.notes.filter(n=>n.inspection_id===a.id)});
 assert.match(m.text(),/Ready to assign/);assert.doesNotMatch(String(m.find(n=>n.type==='label'&&String(n.props.className).includes('consent-check'))[0].props.className),/locked/);
 assert.equal(f.requests.filter(x=>x.rpc==='defectrag_create_corrective_action').length,0);m.close();
});

test('review decisions show plain wording while saved review values stay unchanged',async()=>{
 const saved=[],m=await mount('ReviewForm',{current:{status:'Reviewed',decision:'Reject',reviewer:'QA owner',created_at:'2026-10-26'},onSave:async v=>saved.push(v)},teamFixture());
 const decision=m.find(n=>n.type==='label'&&text(n).startsWith('Review decision'))[0];
 assert.deepEqual(nodes(decision,n=>n.type==='option').map(o=>[o.props.value,text(o)]),[['Hold','Hold: needs more checks'],['Accept','Accept: no defect'],['Reject','Reject: defect confirmed']]);
 assert.match(m.text(),/Reviewed · Reject: defect confirmed/);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});await m.settle();
 assert.deepEqual(saved,[{status:'Reviewed',decision:'Reject',note:''}]);
 assert.equal(reviewBody('Reviewed','Reject'),'DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject","note":""}');m.close();
});

test('signed-out Staff page puts Sign in before the optional registration section',async()=>{
 const f=teamFixture('guest'),m=await mount('TeamWorkspace',{},f);
 // The harness does not render nested components, so check tree order: sign-in form, then the AccountSecurity element.
 const order=m.find(()=>true),form=order.findIndex(n=>n.type==='form'&&n.props.className==='login-form'),security=order.findIndex(n=>typeof n.type==='function'&&'client' in n.props&&'user' in n.props);
 assert.ok(form>=0&&security>form,'sign-in form renders before account registration/security');
 assert.ok(order.some(n=>n.type==='h3'&&text(n)==='Sign in'));m.close();
});
