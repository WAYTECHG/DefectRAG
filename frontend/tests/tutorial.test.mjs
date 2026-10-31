import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {readFile,readdir} from 'node:fs/promises';
import {newPractice,practiceReducer,tutorialSteps} from '../src/tutorial.mjs';
import {PRACTICE_EXAMPLE,practiceActive,practiceApi,practiceClient,practiceRequest,startPracticeMode,stopPracticeMode} from '../src/practice.mjs';
import {reviewBody} from '../src/workflow.mjs';

const step=s=>tutorialSteps()[s.step];
const complete=(s,event,extra={})=>practiceReducer(s,{type:'complete',event,...extra});
const started=()=>practiceReducer(newPractice(),{type:'start'});

test('lesson steps run on the real task pages and complete only on matching actions',()=>{
 const steps=tutorialSteps();assert.equal(steps.length,14);assert.equal(new Set(steps.map(s=>s.id)).size,14);
 for(const page of ['inspect','history','team','cases','batch','alerts','overview'])assert.ok(steps.some(s=>s.page===page));
 assert.ok(steps.every(s=>s.event&&s.target&&s.title&&s.instruction));assert.equal(steps.at(-1).event,'finish');
 let s=started();assert.deepEqual(complete(s,'share'),s);assert.deepEqual(complete(s,'inspect'),s);
 for(const st of steps.slice(0,-1)){
  const extra=st.event==='product'?{value:'candle'}:st.event==='review'?{status:'Reviewed',decision:'Reject'}:st.event==='lifecycle'?{state:'Closed'}:{};
  s=complete(s,st.event,extra);
 }
 assert.equal(step(s).event,'finish');assert.equal(complete(s,'finish').step,13);
 assert.deepEqual(complete(newPractice(),'product',{value:'candle'}),newPractice(),'nothing advances before Start');
});
test('wrong choices give a hint instead of advancing; Back only moves the instructions',()=>{
 let s=complete(started(),'product',{value:'pcb1'});assert.equal(step(s).event,'product');assert.match(s.hint,/Candle/);
 s=complete(s,'product',{value:'candle'});assert.equal(step(s).event,'photo');assert.equal(s.hint,'');
 for(const e of ['photo','inspect','compare','ask','open','share','gallery'])s=complete(s,e);
 s=complete(s,'review',{status:'Reviewed',decision:'Accept'});assert.equal(step(s).event,'review');assert.match(s.hint,/Reject: defect confirmed/);
 s=complete(s,'review',{status:'Reviewed',decision:'Reject'});s=complete(s,'case');assert.equal(step(s).event,'lifecycle');
 for(const [state,next] of [['Assigned','In Progress'],['In Progress','Resolved'],['Resolved','Closed']]){s=complete(s,'lifecycle',{state});assert.equal(step(s).event,'lifecycle');assert.match(s.hint,new RegExp('choose '+next))}
 s=complete(s,'lifecycle',{state:'Closed'});assert.equal(step(s).event,'batch');
 const back=practiceReducer(s,{type:'back'});assert.equal(step(back).event,'lifecycle');assert.equal(back.caseState,'Closed');
});
test('old dismissal keys do not suppress the new lesson; blocked storage is harmless',async()=>{
 const t=await import('../src/tutorial.mjs?new-lesson-storage'),data=new Map([['defectrag-guided-practice-v2','done']]);const storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
 assert.equal(t.tutorialSeen(storage),false);t.rememberTutorial(storage);assert.equal(t.tutorialSeen(storage),true);assert.equal(data.get(t.TUTORIAL_KEY),'done');
 const other=await import('../src/tutorial.mjs?blocked-lesson-storage');const denied={getItem(){throw Error()},setItem(){throw Error()}};
 assert.equal(other.tutorialSeen(denied),false);assert.doesNotThrow(()=>other.rememberTutorial(denied));assert.equal(other.tutorialSeen(denied),true);
});
test('practice measurements are the saved public example, not an invented prediction',async()=>{
 const data=JSON.parse(await readFile(new URL('../public/showcase/data.json',import.meta.url),'utf8'));
 const original=data.records.find(r=>r.id==='7dbb6f27253b450698a1a503cfa9a8c8');
 for(const k of ['category','verdict','score','threshold','uncertainty_margin','inference_ms','model_id'])assert.equal(PRACTICE_EXAMPLE[k],original[k]);
 assert.ok(Object.isFrozen(PRACTICE_EXAMPLE));
});

