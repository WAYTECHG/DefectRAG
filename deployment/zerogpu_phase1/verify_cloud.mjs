// Read-only evidence capture AFTER the single browser-triggered ZeroGPU request.
// Never invokes /inspect and cannot spend another GPU lease.
import {Client} from './client/node_modules/@gradio/client/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const target='https://wizzas-defectrag.hf.space';
const client=await Client.connect(target);
const ready=(await client.predict('/phase1_ready',{message:'phase1-cloud-read-only'})).data[0];
const rows=(await (await fetch(target+'/api/inspections')).json()).data;
assert.equal(rows.length,1,'Expected the one browser-triggered fixture request');
const record=rows[0];
assert.equal(record.phase1.zero_gpu_environment,true);
assert.equal(record.device,'cuda');
assert.equal(ready.zero_gpu_environment,true);
assert.equal(record.model_sha256,'14e71cb6285f22e3d12d2b0d6357c552a26685a8f03a9b626a3e8999e8a89c65');
const local=JSON.parse(await fs.readFile(path.join(root,'runtime/zerogpu-phase1/last-genuine-inspection.json'),'utf8'));
const difference=Math.abs(record.score-local.score);
assert.ok(difference<0.001,'Single-fixture numerical tolerance exceeded');
assert.equal(record.verdict,local.verdict);
const checks={};
for(const [name,url] of Object.entries({dashboard:'/',heatmap:record.heatmap_url,image:record.image_url,
  report:`/api/inspections/${record.id}/report`,evaluation:'/api/evaluation',
  benchmark:'/api/benchmark/official',csv:'/api/export.csv'})) {
  const response=await fetch(target+url);assert.equal(response.status,200,name);checks[name]='passed';
  if(name==='heatmap')assert.match(response.headers.get('content-type'),/^image\//);
}
const css='assets/index-Bn4HF2vD.css';
const cloudCss=Buffer.from(await (await fetch(target+'/'+css)).arrayBuffer());
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
assert.equal(hash(cloudCss),hash(await fs.readFile(path.join(root,'frontend/dist',css))));
assert.equal((await fetch(target+'/api/inspect',{method:'POST'})).status,409);
const config=await (await fetch(target+'/config.js')).text();
assert.ok(config.includes("supabaseUrl:''")&&config.includes("supabasePublishableKey:''"));
const result={status:'passed',target,ready,one_browser_inspection:record,checks,
  local_score:local.score,absolute_score_difference:difference,fixture_tolerance:0.001,
  css_sha256:hash(cloudCss),production_css_identical:true,public_supabase_config:'blank',
  limitations:['one PCB1 fixture, no all12 accuracy re-evaluation','no RAG, batch, cloud staff migration',
    'direct hf.space guest browser tested; authenticated HF iframe identity/quota forwarding not tested',
    'ephemeral public test history, no production persistence or load certification']};
await fs.writeFile(path.join(root,'development-support/zerogpu-phase1/cloud-verification.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
