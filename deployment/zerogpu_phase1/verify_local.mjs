// Read-only verification after the ONE browser-triggered genuine inspection.
import {Client} from './client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const target='http://127.0.0.1:8783';
const client=await Client.connect(target);
const ready=(await client.predict('/phase1_ready',{message:'react-gradio-phase1'})).data[0];
assert.equal(ready.message,'react-gradio-phase1');
assert.equal(ready.server_mode,true);
const record=JSON.parse(await fs.readFile(path.join(root,'runtime/zerogpu-phase1/last-genuine-inspection.json'),'utf8'));
assert.equal(record.device,'cuda');
assert.equal(record.model_id,'dinov2-highres-pcb1-v1');
assert.equal(record.score,0.31308862566947937);
const checks={};
for(const [name,url] of Object.entries({dashboard:'/',history:'/api/inspections',
  heatmap:record.heatmap_url,image:record.image_url,report:`/api/inspections/${record.id}/report`,
  evaluation:'/api/evaluation',benchmark:'/api/benchmark/official',csv:'/api/export.csv'})) {
  const response=await fetch(target+url);assert.equal(response.status,200,name);checks[name]='passed';
  if(name==='heatmap')assert.match(response.headers.get('content-type'),/^image\//);
  if(name==='history'){const body=await response.json();assert.equal(body.data.length,1);assert.equal(body.data[0].id,record.id);}
}
// A REST request cannot bypass the Gradio scheduler.
assert.equal((await fetch(target+'/api/inspect',{method:'POST'})).status,409);
const css='assets/index-Bn4HF2vD.css';
const digest=async p=>crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');
const original=await digest(path.join(root,'frontend/dist',css));
assert.equal(original,await digest(path.join(root,'development-support/zerogpu-phase1/ui-dist',css)));
const navigation=JSON.parse(await fs.readFile(path.join(root,'development-support/zerogpu-phase1/navigation.json'),'utf8'));
assert.equal(navigation.length,9);assert.ok(navigation.every(p=>p.heading));
const report={status:'passed',ready,checks,one_browser_inspection:record,
  css_sha256:original,production_css_identical:true,navigation,
  rest_gpu_bypass:'blocked',zerogpu:'not tested by this local CUDA run'};
await fs.writeFile(path.join(root,'development-support/zerogpu-phase1/local-verification.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({status:report.status,checks,score:record.score,device:record.device,
  production_css_identical:true,versions:ready.versions,navigation_pages:navigation.length},null,2));
