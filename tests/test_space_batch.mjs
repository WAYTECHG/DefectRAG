import assert from 'node:assert/strict';
import {runBatch} from '../deployment/space/batch_jobs.mjs';
const files=['first.jpg','quota.jpg','pending.jpg','another.jpg'].map(name=>({name}));
let calls=0;
const limited=await runBatch(files,async file=>{
 calls++;
 if(file.name==='quota.jpg')throw new Error('You have exceeded your ZeroGPU runs limit.');
 return {id:file.name};
});
assert.equal(calls,2,'No GPU calls may be attempted after quota rejection');
assert.deepEqual(limited.records,[{id:'first.jpg'}]);
assert.equal(limited.errors.length,3);
assert.match(limited.errors[0].message,/Supabase staff login uses a separate account/);
assert.match(limited.errors[1].message,/Not submitted/);
const independent=await runBatch(files.slice(0,2),async file=>{
 if(file.name==='first.jpg')throw new Error('Invalid image');
 return {id:file.name};
});
assert.equal(independent.records.length,1,'Bad input must not discard later valid images');
assert.equal(independent.errors.length,1);
console.log('PASS: quota stops pending GPU submissions; successes survive; input failures stay independent.');
