import {cloudConfigured,cloudClient} from './cloud.js';
import {personalEnabled} from './workspace.mjs';
import {practiceActive} from './practice.mjs';

export async function batchOwner(){
 // Practice batches are never written to browser recovery storage.
 if(practiceActive())return 'practice';
 if(cloudConfigured()){
  const {data}=await (await cloudClient()).auth.getSession();
  if(data.session?.user)return 'staff:'+data.session.user.id+(personalEnabled()?':personal':'');
 }
 // No user identity, token, or signed artifact URL is stored in the checkpoint.
 return 'browser';
}
function database(){
 return new Promise((resolve,reject)=>{
  const request=indexedDB.open('defectrag-batch-checkpoints',1);
  request.onupgradeneeded=()=>request.result.createObjectStore('jobs');
  request.onsuccess=()=>resolve(request.result);
  request.onerror=()=>reject(new Error('Browser batch recovery is unavailable.'));
 });
}
export async function checkpointBatch(owner,job){
 if(owner==='practice')return;
 const db=await database();
 try{await new Promise((resolve,reject)=>{
  const transaction=db.transaction('jobs','readwrite');
  transaction.objectStore('jobs').put(job,owner);
  transaction.oncomplete=resolve;
  transaction.onerror=()=>reject(new Error('Browser storage could not save batch progress.'));
  transaction.onabort=()=>reject(new Error('Browser storage could not save batch progress.'));
 })}finally{db.close()}
}
export async function restoreBatch(owner){
 if(owner==='practice')return null;
 const db=await database();
 try{return await new Promise((resolve,reject)=>{
  const request=db.transaction('jobs').objectStore('jobs').get(owner);
  request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error);
 })}finally{db.close()}
}
