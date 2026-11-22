import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {deployedSummary} from '../src/benchmarkSummary.mjs';

const tuned={profile:'dinov2_tuned_v1',macro_mean:{image_auroc:0.9711,recall:0.9075,false_positive_rate:0.0704,pixel_auroc_224:0.988}};
const baseline={macro_mean:{auroc:0.9513,pixel_auroc:0.986}};

test('the deployed fine-tuned result is the headline, with the frozen baseline as "before"',()=>{
 const summary=deployedSummary(tuned,baseline);
 assert.equal(summary.cards[0].after,0.9711);
 assert.equal(summary.cards[0].before,0.9513);
 assert.deepEqual(summary.cards.map(c=>c.key),['image_auroc','recall','false_positive_rate','pixel_auroc']);
 assert.equal(summary.cards[3].before,0.986);
});

test('no deployed headline for another profile or a missing result',()=>{
 assert.equal(deployedSummary({...tuned,profile:'dinov2_highres_v1'},baseline),null);
 assert.equal(deployedSummary({profile:'dinov2_tuned_v1',status:'unverified'},baseline),null);
 assert.equal(deployedSummary(undefined,baseline),null);
});

test('the saved repository result matches the published 0.971 / 90.7% / 7.0%',()=>{
 const saved=JSON.parse(readFileSync(new URL('../../results/tuned_deployment_evaluation.json',import.meta.url)));
 const summary=deployedSummary(saved,{macro_mean:{auroc:0.9513}});
 assert.equal(summary.cards[0].after.toFixed(3),'0.971');
 assert.equal((summary.cards[1].after*100).toFixed(1),'90.7');
 assert.equal((summary.cards[2].after*100).toFixed(1),'7.0');
});
