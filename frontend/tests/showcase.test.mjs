import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const fixture = JSON.parse(await readFile(new URL('../public/showcase/data.json', import.meta.url), 'utf8'));
const source = (await readFile(new URL('../src/showcase.js', import.meta.url), 'utf8')).replaceAll('import.meta.env', "({MODE:'showcase'})");
const {showcaseApi, assetUrl} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const requests = [];
globalThis.fetch = async (url, options) => {requests.push([url, options]); return {ok:true,json:async()=>fixture};};

test('loads all pages through one static snapshot request and no backend', async () => {
  const [records, stats, alerts, evaluation] = await Promise.all([
    showcaseApi('/api/inspections?limit=500'), showcaseApi('/api/stats'),
    showcaseApi('/api/alerts'), showcaseApi('/api/evaluation')]);
  assert.equal(records.length, fixture.records.length);
  assert.equal(stats.total, records.length);
  assert.equal(alerts.length, records.filter(r=>r.verdict!=='Good').length);
  assert.equal(Object.keys(evaluation.categories).length, 12);
  assert.equal(requests.length, 1);
  assert.equal(requests[0][0], './showcase/data.json');
});
test('rejects mutations and missing examples without sending uploads or chat', async () => {
  for (const path of ['/api/inspect','/api/batch','/api/assistant','/api/alerts/test/acknowledge']) {
    await assert.rejects(showcaseApi(path,{method:'POST'}), /Saved showcase/);
  }
  await assert.rejects(showcaseApi('/api/inspections/'+'f'.repeat(32)), /not found/);
  assert.equal(requests.length, 1);
});
test('preserves the measurements of the deployed tuned detector and static report URLs', async () => {
  assert.equal(fixture.records.length, 24);
  assert.ok(fixture.records.every(r=>/^dinov2-tuned-.+-v1$/.test(r.model_id)), 'every saved example comes from the tuned detector');
  assert.ok(!JSON.stringify(fixture).includes('dinov3'), 'no obsolete detector name in the public snapshot');
  assert.equal(new Set(fixture.samples.map(s=>s.name)).size, 24);
  const record = fixture.records.find(r=>r.category==='pcb1'&&r.verdict==='Anomalous');
  assert.ok(record && record.score > record.threshold);
  assert.deepEqual(await showcaseApi('/api/inspections/'+record.id+'/messages'), []);
  const report = await showcaseApi('/api/benchmark/official');
  assert.equal(Object.keys(report.categories).length,12);
  assert.ok(report.mvtec, 'the MVTec AD check is part of the saved benchmark');
  assert.equal(assetUrl('/api/inspections/'+record.id+'/report'), './showcase/reports/'+record.id+'.html');
  assert.equal(assetUrl('/api/export.csv'), './showcase/inspections.csv');
});

test('both completed benchmark profiles preserve category-averaged image mAP',async()=>{
  const report=await showcaseApi('/api/benchmark/official');
  assert.equal(Object.keys(report.candidate.categories).length,12);
  for(const profile of [report,report.candidate]){
    const mean=Object.values(profile.categories).reduce((sum,c)=>sum+c.benchmark_mean.average_precision,0)/12;
    assert.ok(Math.abs(mean-profile.macro_mean.average_precision)<1e-12);
  }
  assert.ok(report.candidate.macro_mean.auroc>=0&&report.candidate.macro_mean.auroc<=1);
});
