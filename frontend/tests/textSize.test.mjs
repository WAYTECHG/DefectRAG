import test from 'node:test';
import assert from 'node:assert/strict';
import {initialTextSize,applyTextSize,stepTextSize,TEXT_SIZES,TEXT_SIZE_KEY} from '../src/textSize.mjs';
const store=(value)=>({value,getItem(){return this.value},setItem(k,v){this.value=v;this.key=k}});

test('desktop defaults to 80%, phones to 100%, and a saved choice always wins', () => {
 assert.equal(initialTextSize(store(null),1500),0.8);
 assert.equal(initialTextSize(store(null),390),1);
 assert.equal(initialTextSize(store('1.15'),390),1.15);
 assert.equal(initialTextSize(store('0.9'),1500),0.9);
 assert.equal(initialTextSize(store('7'),1500),0.8,'an unknown saved value is ignored');
 assert.equal(initialTextSize({getItem(){throw new Error('blocked')}},1500),0.8,'blocked storage must not break the page');
});

test('applying a size sets the page zoom, remembers it, and survives blocked storage', () => {
 const root={style:{}},saved=store(null);
 assert.equal(applyTextSize(0.9,root,saved),0.9);assert.equal(root.style.zoom,'0.9');assert.equal(saved.key,TEXT_SIZE_KEY);assert.equal(saved.value,'0.9');
 assert.equal(applyTextSize(1,root,saved),1);assert.equal(root.style.zoom,'','100% removes the override');
 assert.equal(applyTextSize(3,root,saved),1,'invalid sizes fall back to 100%');
 assert.doesNotThrow(()=>applyTextSize(0.8,root,{setItem(){throw new Error('blocked')}}));
});

test('A-/A+ step through the sizes and stop at both ends', () => {
 assert.equal(stepTextSize(0.8,-1),0.8);assert.equal(stepTextSize(0.8,1),0.9);
 assert.equal(stepTextSize(TEXT_SIZES.at(-1),1),TEXT_SIZES.at(-1));assert.equal(stepTextSize(1,-1),0.9);
});
