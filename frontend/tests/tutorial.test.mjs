import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {readFile} from 'node:fs/promises';
import {newPractice,practiceReducer,tutorialSteps,practiceRecord} from '../src/tutorial.mjs';

const step=s=>tutorialSteps()[s.step],field=(s,name,value)=>practiceReducer(s,{type:'field',name,value});
function complete(s,event,extra={}){return practiceReducer(s,{type:'complete',event,...extra})}
function throughReview(){
 let s=practiceReducer(newPractice(),{type:'start'});
 s=complete(field(s,'category','candle'),'product');s=complete(s,'photo');s=complete(s,'inspect');s=complete(s,'compare',{value:true});
 s=complete(field(s,'question','What do the highlights show?'),'ask');s=complete(s,'save');s=complete(s,'open');s=complete(s,'share');
 s=field(field(field(s,'reviewStatus','Reviewed'),'decision','Reject'),'reviewNote','Practice surface needs a check.');return complete(s,'review');
}
function assigned(){let s=throughReview();for(const [k,v] of Object.entries({description:'Practice product needs repair.',owner:'Alex (practice)',supervisor:'Sam (practice)',due:'2099-01-01T12:00',confirmed:true}))s=field(s,k,v);return complete(s,'case')}

test('guided steps route through the actual task pages and finish only on actions',()=>{
 const steps=tutorialSteps();assert.equal(steps.length,17);assert.equal(new Set(steps.map(s=>s.id)).size,17);
 for(const page of ['inspect','history','team','cases','batch','alerts','gallery','overview'])assert.ok(steps.some(s=>s.page===page));
 assert.ok(steps.every(s=>s.event&&s.target&&s.instruction));assert.equal(steps[6].page,'history');assert.equal(steps[7].page,'inspect');assert.equal(steps[8].page,'team');
 const text=JSON.stringify(steps);for(const phrase of ['save in Personal Workspace automatically','explicit choice','approved Staff','does not approve','not a live camera','Model performance','Official benchmark'])assert.ok(text.includes(phrase));
});
test('public teaching measurements and image paths match the bundled original, not invented predictions',async()=>{
 const data=JSON.parse(await readFile(new URL('../public/showcase/data.json',import.meta.url),'utf8'));
 const original=data.records.find(r=>r.id==='7dbb6f27253b450698a1a503cfa9a8c8');
 for(const k of ['score','threshold','model_id','verdict'])assert.equal(practiceRecord[k],original[k]);
 for(const k of ['image_url','heatmap_url']){assert.equal(practiceRecord[k],'./'+original[k]);assert.ok((await readFile(new URL('../public/'+original[k],import.meta.url))).length>0)}
 assert.ok(Object.isFrozen(practiceRecord));
});
test('old text-tour dismissal does not suppress the new practice invitation; blocked storage is harmless',async()=>{
 const t=await import('../src/tutorial.mjs?new-lesson-storage'),data=new Map([['defectrag-tutorial-v1','done']]);const storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
 assert.equal(t.tutorialSeen(storage),false);t.rememberTutorial(storage);assert.equal(t.tutorialSeen(storage),true);assert.equal(data.get(t.TUTORIAL_KEY),'done');
 const other=await import('../src/tutorial.mjs?blocked-lesson-storage');const denied={getItem(){throw Error()},setItem(){throw Error()}};
 assert.equal(other.tutorialSeen(denied),false);assert.doesNotThrow(()=>other.rememberTutorial(denied));assert.equal(other.tutorialSeen(denied),true);
});
test('wrong or premature actions cannot skip a lesson, inspect without a photo or infer a product choice',()=>{
 let s=practiceReducer(newPractice(),{type:'start'});assert.deepEqual(complete(s,'share'),s);assert.deepEqual(complete(s,'inspect'),s);
 s=field(s,'category','pcb1');assert.deepEqual(complete(s,'product'),s);s=complete(field(s,'category','candle'),'product');assert.equal(step(s).event,'photo');
 assert.deepEqual(complete(s,'ask'),s);s=complete(s,'photo');assert.equal(step(s).event,'inspect');s=complete(s,'inspect');assert.equal(step(s).event,'compare');
 assert.deepEqual(complete(s,'compare',{value:false}),s);assert.equal(step(complete(s,'compare',{value:true})).event,'ask');
});
test('invalid reviews, unconfirmed defects, missing assignments and past due dates cannot complete case steps',()=>{
 let s=throughReview();assert.equal(step(s).event,'case');assert.match(complete(s,'case').error,/Complete/);
 for(const [k,v] of Object.entries({description:'Practice repair needed.',owner:'Alex (practice)',supervisor:'Sam (practice)',due:'2099-01-01T12:00'}))s=field(s,k,v);
 assert.equal(step(complete(s,'case')).event,'case');s=field(s,'confirmed',true);s=field(s,'due','2000-01-01T12:00');assert.equal(step(complete(s,'case')).event,'case');
 s=field(s,'due','2099-01-01T12:00');s=field(s,'owner','Real private account');assert.equal(step(complete(s,'case')).event,'case');
 assert.equal(throughReview().reviewed,true);
});
test('case progress uses real allowed transitions and requires an explanatory note through closure',()=>{
 let s=assigned();assert.equal(s.caseState,'Assigned');assert.equal(step(s).event,'progress');
 assert.equal(complete(field(field(s,'caseChoice','Closed'),'caseNote','Skip ahead'),'progress').caseState,'Assigned');
 for(const [event,status] of [['progress','In Progress'],['resolve','Resolved'],['close','Closed']]){
  const empty=complete(field(s,'caseChoice',status),event);assert.equal(empty.caseState,s.caseState);
  s=complete(field(field(s,'caseChoice',status),'caseNote','Practice update '+status),event);assert.equal(s.caseState,status);
 }
 assert.deepEqual(s.caseHistory.map(h=>h.state),['Assigned','In Progress','Resolved','Closed']);assert.equal(step(s).page,'batch');
});
test('Back restores a reversible checkpoint instead of leaving a closed case in an earlier editable step',()=>{
 let s=assigned();s=complete(field(field(s,'caseChoice','In Progress'),'caseNote','Checking surface'),'progress');assert.equal(s.caseState,'In Progress');
 s=practiceReducer(s,{type:'back'});assert.equal(step(s).event,'progress');assert.equal(s.caseState,'Assigned');assert.equal(s.caseChoice,'In Progress');
 s=complete(s,'progress');assert.equal(s.caseState,'In Progress');assert.equal(s.caseHistory.length,2);
 assert.equal(practiceReducer(practiceReducer(newPractice(),{type:'start'}),{type:'back'}).step,0);
});
test('new sessions and replay discard practice data, and arbitrary identity fields are ignored',()=>{
 const used=assigned();assert.deepEqual(practiceReducer(used,{type:'field',name:'role',value:'developer'}),used);
 const clean=practiceReducer(used,{type:'start'});assert.equal(clean.caseState,null);assert.equal(clean.shared,false);assert.equal(clean.saved,false);assert.deepEqual(clean.past,[]);
 assert.ok(!('userId' in clean));assert.ok(!('accessToken' in clean));
});

