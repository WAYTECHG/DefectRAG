import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {configureWorkspace,activeWorkspace,setWorkspace,startPolling,createOperationGuard} from '../src/workspace.mjs';

test('activated cloud defaults to personal; legacy mode stays team; scope is validated',()=>{
 configureWorkspace(false);assert.equal(activeWorkspace(),'team');
 configureWorkspace(true);assert.equal(activeWorkspace(),'personal');
 setWorkspace('team');assert.equal(activeWorkspace(),'team');
 assert.throws(()=>setWorkspace('public'));
 setWorkspace('personal');configureWorkspace(false);
});

test('polling coalesces duplicate events, recovers on reconnect and stops cleanly',async()=>{
 const target=new EventTarget(),doc=new EventTarget();target.navigator={onLine:true};doc.hidden=false;
 let calls=0,release;const states=[];
 const poll=startPolling(async()=>{calls++;if(calls===1)await new Promise(resolve=>release=resolve)},
  {target,documentTarget:doc,interval:100000,onState:value=>states.push(value.state)});
 target.dispatchEvent(new Event('focus'));target.dispatchEvent(new Event('defectrag-workspace-change'));
 assert.equal(calls,1);release();await new Promise(resolve=>setImmediate(resolve));
 assert.equal(calls,2);assert.equal(states.at(-1),'synced');
 target.navigator.onLine=false;target.dispatchEvent(new Event('offline'));await poll.refresh();
 assert.equal(calls,2);assert.equal(states.at(-1),'offline');
 target.navigator.onLine=true;target.dispatchEvent(new Event('online'));await new Promise(resolve=>setImmediate(resolve));
 assert.equal(calls,3);poll.stop();target.dispatchEvent(new Event('focus'));assert.equal(calls,3);
});

test('polling surfaces cloud failure without reporting success, then recovers',async()=>{
 const target=new EventTarget(),doc=new EventTarget();let fail=true;const states=[];
 const poll=startPolling(async()=>{if(fail)throw new Error('Cloud unavailable')},
  {target,documentTarget:doc,interval:100000,onState:value=>states.push(value)});
 await new Promise(resolve=>setImmediate(resolve));assert.equal(states.at(-1).state,'stale');
 assert.equal(states.at(-1).error,'Cloud unavailable');fail=false;await poll.refresh();
 assert.equal(states.at(-1).state,'synced');poll.stop();
});

test('stopping a pending refresh suppresses late state notifications',async()=>{
 const target=new EventTarget(),doc=new EventTarget();let release;const states=[];
 const poll=startPolling(()=>new Promise(resolve=>release=resolve),{target,documentTarget:doc,interval:100000,onState:value=>states.push(value.state)});
 poll.stop();release();await new Promise(resolve=>setImmediate(resolve));assert.deepEqual(states,['refreshing']);
});

for(const rejects of [false,true])test(`offline during pending ${rejects?'failed':'successful'} refresh stays offline`,async()=>{
 const target=new EventTarget(),doc=new EventTarget();target.navigator={onLine:true};let release;const states=[];
 const poll=startPolling(()=>new Promise((resolve,reject)=>{release=()=>rejects?reject(new Error('Disconnected')):resolve()}),
  {target,documentTarget:doc,interval:100000,onState:value=>states.push(value.state)});
 try{
  target.navigator.onLine=false;target.dispatchEvent(new Event('offline'));release();
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(states,['refreshing','offline','offline']);
 }finally{poll.stop()}
});

test('sharing completion is invalidated by leaving a view or starting a newer operation',()=>{
 const guard=createOperationGuard(),old=guard.begin();assert.equal(old(),true);
 guard.invalidate();assert.equal(old(),false);
 const current=guard.begin();assert.equal(current(),true);
 const newer=guard.begin();assert.equal(current(),false);assert.equal(newer(),true);
 guard.invalidate();assert.equal(newer(),false);
});

for(const fails of [false,true])test(`actual sharing handler suppresses late ${fails?'error':'success'} after context change`,async()=>{
 const source=(await readFile(new URL('../src/WorkspaceShare.jsx',import.meta.url),'utf8')).replaceAll('\r\n','\n');
 const declaration=source.slice(source.indexOf(' async function save('),source.indexOf('\n return <div>'));
 const guard=createOperationGuard();let resolve,reject,notices=0,opened=0,changed=0;const errors=[],busy=[];
 const pending=new Promise((a,b)=>{resolve=a;reject=b});
 const save=new Function('operations','api','enabled','record','messages','url','shareInspection','workspaceChanged','onNotice','onChanged','setBusy','setError','include',declaration+';return save')(
  {current:guard},()=>pending,true,{id:'old-record'},[],value=>value,()=>assert.fail('Legacy transport should not run'),
  ()=>changed++,()=>notices++,()=>opened++,value=>busy.push(value),value=>errors.push(value),false);
 const work=save();guard.invalidate();
 if(fails)reject(new Error('Old account request failed'));else resolve({alreadyShared:false});
 await work;
 assert.equal(notices,0);assert.equal(opened,0);assert.deepEqual(errors,['']);assert.deepEqual(busy,[true]);
 assert.equal(changed,fails?0:1);
});
