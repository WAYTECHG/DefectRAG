import {Client} from '../zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const cloud=process.argv.includes('--cloud'),target=cloud?'https://wizzas-defectrag.hf.space':'http://127.0.0.1:8784';
const vision=JSON.parse(await fs.readFile(path.join(root,`development-support/space/phase2-${cloud?'cloud':'local'}.json`),'utf8'));
const record=vision.cases.find(row=>row.name==='pcb1_anomalous.jpg').result;
const out=path.join(root,`development-support/space/phase3-${cloud?'cloud':'local'}.json`);
let report;try{report=JSON.parse(await fs.readFile(out,'utf8'))}catch{report={target,inspection_id:record.id,answers:[]}}
const cases=[['measurement','Is this image anomalous?'],['generation','Explain what this heatmap shows and how I should read it.'],
 ['followup','Does that show a specific defect type?'],['unsupported','What caused it and how do I repair it?']];
for(const [name,question]of cases){
 if(report.answers.some(row=>row.name===name))continue;
 const client=await Client.connect(target,{record_history:false,...(process.env.SPACE_HF_TOKEN?{token:process.env.SPACE_HF_TOKEN}:{})});
 let answer;
 try{answer=(await client.predict('/assistant',{inspection_id:record.id,question,session:vision.session,token:''})).data[0]}
 finally{if(client.stream_instance)client.stream_instance.onerror=error=>{if(error?.name!=='AbortError')console.error(error)};client.close()}
 assert.equal(answer.observation.id,record.id);
 if(name==='measurement')assert.equal(answer.mode,'measurement_only');
 if(name==='generation'){
  assert.equal(answer.mode,'llm',JSON.stringify(answer));assert.ok(answer.claims.length>0);
  for(const claim of answer.claims){const source=answer.evidence.find(row=>row.chunk_id===claim.source_id);assert.ok(source?.text.includes(claim.quote));assert.ok(answer.answer.includes('['+claim.source_id+']'))}
  if(cloud){assert.equal(answer.generation.zero_gpu,true);assert.ok(answer.generation.generation_ms>0)}
 }
 if(name==='unsupported')assert.equal(answer.mode,'abstained');
 report.answers.push({name,question,answer});await fs.writeFile(out,JSON.stringify(report,null,2));
 console.log(JSON.stringify({name,mode:answer.mode,answer:answer.answer,generation:answer.generation}));
}
const headers={'X-DefectRAG-Session':vision.session};
const history=(await(await fetch(target+`/api/inspections/${record.id}/messages`,{headers})).json()).data;
assert.ok(history.length>=8);
report.status='passed';report.saved_turns=history.length;
await fs.writeFile(out,JSON.stringify(report,null,2));console.log('LIVE RETRIEVAL + GENERATION + CITATIONS + HISTORY PASSED');