test('the whole lesson runs against the in-memory store with no network, then ends cleanly',async()=>{
 const realFetch=globalThis.fetch,events=[];let network=0;
 globalThis.fetch=async url=>{if(String(url).startsWith('asset:'))return new Response(new Blob(['jpg']));network++;throw Error('network used: '+url)};
 try{
  startPracticeMode({assets:{original:'asset:original',heatmap:'asset:heatmap'},metadata:{samples:[{name:'candle_anomalous'}]},onEvent:e=>events.push(e)});
  assert.equal(practiceActive(),true);assert.equal((await practiceApi('/api/health')).practice,true);
  const wrong=new FormData();wrong.append('category','pcb1');wrong.append('batch','');
  await assert.rejects(practiceApi('/api/inspect',{method:'POST',body:wrong}),/choose Candle/);
  const form=new FormData();form.append('category','candle');form.append('batch','');
  const r=await practiceApi('/api/inspect',{method:'POST',body:form});
  assert.equal(r.score,PRACTICE_EXAMPLE.score);assert.equal(r.image_url,'asset:original');assert.equal(r.storage,'browser_session');
  assert.equal((await practiceApi('/api/assistant',{method:'POST',body:JSON.stringify({inspection_id:r.id,question:'Why?'})})).mode,'retrieval_only');
  assert.equal((await practiceApi('/api/inspections/'+r.id+'/messages')).length,2);
  assert.deepEqual(await practiceApi('/api/inspections/'+r.id+'/share',{method:'POST',body:'{}'}),{alreadyShared:false});
  await assert.rejects(practiceApi('/api/inspections/'+r.id+'/publication',{method:'POST',body:JSON.stringify({consent:false})}),/public/);
  assert.equal((await practiceApi('/api/inspections/'+r.id+'/publication',{method:'POST',body:JSON.stringify({consent:true})})).practice,true);
  const client=practiceClient();
  assert.equal((await client.from('shared_inspections').select('*').is('archived_at',null)).data.length,1);
  assert.equal((await client.rpc('defectrag_ca_staff')).data,true);
  await client.from('staff_notes').insert({inspection_id:r.id,body:reviewBody('Reviewed','Accept')});
  const accept=(await client.from('staff_notes').select('*').eq('inspection_id',r.id)).data[0];
  assert.match((await client.rpc('defectrag_create_corrective_action',{p_inspection:r.id,p_review:accept.id,p_confirmed:true})).error.message,/Reject/);
  await client.from('staff_notes').insert({inspection_id:r.id,body:reviewBody('Reviewed','Reject','Wax crack')});
  const reject=(await client.from('staff_notes').select('*').eq('inspection_id',r.id).like('body','DEFECTRAG_REVIEW_V1:%')).data.at(-1);
  const due=new Date(Date.now()+86400000).toISOString(),me=(await client.auth.getUser()).data.user.id;
  const others=(await client.from('staff_members').select('*')).data.filter(p=>p.user_id!==me);
  const blocked=(await client.rpc('defectrag_create_corrective_action',{p_inspection:r.id,p_review:reject.id,p_confirmed:true,p_owner:others[0].user_id,p_supervisor:others[1].user_id,p_priority:'High',p_description:'Repair the candle surface',p_due:due})).data;
  assert.match((await client.rpc('defectrag_update_corrective_action',{p_id:blocked,p_version:1,p_state:'Assigned',p_note:'Start'})).error.message,/person responsible, the supervisor/);
  const reject2=(await client.from('staff_notes').insert({inspection_id:r.id,body:reviewBody('Reviewed','Reject','Second check')})).data;
  const id=(await client.rpc('defectrag_create_corrective_action',{p_inspection:r.id,p_review:reject2.id,p_confirmed:true,p_owner:others[0].user_id,p_supervisor:me,p_priority:'High',p_description:'Repair the candle surface',p_due:due})).data;
  assert.match((await client.rpc('defectrag_update_corrective_action',{p_id:id,p_version:1,p_state:'Closed',p_note:'Skip'})).error.message,/allowed next status/);
  let version=1;for(const state of ['Assigned','In Progress','Resolved','Closed'])version=(await client.rpc('defectrag_update_corrective_action',{p_id:id,p_version:version,p_state:state,p_note:'Practice '+state})).data;
  assert.equal((await client.from('corrective_action_history').select('*').eq('case_id',id)).data.length,5);
  for(const n of [1,2]){const b=new FormData();b.append('category','candle');b.append('batch','LINE-PRACTICE');await practiceApi('/api/inspect',{method:'POST',body:b})}
  assert.equal((await practiceApi('/api/batch-name?name=line-practice')).available,false);
  const alert=(await practiceApi('/api/alerts'))[0];await practiceApi('/api/alerts/'+alert.id+'/acknowledge',{method:'POST'});
  assert.match(await (await practiceRequest('/api/export.csv')).text(),/not exported/);
  await assert.rejects(practiceApi('/api/local-sync/run',{method:'POST'}),/not part of the practice lesson/);
  const names=events.map(e=>e.event);
  for(const e of ['inspect','ask','share','gallery','review','case','lifecycle','batch','alert'])assert.ok(names.includes(e),e);
  assert.deepEqual(events.filter(e=>e.event==='review').map(e=>e.decision),['Accept','Reject','Reject']);
  assert.equal(events.filter(e=>e.event==='lifecycle').at(-1).state,'Closed');
  assert.equal(network,0,'no request left the browser');
 }finally{stopPracticeMode();globalThis.fetch=realFetch}
 assert.equal(practiceActive(),false);await assert.rejects(practiceApi('/api/health'),/lesson has ended/);assert.throws(()=>practiceClient(),/lesson has ended/);
});

