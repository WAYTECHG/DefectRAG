import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import {normalizeBatchName,batchNameTaken,storageDescription,personalSaveAccess} from '../src/inspectionUX.mjs';
import {inspectionReadiness} from '../src/inspectionReadiness.mjs';

test('batch names reject case/spacing/compatibility variants without blocking retries',()=>{
 assert.equal(normalizeBatchName('  ＱＡ  Batch '),'qa batch');
 assert.ok(batchNameTaken('qa batch',[{batch:' QA  BATCH '}]));
 const base={health:{status:'ok',mode:'local_single_user'},files:[{name:'x.jpg',size:4,type:'image/jpeg'}],multiple:true,batch:'qa batch',knownBatches:[{batch:'QA BATCH'}]};
 assert.equal(inspectionReadiness(base).code,'duplicate_batch');
 assert.equal(inspectionReadiness({...base,retry:true}).disabled,false);
 assert.equal(inspectionReadiness({...base,batch:'new'}).disabled,false);
 assert.equal(inspectionReadiness({...base,multiple:false}).disabled,false,'Individual label grouping is unchanged');
});

test('durable private storage is gated by approved account assurance, not signup alone',()=>{
 for(const state of ['guest','checking','pending','rejected','revoked','mfa','unavailable']){
  const result=personalSaveAccess(state);assert.equal(result.allowed,false);assert.ok(result.reason.length>20);
 }
 assert.equal(personalSaveAccess('authorized').allowed,true);
 assert.match(storageDescription('browser_session'),/Temporary/);
 assert.match(storageDescription('browser_session',true),/Saved only on this computer/);
 assert.match(storageDescription('local_account'),/confirm it has also reached the online account/);
 assert.match(storageDescription('supabase_personal'),/Saved online in Personal Workspace/);
 assert.match(storageDescription(undefined),/not automatically/);
});

async function component(path,name='default'){
 const result=await build({entryPoints:[fileURLToPath(new URL(path,import.meta.url))],bundle:true,platform:'node',format:'cjs',write:false,external:['react','react-dom']});
 const require=createRequire(new URL('../package.json',import.meta.url)),module={exports:{}};
 new Function('require','module','exports',result.outputFiles[0].text)(require,module,module.exports);
 return {Component:module.exports[name]||module.exports,React:require('react'),render:require('react-dom/server').renderToStaticMarkup};
}

test('upload guidance distinguishes unprocessed selections from historical identity',async()=>{
 const {Component,React,render}=await component('../src/InspectionDraft.jsx');
 const markup=render(React.createElement(Component,{multiple:true,files:[{}]}));
 assert.match(markup,/Photos do not need to be inspected first/);assert.match(markup,/ready to inspect/);
 assert.match(markup,/A filename does not tell/);
});

test('guest storage controls are disabled with explanation, while approved saving remains available',async()=>{
 const {Component,React,render}=await component('../src/WorkspaceShare.jsx');
 const props={record:{id:'x',storage:'browser_session'},enabled:true,messages:[]};
 const guest=render(React.createElement(Component,{...props,access:{state:'guest'}}));
 assert.match(guest,/disabled=""[^>]*>Save to Personal/);assert.match(guest,/approved Staff account and its security code/);
 const staff=render(React.createElement(Component,{...props,access:{state:'authorized'}}));
 assert.doesNotMatch(staff,/disabled=""[^>]*>Save to Personal/);
});

test('an unconfigured local gallery offers public browsing without implying automatic publication',async()=>{
 const {Component,React,render}=await component('../src/CommunityGallery.jsx','GalleryUnavailableNotice');
 const local=render(React.createElement(Component,{local:true}));
 assert.match(local,/class="note"/);assert.match(local,/Public sharing is not available from this computer yet/);
 assert.match(local,/href="https:\/\/wizzas-defectrag\.hf\.space\/#gallery"/);
 assert.match(local,/target="_blank" rel="noreferrer"/);assert.match(local,/does not publish a local inspection/);
 const cloud=render(React.createElement(Component,{local:false}));
 assert.match(cloud,/public gallery is not available yet/);assert.doesNotMatch(cloud,/<a |this device/);
});
