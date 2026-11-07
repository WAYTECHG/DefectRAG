// Live check: the assistant describes the fine-tuned DINOv2 profile correctly for a saved inspection.
import {Client} from '../zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
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
const image=await fs.readFile(path.join(root,'samples','macaroni2_anomalous.jpg'));
const record=await call('/inspect',{image_b64:image.toString('base64'),filename:'macaroni2_anomalous.jpg',category:'macaroni2',batch:'TUNED-ASSISTANT-CHECK',session,token:''});
console.log(JSON.stringify({model_id:record.model_id,verdict:record.verdict,score:record.score}));
const question=process.argv[2]||'Which detector produced this result, and was its encoder fine-tuned or frozen?';
const answer=await call('/assistant',{inspection_id:record.id,question,session,token:'',workspace:'personal'});
console.log(JSON.stringify({mode:answer.mode,answer:answer.answer,sources:(answer.evidence||[]).map(e=>e.id)},null,2));
