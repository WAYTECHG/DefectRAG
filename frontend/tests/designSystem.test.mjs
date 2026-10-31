import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {initialTheme,applyTheme,THEME_KEY} from '../src/theme.mjs';
import {overviewCards,dailyActivity,overviewRows} from '../src/overview.mjs';

const store=(value)=>{const m=new Map(value?[[THEME_KEY,value]]:[]);return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),m}};
const media=dark=>()=>({matches:dark});

test('a saved theme wins; otherwise the device setting is followed',()=>{
 assert.equal(initialTheme(store('dark'),media(false)),'dark');
 assert.equal(initialTheme(store('light'),media(true)),'light');
 assert.equal(initialTheme(store(),media(true)),'dark');
 assert.equal(initialTheme(store(),media(false)),'light');
 assert.equal(initialTheme({getItem(){throw Error('blocked')}},media(false)),'light','blocked storage falls back');
});

test('applying a theme toggles the root class and remembers the choice',()=>{
 const classes=new Set(),root={classList:{toggle:(c,on)=>on?classes.add(c):classes.delete(c)}},s=store();
 applyTheme('dark',root,s);assert.ok(classes.has('dark'));assert.equal(s.m.get(THEME_KEY),'dark');
 applyTheme('light',root,s);assert.ok(!classes.has('dark'));
});

test('every stylesheet colour comes from a token defined for both themes',async()=>{
 const tokens=await readFile(new URL('../src/tokens.css',import.meta.url),'utf8');
 const [light,dark]=tokens.split(':root.dark');
 const defined=t=>new Set([...t.matchAll(/--([a-z0-9-]+):/g)].map(m=>m[1]));
 for(const name of ['style.css','theme.css','design.css']){
  const css=await readFile(new URL('../src/'+name,import.meta.url),'utf8');
  assert.doesNotMatch(css,/#[0-9a-fA-F]{3,8}\b/,name+' has no hard-coded colours');
  for(const [,v] of css.matchAll(/var\(--([a-z0-9-]+)\)/g)){
   if(['split'].includes(v))continue;
   assert.ok(defined(light).has(v),`${name}: --${v} defined for light`);
  }
 }
 const colourTokens=[...defined(light)].filter(t=>!['radius','font-sans','font-mono'].includes(t));
 for(const t of colourTokens)assert.ok(defined(dark).has(t),`--${t} also defined for dark`);
});

test('overview cards show each result share and the chart counts per local day',()=>{
 const cards=overviewCards({total:4,counts:{Good:1,Anomalous:2,Uncertain:1},batches:[{batch:'LINE-A'},{batch:''}]});
 assert.deepEqual(cards.map(c=>[c.value,c.share]),[[4,null],[1,'25%'],[2,'50%'],[1,'25%']]);
 assert.equal(cards[0].detail,'1 named batch');
 const now=new Date(2026,9,31,12);
 const rows=[{created_at:new Date(2026,9,31,9).toISOString(),verdict:'Anomalous'},{created_at:new Date(2026,9,30,9).toISOString(),verdict:'Good'},{created_at:new Date(2026,8,1).toISOString(),verdict:'Good'}];
 const days=dailyActivity(rows,7,now);
 assert.equal(days.length,7);assert.deepEqual(days.at(-1),{date:'2026-10-31',total:1,unusual:1});assert.equal(days.at(-2).total,1);
 assert.equal(days.reduce((n,d)=>n+d.total,0),2,'older records fall outside the period');
 assert.deepEqual(overviewRows(rows,'unusual').map(r=>r.verdict),['Anomalous']);
});
