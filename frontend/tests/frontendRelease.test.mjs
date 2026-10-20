import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {sourceFingerprint,recordBuild,validateBuild,stageBuild} from '../../deployment/space/frontend_release.mjs';

async function fixture(t){
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'defectrag-release-'));
 // Temporary directory created by this test only; resolved target checked before cleanup.
 t.after(async()=>{if(path.dirname(root)!==await fs.realpath(os.tmpdir()))throw new Error('Unsafe temporary cleanup');await fs.rm(root,{recursive:true,force:true})});
 const contents={'frontend/index.html':'<div id="root"/>','frontend/package.json':'{}','frontend/package-lock.json':'{}','frontend/vite.config.js':'export default {};',
  'frontend/src/main.jsx':'export default 1;','frontend/public/config.js':'public-placeholder','frontend/public/logo.svg':'<svg/>',
  'frontend/tests/unit.test.mjs':'//fixture','deployment/space/transport.js':'//transport','deployment/space/build_ui.mjs':'//builder',
  'deployment/supabase/functions/staff-notifications/worker.mjs':'//worker','deployment/n8n/staff-notifications.json':'{}',
  'deployment/zerogpu_phase1/client/package.json':'{}','deployment/zerogpu_phase1/client/package-lock.json':'{}'};
 for(const [name,text] of Object.entries(contents)){await fs.mkdir(path.dirname(path.join(root,name)),{recursive:true});await fs.writeFile(path.join(root,name),text)}
 const output=path.join(root,'runtime/cloud');await fs.mkdir(path.join(output,'assets'),{recursive:true});
 for(const [name,text] of Object.entries({'index.html':'<script src="assets/current.js"></script>','assets/current.js':'new react','assets/stale.js':'old react','config.js':'installed-public-config','logo.svg':'<svg/>'}))await fs.writeFile(path.join(output,name),text);
 await recordBuild(root,output,[{fileName:'index.html'},{fileName:'assets/current.js'}],await sourceFingerprint(root));
 return {root,output};
}
test('unverified build is rejected and stale disk chunks are excluded from upload manifest',async t=>{
 const {root,output}=await fixture(t);
 await assert.rejects(validateBuild(root,output),/successful verification/);
 const manifest=await validateBuild(root,output,{requireVerified:false});assert.equal(manifest.files['assets/stale.js'],undefined);
});
test('source changes, asset tampering and public configuration drift block publishing',async t=>{
 const {root,output}=await fixture(t);const manifest=JSON.parse(await fs.readFile(output+'.build.json','utf8'));manifest.verified=true;
 await fs.writeFile(output+'.build.json',JSON.stringify(manifest));await validateBuild(root,output);
 await fs.writeFile(path.join(output,'config.js'),'different-public-config');await assert.rejects(validateBuild(root,output),/changed after verification/);
 await fs.writeFile(path.join(output,'config.js'),'installed-public-config');
 await fs.writeFile(path.join(output,'assets/current.js'),'tampered');await assert.rejects(validateBuild(root,output),/changed after verification/);
 await fs.writeFile(path.join(output,'assets/current.js'),'new react');
 await fs.writeFile(path.join(root,'frontend/src/main.jsx'),'export default 2;');await assert.rejects(validateBuild(root,output),/inputs changed/);
});
test('CRLF checkout changes do not invalidate the source fingerprint',async t=>{
 const {root}=await fixture(t);const name=path.join(root,'frontend/src/main.jsx');await fs.writeFile(name,'one\ntwo\n');const before=await sourceFingerprint(root);
 await fs.writeFile(name,'one\r\ntwo\r\n');assert.equal(await sourceFingerprint(root),before);
});
test('changing the separately pinned Gradio client lock blocks a stale cloud build',async t=>{
 const {root,output}=await fixture(t);
 await fs.writeFile(path.join(root,'deployment/zerogpu_phase1/client/package-lock.json'),'{"changed":true}');
 await assert.rejects(validateBuild(root,output,{requireVerified:false}),/inputs changed/);
});
test('staging preserves conflicting installed public configuration and copies verified files only',async t=>{
 const {root,output}=await fixture(t);const receipt=JSON.parse(await fs.readFile(output+'.build.json','utf8'));receipt.verified=true;await fs.writeFile(output+'.build.json',JSON.stringify(receipt));
 const destination=path.join(root,'release');await fs.mkdir(destination);await fs.writeFile(path.join(destination,'config.js'),'different-installed-config');
 await assert.rejects(stageBuild(root,output,destination),/configuration differs/);assert.equal(await fs.readFile(path.join(destination,'config.js'),'utf8'),'different-installed-config');
 await fs.writeFile(path.join(destination,'config.js'),'installed-public-config');await stageBuild(root,output,destination);await validateBuild(root,destination);
 await assert.rejects(fs.stat(path.join(destination,'assets/stale.js')),/ENOENT/);
});
test('untrusted manifest paths and source edits during build fail closed',async t=>{
 const {root,output}=await fixture(t);const receipt=JSON.parse(await fs.readFile(output+'.build.json','utf8'));receipt.verified=true;receipt.files['../outside.js']='fake';await fs.writeFile(output+'.build.json',JSON.stringify(receipt));
 await assert.rejects(validateBuild(root,output),/Unsafe manifest path/);
 await assert.rejects(recordBuild(root,output,[],'old-source-fingerprint'),/Source changed during build/);
});
