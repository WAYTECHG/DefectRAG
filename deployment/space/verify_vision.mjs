// Bounded integration verification, not a new model benchmark. Resume saved cases.
import {Client} from '../zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const cloud=process.argv.includes('--cloud'),target=cloud?'https://wizzas-defectrag.hf.space':'http://127.0.0.1:8784';
const out=path.join(root,`development-support/space/phase2-${cloud?'cloud':'local'}.json`);
await fs.mkdir(path.dirname(out),{recursive:true});
let report;
try{report=JSON.parse(await fs.readFile(out,'utf8'))}catch{report={target,session:crypto.randomBytes(32).toString('hex'),cases:[]}}
const save=()=>fs.writeFile(out,JSON.stringify(report,null,2));
const headers={'X-DefectRAG-Session':report.session};
const call=async(endpoint,payload)=>{
 const client=await Client.connect(target,process.env.SPACE_HF_TOKEN?{token:process.env.SPACE_HF_TOKEN}:undefined);
 try{return (await client.predict(endpoint,payload)).data[0]}finally{
  if(client.stream_instance)client.stream_instance.onerror=error=>{if(error?.name!=='AbortError')console.error(error)};
  client.close();
 }
};
report.ready=await call('/ready',{message:'bounded-all12-smoke'});
const cats=report.ready.categories;
assert.equal(cats.length,12);
for(const category of cats)for(const kind of ['good','anomalous']){
 const name=`${category}_${kind}.jpg`;
 if(report.cases.some(row=>row.name===name))continue;
 const image=await fs.readFile(path.join(root,'samples',name));
 const result=await call('/inspect',{image_b64:image.toString('base64'),filename:name,category,batch:'MIGRATION-SMOKE',session:report.session,token:''});
 assert.equal(result.category,category);assert.ok(Number.isFinite(result.score));assert.equal(result.device,'cuda');
 assert.equal(result.deployment.zero_gpu_environment,cloud);
 const card=JSON.parse(await fs.readFile(path.join(root,'models/highres',category+'.json'),'utf8'));
 assert.equal(result.model_sha256,card.bank_sha256);assert.equal(result.threshold,card.threshold);
 for(const kind of ['image','heatmap','report'])assert.equal((await fetch(target+result[kind+'_url'])).status,200,kind);
 assert.equal((await fetch(target+`/api/inspections/${result.id}/heatmap`)).status,401);
 report.cases.push({name,input_sha256:crypto.createHash('sha256').update(image).digest('hex'),result});
 await save();console.log(JSON.stringify({name,score:result.score,verdict:result.verdict,ms:result.inference_ms,mb:result.peak_gpu_mb}));
}
const history=await (await fetch(target+'/api/inspections?limit=500',{headers})).json();
assert.equal(history.data.length,24);
const other={'X-DefectRAG-Session':crypto.randomBytes(32).toString('hex')};
const foreign=await (await fetch(target+'/api/inspections',{headers:other})).json();
assert.equal(foreign.data.length,0);
assert.equal((await fetch(target+'/api/inspections/'+report.cases[0].result.id,{headers:other})).status,404);
const testClient=await Client.connect(target,process.env.SPACE_HF_TOKEN?{token:process.env.SPACE_HF_TOKEN}:undefined);
let rejected=false;
try{await testClient.predict('/inspect',{image_b64:'bm90LWFuLWltYWdl',filename:'broken.jpg',category:'pcb1',batch:'',session:report.session,token:''})}catch{rejected=true}finally{
 if(testClient.stream_instance)testClient.stream_instance.onerror=error=>{if(error?.name!=='AbortError')console.error(error)};
 testClient.close();
}
assert.ok(rejected,'Invalid input must fail');
report.privacy='other workspace empty; unsigned image blocked; foreign inspection 404';
report.invalid_image='rejected';
const css='assets/index-Bn4HF2vD.css',hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(hash(await fs.readFile(path.join(root,'frontend/dist',css))),hash(Buffer.from(await(await fetch(target+'/'+css)).arrayBuffer())));
if(cloud){
 const local=JSON.parse(await fs.readFile(path.join(root,'development-support/space/phase2-local.json'),'utf8'));
 report.parity=report.cases.map(row=>{
  const reference=local.cases.find(other=>other.name===row.name);
  const difference=Math.abs(row.result.score-reference.result.score);
  assert.ok(difference<0.002,`${row.name} parity difference ${difference}`);
  return {name:row.name,absolute_difference:difference,same_verdict:row.result.verdict===reference.result.verdict};
 });
}
report.status='passed';await save();console.log('ALL12 REAL VISION + PRIVACY CHECKS PASSED');
