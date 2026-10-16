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
test('preserves real measurements, final cited conversations and static report URLs', async () => {
  const record = fixture.records.find(r=>r.id==='a6226ef392eb417e8991369e890d816b');
  assert.equal(record.score, 0.09611436724662781);
  const messages = await showcaseApi('/api/inspections/'+record.id+'/messages');
  assert.equal(messages.filter(m=>m.mode==='llm').length, 2);
  assert.equal(messages.filter(m=>m.mode==='measurement_only').length, 2);
  assert.match(messages.find(m=>m.mode==='measurement_only').answer,/0.09611/);
  assert.equal(messages.at(-1).mode,'abstained');
  assert.equal(Object.keys((await showcaseApi('/api/benchmark/official')).categories).length,12);
  assert.equal(assetUrl('/api/inspections/'+record.id+'/report'), './showcase/reports/'+record.id+'.html');
  assert.equal(assetUrl('/api/export.csv'), './showcase/inspections.csv');
});
