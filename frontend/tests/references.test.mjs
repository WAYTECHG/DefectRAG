import test from 'node:test';
import assert from 'node:assert/strict';
import {pickReferences, rankLabel, referenceUrl} from '../src/references.mjs';

const library = {items: [{id: 'pcb1/00', thumb: 'data:a'}, {id: 'pcb1/01', thumb: 'data:b'}, {id: 'pcb1/02', thumb: 'data:c'}]};

test('the library file is addressed relatively so it works on the Space and locally', () => {
  assert.equal(referenceUrl('pcb1'), './assets/references/pcb1.json');
});

test('references keep the record order and gain their thumbnails', () => {
  const record = {references: [{id: 'pcb1/02', similarity: 0.97}, {id: 'pcb1/00', similarity: 0.93}]};
  const picked = pickReferences(record, library);
  assert.deepEqual(picked.map(p => p.id), ['pcb1/02', 'pcb1/00']);
  assert.deepEqual(picked.map(p => p.thumb), ['data:c', 'data:a']);
});

test('an id without a thumbnail is skipped instead of breaking the page', () => {
  const picked = pickReferences({references: [{id: 'pcb1/99', similarity: 0.9}, {id: 'pcb1/01', similarity: 0.8}]}, library);
  assert.deepEqual(picked.map(p => p.id), ['pcb1/01']);
});

test('records without references, or a missing library, give an empty list', () => {
  assert.deepEqual(pickReferences({}, library), []);
  assert.deepEqual(pickReferences({references: [{id: 'pcb1/00', similarity: 1}]}, null), []);
  assert.deepEqual(pickReferences(undefined, undefined), []);
});

test('photos are labelled by rank, not by a near-constant percentage', () => {
  assert.deepEqual([0, 1, 2].map(rankLabel), ['Closest match', '2nd closest', '3rd closest']);
  assert.equal(rankLabel(3), '4th closest');
});