test('cloud helpers and batch recovery switch to the lesson store only while practice runs',async()=>{
 globalThis.window=new EventTarget();window.DEFECTRAG_PUBLIC_CONFIG={};
 // Same loading as cloud.test.mjs: Vite env removed, lesson store shared by URL.
 const source=(await readFile(new URL('../src/cloud.js',import.meta.url),'utf8')).replaceAll('import.meta.env','({})')
  .replace("from './practice.mjs'","from '"+new URL('../src/practice.mjs',import.meta.url).href+"'");
 const cloud=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64')),batch=await import('../src/batchCheckpoint.js?practice-routing');
 assert.equal(cloud.cloudConfigured(),false,'no real Supabase configuration in this test');
 startPracticeMode({assets:{},onEvent(){}});
 try{
  assert.equal(cloud.cloudConfigured(),true);const client=await cloud.cloudClient();
  assert.equal((await client.auth.getSession()).data.session.access_token,'PRACTICE_NOT_A_TOKEN');
  assert.equal((await cloud.currentStaff()).staff.display_name,'You (practice)');
  assert.equal(await batch.batchOwner(),'practice');await batch.checkpointBatch('practice',{items:[]});assert.equal(await batch.restoreBatch('practice'),null);
 }finally{stopPracticeMode()}
 assert.equal(cloud.cloudConfigured(),false);
});