const require=createRequire(new URL('../package.json',import.meta.url)),React=require('react');
const cache=new Map();
async function mounted(file,initial){
 let code=cache.get(file);if(!code){code=(await build({entryPoints:[fileURLToPath(new URL('../src/'+file,import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',external:['react'],loader:{'.jpg':'dataurl'}})).outputFiles[0].text;cache.set(file,code)}
 let props=initial,tree,cursor=0;const slots=[];
 const fake={...React,createElement(type,p,...children){return {type,props:{...p,children}}},useEffect(){},useRef(){return {current:null}},useState(initial){const i=cursor++;if(!(i in slots))slots[i]=typeof initial==='function'?initial():initial;return [slots[i],v=>{slots[i]=typeof v==='function'?v(slots[i]):v}]}};
 const mod={exports:{}};new Function('require','module','exports',code)(id=>id==='react'?fake:require(id),mod,mod.exports);
 const text=n=>typeof n==='string'||typeof n==='number'?String(n):Array.isArray(n)?n.map(text).join(''):n&&typeof n==='object'?text(n.props.children):'';
 const nodes=(n,fn)=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(c=>nodes(c,fn)):[...(fn(n)?[n]:[]),...nodes(n.props.children,fn)];
 function render(next=props){props=next;cursor=0;tree=mod.exports.default(props);return tree}render();
 return {render,tree:()=>tree,text:()=>text(tree),find:fn=>nodes(tree,fn),button:label=>nodes(tree,n=>n.type==='button'&&text(n).trim()===label)[0],textOf:text};
}
test('welcome offers Start or Skip and hands control to actions rather than text Next buttons',async()=>{
 let started=0,skipped=0;const m=await mounted('Tutorial.jsx',{open:true,onStart:()=>started++,onDismiss:()=>skipped++});
 assert.ok(m.button('Start guided practice'));assert.equal(m.button('Next'),undefined);m.button('Start guided practice').props.onClick();assert.equal(started,1);
 m.button('Skip tutorial').props.onClick();assert.equal(skipped,1);let prevented=false;m.tree().props.onCancel({preventDefault(){prevented=true}});assert.ok(prevented);assert.equal(skipped,2);
});
test('actual practice controls drive the action sequence, route changes and validation; no request service is needed',async()=>{
 let state=practiceReducer(newPractice(),{type:'start'}),dismissed=0;
 const action=a=>{state=practiceReducer(state,a)};
 const props=()=>({state,page:step(state).page,onAction:action,onReturn(){},onDismiss(){dismissed++}});
 const m=await mounted('GuidedPractice.jsx',props());
 function input(label,value){const parent=m.find(n=>n.type==='label'&&m.textOf(n).startsWith(label))[0];assert.ok(parent,label);const find=n=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(find):[...(['input','select','textarea'].includes(n.type)?[n]:[]),...find(n.props.children)];find(parent)[0].props.onChange({target:{value,checked:value}});m.render(props())}
 function submit(){const form=m.find(n=>n.type==='form')[0];assert.ok(form);form.props.onSubmit({preventDefault(){}});m.render(props())}
 function click(label){assert.ok(m.button(label),label);m.button(label).props.onClick();m.render(props())}
 input('Product category','candle');assert.equal(step(state).event,'photo');click('Use sample photo');
 const run=m.find(n=>typeof n.type==='function'&&n.props.onRun)[0];assert.equal(run.props.readiness.disabled,false);run.props.onRun();m.render(props());
 const viewer=m.find(n=>typeof n.type==='function'&&n.props.onComparisonUsed)[0];viewer.props.onComparisonUsed();m.render(props());
 input('Question about this result','Why is this highlighted?');submit();assert.ok(state.answer);assert.match(m.text(),/prepared text, not a live AI/);
 action({type:'navigate',page:'history'});m.render(props());assert.equal(step(state).page,'history');click('Open inspection');click('Share with team (practice)');assert.equal(step(state).page,'team');
 submit();assert.ok(state.error);input('Review status','Reviewed');input('Decision','Reject');input('Review note','Practice check confirmed');submit();assert.equal(step(state).page,'cases');
 input('What needs fixing?','Practice candle surface repair.');input('Person responsible','Alex (practice)');input('Supervisor','Sam (practice)');click('Use tomorrow at noon');assert.ok(Date.parse(state.due)>Date.now());
 const confirm=m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0];confirm.props.onChange({target:{checked:true}});m.render(props());submit();
 for(const status of ['In Progress','Resolved','Closed']){input('Case status',status);input('What changed or was fixed?','Practice work '+status);submit()}
 assert.equal(step(state).page,'batch');submit();assert.ok(state.error);input('Batch label','Training batch 01');click('Add two sample photos');submit();
 assert.equal(step(state).page,'alerts');click('Mark as seen');assert.equal(step(state).page,'gallery');submit();assert.ok(state.error);
 m.find(n=>n.type==='input'&&n.props.type==='checkbox')[0].props.onChange({target:{checked:true}});m.render(props());submit();
 assert.equal(step(state).page,'overview');click('Finish tutorial');assert.equal(dismissed,1);
});
test('wrong-page navigation offers return to lesson, never a real workspace or approval form',async()=>{
 const m=await mounted('GuidedPractice.jsx',{state:practiceReducer(newPractice(),{type:'start'}),page:'team',onAction(){},onReturn(){},onDismiss(){}});
 assert.ok(m.button('Return to current step'));assert.equal(m.button('Save review (practice)'),undefined);assert.doesNotMatch(m.text(),/password|email address|staff access management/i);
});
test('shared image viewer still toggles and reports actual divider use; normal viewers need no callback',async()=>{
 let used=0;const m=await mounted('InspectionViewer.jsx',{record:practiceRecord,url:x=>x,heatmap:true,onComparisonUsed(){used++}});
 m.button('Compare images').props.onClick();m.render();assert.ok(m.button('Single image'));
 m.find(n=>n.type==='input'&&n.props.type==='range')[0].props.onChange({target:{value:'65'}});m.render();assert.equal(used,1);
 const normal=await mounted('InspectionViewer.jsx',{record:practiceRecord,url:x=>x,heatmap:true});normal.button('Compare images').props.onClick();normal.render();assert.doesNotThrow(()=>normal.find(n=>n.type==='input'&&n.props.type==='range')[0].props.onChange({target:{value:'40'}}));
});
test('practice modules cannot invoke cloud, inference, notifications or persisted batch services',async()=>{
 for(const name of ['Tutorial.jsx','GuidedPractice.jsx','tutorial.mjs']){const s=await readFile(new URL('../src/'+name,import.meta.url),'utf8');assert.doesNotMatch(s,/fetch\(|cloudClient|\.rpc\(|api\(|FormData|workspaceChanged|checkpointBatch|localSyncRequest|sessionStorage/)}
 const main=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.match(main,/if\(practiceRunning\)return;const poll=startPolling/);assert.match(main,/practiceRunning\?<GuidedPractice[\s\S]*?:<>[\s\S]*<TeamWorkspace/);
 assert.match(main,/if\(practiceRunning\)practiceAction\(\{type:'navigate',page:p\}\)/);
 assert.match(main,/open=\{tutorialOpen&&!practice.started\}/);assert.match(main,/setTutorialOpen\(false\);setPractice\(newPractice\(\)\)/);
 const start=main.slice(main.indexOf('function startPractice'),main.indexOf('function practiceAction'));
 assert.doesNotMatch(start,/setFiles|setResult|setCategory|setBatch|changeWorkspace|setWorkspace|setMessages/);assert.match(start,/if\(busy\|\|ragBusy\|\|recordLoading\)return/);
 assert.ok(main.includes("page!=='overview'||!health||busy||ragBusy||recordLoading||tutorialPrompted.current"));
});

test('practice images are emitted as standard build assets served by both runtimes',async()=>{
 const result=await build({entryPoints:[fileURLToPath(new URL('../src/GuidedPractice.jsx',import.meta.url))],bundle:true,write:false,platform:'browser',format:'esm',outdir:'test-output',assetNames:'assets/[name]-[hash]',loader:{'.jpg':'file'}});
 const images=result.outputFiles.filter(f=>f.path.endsWith('.jpg'));assert.equal(images.length,3);
 const originals=await Promise.all(['7dbb6f27253b450698a1a503cfa9a8c8.jpg','7dbb6f27253b450698a1a503cfa9a8c8_heatmap.jpg','14418c36d94648adbdbc2779a6a33b3c.jpg'].map(name=>readFile(new URL('../public/showcase/images/'+name,import.meta.url))));
 for(const bytes of originals)assert.ok(images.some(f=>Buffer.from(f.contents).equals(bytes)));
 const jsx=await readFile(new URL('../src/GuidedPractice.jsx',import.meta.url),'utf8');assert.doesNotMatch(jsx,/src=.?["']\.\/showcase/);assert.ok(jsx.includes('image_url:practiceOriginal,heatmap_url:practiceHeatmap'));
});
