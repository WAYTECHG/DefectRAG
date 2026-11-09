// Live check: an inspection on the public Space names its closest normal reference photos, and the verdict is unchanged.
import {Client} from '../zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const target='https://wizzas-defectrag.hf.space';
const session=crypto.randomBytes(32).toString('hex');
const call=async(endpoint,payload)=>{
 const client=await Client.connect(target,process.env.SPACE_HF_TOKEN?{token:process.env.SPACE_HF_TOKEN}:undefined);
 try{return (await client.predict(endpoint,payload)).data[0]}finally{
  if(client.stream_instance)client.stream_instance.onerror=error=>{if(error?.name!=='AbortError')console.error(error)};
  client.close();
 }
};
for(const name of ['pcb1_anomalous.jpg','candle_good.jpg']){
 const category=name.replace(/_(good|anomalous)\.jpg$/,'');
 const image=await fs.readFile(path.join(root,'samples',name));
 const result=await call('/inspect',{image_b64:image.toString('base64'),filename:name,category,batch:'REFERENCES-LIVE-CHECK',session,token:''});
 assert.ok(Array.isArray(result.references)&&result.references.length===3,'three references expected');
 assert.ok(result.references.every(r=>r.id.startsWith(category+'/')&&Number.isFinite(r.similarity)));
 const library=await (await fetch(`${target}/assets/references/${category}.json`)).json();
 const known=new Set(library.items.map(i=>i.id));
 assert.ok(result.references.every(r=>known.has(r.id)),'every named reference has a thumbnail');
 console.log(JSON.stringify({name,verdict:result.verdict,score:Number(result.score.toFixed(4)),references:result.references.map(r=>r.id)}));
}
console.log('LIVE REFERENCES CHECK PASSED');
