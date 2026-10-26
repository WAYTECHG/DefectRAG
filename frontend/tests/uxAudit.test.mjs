import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';
import {filterInspectionRows} from '../src/inspectionUX.mjs';

const require=createRequire(new URL('../package.json',import.meta.url)),React=require('react');
async function mount(name,props,initial=[]){
 const code=(await build({entryPoints:[fileURLToPath(new URL('../src/'+name,import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',external:['react']})).outputFiles[0].text;
 let cursor=0,refCursor=0,tree;const slots=[...initial],refs=[],effects=[];
 const fake={...React,createElement(type,p,...children){return {type,props:{...p,children}}},useEffect(fn){effects.push(fn)},useRef(){return refs[refCursor++]||=( {current:null})},useState(value){const i=cursor++;if(!(i in slots))slots[i]=typeof value==='function'?value():value;return [slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v]}};
 const m={exports:{}};new Function('require','module','exports',code)(id=>id==='react'?fake:require(id),m,m.exports);
 const text=n=>typeof n==='string'||typeof n==='number'?String(n):Array.isArray(n)?n.map(text).join(''):n&&typeof n==='object'?text(n.props.children):'';
 const nodes=(n,fn)=>!n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(c=>nodes(c,fn)):[...(fn(n)?[n]:[]),...nodes(n.props.children,fn)];
 function render(){cursor=refCursor=0;effects.length=0;tree=m.exports.default(props);return tree}render();
 return {render,refs,slots,effects,text:()=>text(tree),find:fn=>nodes(tree,fn),button:label=>nodes(tree,n=>n.type==='button'&&text(n).trim()===label)[0]};
}

test('batch history excludes individual photos while ordinary history retains them and all filters',()=>{
 const rows=[{id:1,category:'candle',verdict:'Good',batch:''},{id:2,category:'candle',verdict:'Anomalous',batch:'QA 01'},
  {id:3,category:'pcb1',verdict:'Good',batch:'QA 02'},{id:4,category:'pcb1',verdict:'Good',batch:'   '}];
 assert.deepEqual(filterInspectionRows(rows,{},'batch').map(r=>r.id),[2,3]);
 assert.deepEqual(filterInspectionRows(rows,{},'history').map(r=>r.id),[1,2,3,4]);
 assert.deepEqual(filterInspectionRows(rows,{category:'candle',verdict:'Anomalous',batch:'QA 01'},'batch').map(r=>r.id),[2]);
 assert.deepEqual(filterInspectionRows(rows,{verdict:'Good'},'batch').map(r=>r.id),[3]);
 assert.equal(rows.length,4,'Filtering does not delete or mutate saved records');
});

test('demo reviews explicitly stay in this browser; real Staff reviews retain their label and API submission',async()=>{
 const saves=[],m=await mount('ReviewForm.jsx',{demo:true,onSave:async v=>saves.push(v)});
 assert.match(m.text(),/Demo review · this browser only/);assert.match(m.text(),/not an official Staff review/);
 await m.find(n=>n.type==='form')[0].props.onSubmit({preventDefault(){}});
 assert.deepEqual(saves,[{status:'Needs review',decision:'Pending',note:''}]);
 const staff=await mount('ReviewForm.jsx',{onSave(){}});assert.match(staff.text(),/Staff review/);assert.doesNotMatch(staff.text(),/Demo review/);
});

test('gallery opening focuses and reveals its preview; closing returns focus to the exact opening control',async()=>{
 const item={id:'public-fixture',created_at:'2026-10-27',measurement:{category:'candle',verdict:'Good',score:.1}};
 const m=await mount('CommunityGallery.jsx',{api:async()=>({enabled:true,items:[item]})},[0,0,{enabled:true,items:[item]},'',null,'',false]);
 let focused=0,scrolled=0,returned=0;const heading={focus(){focused++},scrollIntoView(){scrolled++}},trigger={focus(){returned++}};
 m.refs[0].current=heading;
 const open=m.button('View image & heatmap');assert.equal(open.props['aria-expanded'],false);open.props.onClick({currentTarget:trigger});m.render();
 assert.equal(m.button('View image & heatmap').props['aria-expanded'],true);
 // Run the real preview navigation effect, independently of network-loading effects.
 m.effects[0]();assert.equal(focused,1);assert.equal(scrolled,1);
 assert.ok(m.find(n=>n.type==='h2'&&n.props.id==='public-inspection-preview-heading'&&n.props.tabIndex===-1).length);
 m.button('Close preview').props.onClick();assert.equal(returned,1);assert.equal(m.slots[3],'');
});

test('failed gallery preview offers a nearby retry that preserves selection',async()=>{
 const m=await mount('CommunityGallery.jsx',{api:async()=>({})},[0,0,{enabled:true,items:[]},'public-fixture',null,'Connection failed',false]);
 assert.ok(m.button('Retry preview'));m.button('Retry preview').props.onClick();
 assert.equal(m.slots[3],'public-fixture');assert.equal(m.slots[5],'');assert.equal(m.slots[1],1);
});

test('tutorial controls use scoped checkbox/text-area styles and both explicit consent labels',async()=>{
 const css=await readFile(new URL('../src/theme.css',import.meta.url),'utf8');
 assert.match(css,/\.guided-practice input\[type="checkbox"\]\{width:auto;min-height:0/);
 assert.match(css,/\.guided-practice textarea\{display:block;width:100%/);
 assert.match(css,/\.guided-practice \.guided-consent\{display:flex/);
 const jsx=await readFile(new URL('../src/GuidedPractice.jsx',import.meta.url),'utf8');
 assert.equal((jsx.match(/className="guided-consent"/g)||[]).length,2);
});

test('saved results move into view only after loading; demo recovery and reviews do not claim account storage',async()=>{
 const source=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.match(source,/if\(!practiceRunning&&ready&&!busy&&!recordLoading\)/);
 assert.match(source,/resultHeading\.current\?\.focus\(\{preventScroll:true\}\)/);
 assert.match(source,/resultHeading\.current\?\.scrollIntoView/);
 assert.match(source,/<h2 ref=\{resultHeading\} tabIndex=\{-1\}/);
 assert.match(source,/demo=\{publicDemoAvailable\(health,inspectionAccess\)\}/);
 assert.match(source,/Recover demo inspections/);assert.match(source,/Only this browser’s demo archive/);
});

test('New inspection and sample handlers cannot discard an active inspection, answer or record load',async()=>{
 const s=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 const handler=s.slice(s.indexOf(' async function sampleFile('),s.indexOf(' async function inspect('));
 for(const [busy,ragBusy,recordLoading] of [[true,false,false],[false,true,false],[false,false,true]]){
  let reset=0;const fn=new Function('busy','ragBusy','recordLoading','resetInspection',handler+';return sampleFile')
   (busy,ragBusy,recordLoading,()=>reset++);
  await fn({});assert.equal(reset,0);
 }
 assert.match(s,/disabled=\{busy\|\|ragBusy\|\|recordLoading\} title=\{busy\|\|ragBusy\|\|recordLoading\?'Finish the current inspection/);
 assert.match(s,/onClick=\{\(\)=>\{if\(busy\|\|ragBusy\|\|recordLoading\)return;if\(health/);
 assert.match(s,/multiple=\{page==='batch'\} disabled=\{busy\|\|ragBusy\|\|recordLoading\}/);
});

test('edited interface files retain readable UTF-8 punctuation on Windows',async()=>{
 for(const name of ['ArchiveDialog.jsx','InspectionViewer.jsx','TeamWorkspace.jsx','theme.css','main.jsx']){
  const s=await readFile(new URL('../src/'+name,import.meta.url),'utf8');assert.doesNotMatch(s,/Â·|â†|â€/,name);
 }
});
