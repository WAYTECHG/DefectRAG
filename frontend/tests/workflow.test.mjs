import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequestScope,newBatch,continueBatch,batchView,reviewBody,parseReview} from '../src/workflow.mjs';

const source=(await readFile(new URL('../src/main.jsx',import.meta.url),'utf8')).replaceAll('\r\n','\n');
test('actual assistant handler discards a late answer and error after inspection changes',async()=>{
 for(const failure of [false,true]){
  const scope=createRequestScope();let messages=[],error='',busy=false,resolve,reject;
  const response=new Promise((a,b)=>{resolve=a;reject=b});
  const declaration=source.slice(source.indexOf(' async function ask('),source.indexOf(' async function exportHistory('));
  const ask=new Function('result','ragBusy','question','context','api','setRagBusy','setError','setQuestion','setMessages',declaration+';return ask')(
   {id:'inspection-A'},false,'Explain this result',{current:scope},()=>response,value=>busy=value,value=>error=value,()=>{},updater=>messages=updater(messages));
  const pending=ask();scope.invalidate();busy=false;
  if(failure)reject(new Error('Old inspection failed'));else resolve({answer:'Answer for A'});
  await pending;
  assert.deepEqual(messages,[]);assert.equal(error,'');assert.equal(busy,false);
 }
});

test('out-of-order record opens cannot replace the newest selection or its messages',async()=>{
 const scope=createRequestScope();let result,messages,category,release;
 const delayed=new Promise(resolve=>release=resolve);
 const declaration=source.slice(source.indexOf(' async function openRecord('),source.indexOf(' async function sampleFile('));
 const open=new Function('resetInspection','setCategory','setBatch','setFiles','setRecordLoading','go','api','SHOWCASE','setResult','setMessages','setReview','setError','practiceRunning','page','practiceAction',declaration+';return openRecord')(
  ()=>{scope.invalidate();return scope.capture()},value=>category=value,()=>{},()=>{},()=>{},()=>{},
  async path=>{const first=path.includes('inspection-A');if(first)await delayed;if(path.endsWith('/messages'))return [first?'A messages':'B messages'];if(path.endsWith('/reviews'))return [];return {id:first?'inspection-A':'inspection-B',category:first?'candle':'pcb1',batch:'saved-batch'}},false,
  value=>result=value,value=>messages=value,()=>{},error=>{throw new Error(error)},false,'history',()=>assert.fail('normal work never reports lesson events'));
 const first=open({id:'inspection-A',category:'candle'});await open({id:'inspection-B',category:'pcb1'});release();await first;
 assert.equal(result.id,'inspection-B');assert.equal(category,'pcb1');assert.deepEqual(messages,['B messages']);
});

test('quota interruption survives checkpoint restore and retries only unfinished image IDs',async()=>{
 const files=[{name:'same.jpg'},{name:'same.jpg'},{name:'third.jpg'}];
 let job=newBatch(files,'pcb1','TEST-BATCH'),saved,calls=0;
 job=await continueBatch(job,async()=>{calls++;if(calls===2)throw new Error('You have exceeded your ZeroGPU runs limit');return {id:'completed-A',category:'pcb1',score:.2,image_url:'private-url?token=secret'}},async value=>saved=structuredClone(value));
 assert.equal(calls,2);assert.equal(job.items[0].status,'completed');assert.equal(job.items[1].status,'failed');assert.equal(job.items[2].status,'pending');
 assert.equal(saved.items[0].record.image_url,undefined);
 const submitted=[];await continueBatch(saved,async file=>{submitted.push(file.name);return {id:'retry-'+submitted.length}},async()=>{});
 assert.deepEqual(submitted,['same.jpg','third.jpg']);assert.equal(batchView(job).records.length,1);
});

test('account/context change stops remaining submissions but saves the in-flight completion',async()=>{
 let current=true,saved,calls=0;
 const job=await continueBatch(newBatch([{name:'a'},{name:'b'}],'pcb1','B'),async()=>{calls++;current=false;return {id:'completed'}},async value=>saved=value,()=>current);
 assert.equal(calls,1);assert.equal(saved.items[0].status,'completed');assert.equal(job.items[1].status,'pending');
});

test('review parsing trusts row author/time rather than claimed values in note JSON',()=>{
 const body=reviewBody('Reviewed','Hold','More evidence needed');
 const parsed=parseReview({body,author_id:'real-user',created_at:'database-time'},{'real-user':'Approved reviewer'});
 assert.equal(parsed.reviewer,'Approved reviewer');assert.equal(parsed.created_at,'database-time');
 assert.throws(()=>reviewBody('Reviewed','Pending'));assert.throws(()=>reviewBody('In review','Accept'));
 assert.equal(parseReview({body:'ordinary note'}),null);
});
