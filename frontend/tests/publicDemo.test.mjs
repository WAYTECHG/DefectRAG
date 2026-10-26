import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {publicDemoAvailable} from '../src/publicDemo.mjs';

test('public demo requires an actual guest posture; denied and unverified sessions never fall back',()=>{
 for(const health of [{mode:'cloud_session_workspace'},{local_sync_enabled:true}]){
  assert.equal(publicDemoAvailable(health,{state:'guest'}),true);
  for(const state of ['authorized','pending','mfa','revoked','rejected','denied','checking','unavailable'])assert.equal(publicDemoAvailable(health,{state}),false);
 }
 assert.equal(publicDemoAvailable(null,{state:'guest'}),false);
 assert.equal(publicDemoAvailable({mode:'local_single_user'},{state:'guest'}),false);
});

const root=fileURLToPath(new URL('..',import.meta.url));
const built=await build({stdin:{contents:"export {default} from './src/PublicDemoNotice.jsx';",resolveDir:root,loader:'jsx'},bundle:true,write:false,platform:'node',format:'cjs',external:['react']});
const require=createRequire(new URL('../package.json',import.meta.url)),module={exports:{}};
new Function('require','module','exports',built.outputFiles[0].text)(require,module,module.exports);
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
test('demo entry preserves existing styles and clearly describes storage and quota limits',()=>{
 const cloud=renderToStaticMarkup(React.createElement(module.exports.default,{cloud:true,onStart(){}}));
 assert.ok(cloud.includes('Try an inspection'));assert.ok(cloud.includes('class="note"'));assert.ok(cloud.includes('belong to this browser session'));
 assert.ok(cloud.includes('Free service limits'));assert.ok(cloud.includes('Private Staff records are not shown'));
 const local=renderToStaticMarkup(React.createElement(module.exports.default,{cloud:false,onStart(){}}));
 assert.ok(local.includes('Without signing in, results stay on this computer'));
});

test('demo navigation checks guest posture and explicitly selects Personal without signing anyone out',async()=>{
 const source=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 const handler=source.slice(source.indexOf(' function openPublicDemo('),source.indexOf(' function resetInspection('));
 for(const state of ['guest','pending','authorized']){
  const calls=[];
  const run=new Function('publicDemoAvailable','health','inspectionAccess','switchToPersonalWorkspace','go',handler+';return openPublicDemo')(
   publicDemoAvailable,{mode:'cloud_session_workspace'},{state},()=>calls.push('personal'),page=>calls.push(page));
  run();assert.deepEqual(calls,state==='guest'?['personal','inspect']:[]);
 }
});
