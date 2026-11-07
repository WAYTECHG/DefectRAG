// Live check of the fine-tuned profile on the public Space: one good and one anomalous sample per category.
// Writes development-support/space/tuned-live.json; scripts/verify_tuned_live_parity.py then compares the scores with the local app.
import {Client} from '../zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const target='https://wizzas-defectrag.hf.space';
const out=path.join(root,'development-support/space/tuned-live.json');
const session=crypto.randomBytes(32).toString('hex');
const call=async(endpoint,payload)=>{
 const client=await Client.connect(target,process.env.SPACE_HF_TOKEN?{token:process.env.SPACE_HF_TOKEN}:undefined);
 try{return (await client.predict(endpoint,payload)).data[0]}finally{
  if(client.stream_instance)client.stream_instance.onerror=error=>{if(error?.name!=='AbortError')console.error(error)};
  client.close();
 }
};
const ready=await call('/ready',{message:'tuned-live-check'});
assert.equal(ready.categories.length,12);
const cases=[];
for(const category of ready.categories)for(const kind of ['good','anomalous']){
 const name=`${category}_${kind}.jpg`;
 const image=await fs.readFile(path.join(root,'samples',name));
 const result=await call('/inspect',{image_b64:image.toString('base64'),filename:name,category,batch:'TUNED-LIVE-CHECK',session,token:''});
 const card=JSON.parse(await fs.readFile(path.join(root,'models/highres_tuned',category+'.json'),'utf8'));
 assert.equal(result.category,category);
 assert.ok(Number.isFinite(result.score));
 assert.equal(result.device,'cuda');
 assert.equal(result.profile,'dinov2_tuned_v1');
 assert.equal(result.model_id,card.model_id);
 assert.equal(result.model_sha256,card.bank_sha256);
 assert.equal(result.threshold,card.threshold);
 cases.push({name,score:result.score,verdict:result.verdict,threshold:result.threshold,ms:result.inference_ms,model_id:result.model_id});
 console.log(JSON.stringify(cases.at(-1)));
}
await fs.writeFile(out,JSON.stringify({target,cases},null,2));
console.log('LIVE TUNED PROFILE CHECK PASSED: '+cases.length+' inspections');
