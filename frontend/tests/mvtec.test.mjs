import test from 'node:test';
import assert from 'node:assert/strict';
import {markSymbol, mvtecCards, mvtecRows, productLabel} from '../src/mvtec.mjs';

const arms = [
  {key: 'A_random_frozen', label: 'Random-sample memory'},
  {key: 'B_coreset_frozen', label: 'Coreset memory'},
  {key: 'C_coreset_tuned', label: 'Coreset + fine-tuned encoder'},
];
const summary = {
  arms,
  macro_mean: {
    A_random_frozen: {auroc: 0.986, pixel_auroc: 0.886},
    B_coreset_frozen: {auroc: 0.992, pixel_auroc: 0.888},
    C_coreset_tuned: {auroc: 0.992, pixel_auroc: 0.881},
  },
  categories: {
    metal_nut: {n_test: 115, arms: {A_random_frozen: {auroc: 1}, B_coreset_frozen: {auroc: 1}, C_coreset_tuned: {auroc: 1, pixel_auroc: 0.976}}, differences: {'B-A': [0, 0], 'C-B': [0, 0], 'C-A': [0, 0]}},
    cable: {n_test: 150, arms: {A_random_frozen: {auroc: 0.961}, B_coreset_frozen: {auroc: 0.984}, C_coreset_tuned: {auroc: 0.993, pixel_auroc: 0.975}}, differences: {'B-A': [0.01, 0.04], 'C-B': [0.001, 0.02], 'C-A': [0.02, 0.05]}},
    wood: {n_test: 79, arms: {A_random_frozen: {auroc: 0.98}, B_coreset_frozen: {auroc: 0.986}, C_coreset_tuned: {auroc: 0.974, pixel_auroc: 0.716}}, differences: {'B-A': [-0.01, 0.02], 'C-B': [-0.03, -0.002], 'C-A': [-0.03, 0.01]}},
  },
};

test('product keys become readable names', () => {
  assert.equal(productLabel('metal_nut'), 'Metal nut');
  assert.equal(productLabel('cable'), 'Cable');
});

test('cards show each variant with its macro AUROC', () => {
  const cards = mvtecCards(summary);
  assert.deepEqual(cards.map(c => c.auroc), [0.986, 0.992, 0.992]);
  assert.equal(cards[2].label, 'Coreset + fine-tuned encoder');
});

test('rows keep the three AUROCs in variant order and mark only clear differences', () => {
  const rows = mvtecRows(summary);
  const cable = rows.find(r => r.key === 'cable');
  assert.deepEqual(cable.values, [0.961, 0.984, 0.993]);
  assert.equal(cable.coreset, 'better');
  assert.equal(cable.tuned, 'better');
  assert.equal(rows.find(r => r.key === 'metal_nut').coreset, '');
  const wood = rows.find(r => r.key === 'wood');
  assert.equal(wood.coreset, '');
  assert.equal(wood.tuned, 'worse');
  assert.equal(wood.pixel, 0.716);
});

test('symbols are empty unless a difference is clear', () => {
  assert.equal(markSymbol('better'), '▲');
  assert.equal(markSymbol('worse'), '▼');
  assert.equal(markSymbol(''), '');
});

test('a missing summary gives empty lists instead of an error', () => {
  assert.deepEqual(mvtecCards(undefined), []);
  assert.deepEqual(mvtecRows(undefined), []);
});
