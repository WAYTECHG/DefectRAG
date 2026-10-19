import test from 'node:test';
import assert from 'node:assert/strict';
import {configureWorkspace,activeWorkspace,setWorkspace,startPolling} from '../src/workspace.mjs';

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