test('main routes every API call through the lesson store first and clears state on entry and exit',async()=>{
 const main=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.match(main,/async function request\(path,options=\{\}\) \{\r?\n if\(practiceActive\(\)\)return practiceRequest\(path,options\);/);
 const api=main.slice(main.indexOf('async function api('),main.indexOf('const response=await request(path,options);'));
 assert.match(api,/if\(practiceActive\(\)\) return practiceApi\(path,options\);/);
 const start=main.slice(main.indexOf(' function startPractice'),main.indexOf(' function practiceAction'));
 assert.match(start,/if\(busy\|\|ragBusy\|\|recordLoading\)return/);assert.ok(start.indexOf('startPracticeMode(')<start.indexOf('clearLessonState()'));
 const close=main.slice(main.indexOf(' function closeTutorial'),main.indexOf(' function clearLessonState'));
 assert.ok(close.indexOf('stopPracticeMode()')<close.indexOf('clearLessonState()'));
 assert.match(main,/key=\{page\+\(practiceRunning\?':practice':''\)\}/,'Staff pages remount with the lesson client');
 assert.doesNotMatch(main,/GuidedPractice/);
 assert.ok(main.includes("page!=='overview'||!health||busy||ragBusy||recordLoading||tutorialPrompted.current"));
});

test('every lesson step highlights a real control that exists in the application source',async()=>{
 const dir=new URL('../src/',import.meta.url),files=(await readdir(dir)).filter(f=>f.endsWith('.jsx'));
 const source=(await Promise.all(files.map(f=>readFile(new URL(f,dir),'utf8')))).join('\n');
 for(const s of tutorialSteps())assert.ok(source.includes(`data-tour="${s.target}"`)||source.includes(`'${s.target}'`)&&source.includes('data-tour={'),s.target);
});

const require=createRequire(new URL('../package.json',import.meta.url));
async function mounted(file,props){
 const out=await build({entryPoints:[fileURLToPath(new URL('../src/'+file,import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',external:['react','lucide-react'],loader:{'.jpg':'text'},logLevel:'silent'});
 const React=require('react'),slots=[];let cursor=0,tree;
 const fake={...React,createElement:(type,p,...children)=>({type,props:{...p,children}}),useState(v){const i=cursor++;if(!(i in slots))slots[i]=v;return [slots[i],n=>{slots[i]=typeof n==='function'?n(slots[i]):n}]},useRef(v){const i=cursor++;slots[i]||={current:v};return slots[i]},useEffect(){}};
 const mod={exports:{}};new Function('require','module','exports',out.outputFiles[0].text)(id=>id==='react'?fake:id==='lucide-react'?new Proxy({},{get:()=>()=>null}):require(id),mod,mod.exports);
 const nodes=(t,f)=>t==null||typeof t!=='object'?[]:Array.isArray(t)?t.flatMap(x=>nodes(x,f)):[...(f(t)?[t]:[]),...nodes(t.props?.children,f)];
 const text=n=>typeof n==='string'||typeof n==='number'?String(n):Array.isArray(n)?n.map(text).join(''):n?.props?text(n.props.children):'';
 const render=()=>{cursor=0;tree=mod.exports.default(props);return tree};render();
 return {render,find:f=>nodes(tree,f),text:()=>text(tree),button:label=>nodes(tree,n=>n.type==='button'&&text(n).trim().includes(label))[0]};
}
test('coach card guides from any page, offers Show me on the right page and Finish at the end',async()=>{
 const calls=[];let s=started();
 const off=await mounted('TutorialCoach.jsx',{state:s,page:'overview',onGo:p=>calls.push(p),onSkip(){},onFinish(){},onBack(){}});
 assert.match(off.text(),/STEP 1 OF 14/);assert.match(off.text(),/nothing is saved, shared, published or emailed/);
 off.button('Go to Image inspection').props.onClick();assert.deepEqual(calls,['inspect']);
 const on=await mounted('TutorialCoach.jsx',{state:s,page:'inspect',onGo(){},onSkip(){},onFinish(){},onBack(){}});assert.ok(on.button('Show me'));
 for(const st of tutorialSteps().slice(0,-1))s=complete(s,st.event,{value:'candle',status:'Reviewed',decision:'Reject',state:'Closed'});
 let finished=0;const end=await mounted('TutorialCoach.jsx',{state:s,page:'alerts',onGo(){},onSkip(){},onFinish(){finished++},onBack(){}});
 end.button('Finish tutorial').props.onClick();assert.equal(finished,1);
});
test('shared image viewer reports actual divider use; normal viewers need no callback',async()=>{
 const record={...PRACTICE_EXAMPLE,id:'x',image_url:'a.jpg',heatmap_url:'b.jpg'};let used=0;
 const m=await mounted('InspectionViewer.jsx',{record,url:x=>x,heatmap:true,onComparisonUsed(){used++}});
 m.button('Compare images').props.onClick();m.render();m.find(n=>n.type==='input'&&n.props.type==='range')[0].props.onChange({target:{value:'65'}});assert.equal(used,1);
 const normal=await mounted('InspectionViewer.jsx',{record,url:x=>x,heatmap:true});normal.button('Compare images').props.onClick();normal.render();
 assert.doesNotThrow(()=>normal.find(n=>n.type==='input'&&n.props.type==='range')[0].props.onChange({target:{value:'40'}}));
});
test('practice images are bundled build assets identical to the public example files',async()=>{
 const result=await build({entryPoints:[fileURLToPath(new URL('../src/main.jsx',import.meta.url))],bundle:true,write:false,platform:'browser',format:'esm',outdir:'test-output',assetNames:'assets/[name]-[hash]',loader:{'.jpg':'file','.css':'empty'},define:{'import.meta.env':'{"MODE":"test"}'},external:['@supabase/supabase-js'],logLevel:'silent'});
 const images=result.outputFiles.filter(f=>f.path.endsWith('.jpg'));assert.equal(images.length,2);
 for(const name of ['7dbb6f27253b450698a1a503cfa9a8c8.jpg','7dbb6f27253b450698a1a503cfa9a8c8_heatmap.jpg']){
  const bytes=await readFile(new URL('../public/showcase/images/'+name,import.meta.url));assert.ok(images.some(f=>Buffer.from(f.contents).equals(bytes)),name);
 }
});
