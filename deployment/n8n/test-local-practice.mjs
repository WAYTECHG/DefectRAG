import assert from 'node:assert/strict';
import {createLedger, fixtureEvent as e, fixtureMarker as marker, startFixture} from './local-practice-fixture.mjs';
const begin = {operation: 'begin', event_id: e.event_id, lease_token: e.lease_token};
const finish = {...begin, operation: 'finish', receipt: '<synthetic@local.invalid>'};
let count = 0;
function check(name, fn) {fn(); count++; console.log(name + ': PASS');}
check('missing marker and wrong IDs denied without state change', () => {
  const l = createLedger(); assert.equal(l.request('', begin).status, 403);
  assert.equal(l.request(marker, {...begin, event_id: 'real-record-not-permitted'}).status, 403);
  assert.equal(l.status().effect, 'new');
});
check('reserve, accept and finish once; duplicate suppressed', () => {
  const l = createLedger(); assert.equal(l.request(marker, begin).body.execute, true);
  assert.equal(l.request(marker, finish).status, 409);
  assert.equal(l.accept(), true); assert.equal(l.accept(), false);
  assert.equal(l.request(marker, finish).body.done, true);
  assert.deepEqual(l.request(marker, begin).body, {execute: false, done: true});
  assert.equal(l.status().accepted, 1); assert.equal(l.status().realEmailsSent, 0);
});
check('SMTP failure leaves processing; retry quarantined', () => {
  const l = createLedger(); l.configure({failSmtp: true}); l.request(marker, begin);
  assert.equal(l.accept(), false); assert.equal(l.request(marker, begin).body.manual_review, true);
});
check('receipt failure after acceptance cannot resend', () => {
  const l = createLedger(); l.request(marker, begin); l.accept(); l.configure({failFinish: true});
  assert.equal(l.request(marker, finish).status, 503);
  assert.equal(l.request(marker, begin).body.execute, false); assert.equal(l.accept(), false);
});
check('controls reject unknown fields and nonboolean modes', () => {
  const l = createLedger(); assert.equal(l.configure({reset: true}), false);
  assert.equal(l.configure({failSmtp: 'false'}), false);
});
const f = await startFixture({httpPort: 0, smtpPort: 0, lifetimeMs: 10000});
try {
  const root = 'http://127.0.0.1:' + f.httpPort;
  assert.equal((await fetch(root + '/effect', {method: 'POST', body: JSON.stringify(begin)})).status, 403);
  assert.equal((await fetch(root + '/effect', {method: 'POST', headers: {'X-DefectRAG-Local-QA': marker}, body: '{bad'})).status, 400);
  assert.equal((await fetch(root + '/effect', {method: 'POST', headers: {'X-DefectRAG-Local-QA': marker}, body: 'x'.repeat(4100)})).status, 413);
  assert.equal((await fetch(root + '/other')).status, 404);
  assert.equal((await (await fetch(root + '/qa/status')).json()).accepted, 0);
  count++; console.log('actual loopback HTTP guard, route, JSON and size limits: PASS');
} finally {f.close();}
console.log(JSON.stringify({passed: count, actualSupabase: false, realEmailsSent: 0}));
