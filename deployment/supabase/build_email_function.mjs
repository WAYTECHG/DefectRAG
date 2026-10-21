// Offline, paste-ready Dashboard package. No CLI installation or secret input.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(path.join(root,'frontend/package.json'));
const {build}=require('esbuild');
const inputs=['deployment/supabase/functions/staff-notifications/index.ts',
 'deployment/supabase/functions/staff-notifications/worker.mjs',
 'deployment/supabase/functions/staff-notifications/direct-email.mjs','deployment/supabase/config.toml'];
const digest=b=>createHash('sha256').update(b).digest('hex');
async function hashes(){return Object.fromEntries(await Promise.all(inputs.map(async name=>[name,digest((await fs.readFile(path.join(root,name))).toString().replaceAll('\r\n','\n'))])))}
const before=await hashes();
const built=await build({absWorkingDir:root,entryPoints:[inputs[0]],bundle:true,write:false,platform:'neutral',format:'esm',target:'es2022',minify:false,logLevel:'silent'});
assert.deepEqual(await hashes(),before,'Source changed during packaging');
const code=built.outputFiles[0].text;
assert.ok(!/^import\s/m.test(code),'Package must contain its local imports');
let handler;
const evaluate=new Function('Deno','fetch',code);
const noNetwork=()=>assert.fail('Smoke tests must never contact a network');
const env={DEFECTRAG_NOTIFICATIONS_ENABLED:'0'};
evaluate({env:{get:name=>env[name]},serve:fn=>{handler=fn}},noNetwork);
assert.equal(typeof handler,'function');
const post=()=>new Request('https://fixture.invalid/functions/v1/staff-notifications',{method:'POST'});
let response=await handler(post());assert.equal(response.status,503);assert.deepEqual(await response.json(),{error:'notifications_disabled'});
env.DEFECTRAG_NOTIFICATIONS_ENABLED='1';env.DEFECTRAG_NOTIFICATION_WORKER_SECRET='fixture-secret-only-32-characters-minimum';
response=await handler(post());assert.equal(response.status,401);assert.deepEqual(await response.json(),{error:'unauthorized'});
response=await handler(new Request('https://fixture.invalid'));assert.equal(response.status,405);
const checkHeaders={'X-DefectRAG-Check-Event':'11111111-1111-4111-8111-111111111111'};
response=await handler(new Request('https://fixture.invalid',{method:'POST',headers:checkHeaders}));assert.equal(response.status,401);
checkHeaders.Authorization='Bearer '+env.DEFECTRAG_NOTIFICATION_WORKER_SECRET;
response=await handler(new Request('https://fixture.invalid',{method:'POST',headers:checkHeaders}));assert.equal(response.status,409);
env.DEFECTRAG_NOTIFICATIONS_ENABLED='0';
response=await handler(new Request('https://fixture.invalid',{method:'POST',headers:checkHeaders}));assert.equal(response.status,200);assert.equal((await response.json()).ready_for_qa,false);
const output=path.join(root,process.argv.includes('--diagnostics')?'runtime/email-diagnostics-release':'runtime/email-function-release');await fs.mkdir(output,{recursive:true});
await fs.writeFile(path.join(output,'index.ts'),code);
await fs.writeFile(path.join(output,'manifest.json'),JSON.stringify({function:'staff-notifications',inputs:before,bundle_sha256:digest(code),
 offline_checks:['bundled source has no local imports','disabled POST503 without network','enabled unauthorized POST401 without network','GET405',
 'unauthorized diagnostic401 without network','enabled diagnostic409 without network','disabled diagnostic200 without network'],
 production_deployed:false,secrets_read:false,scope:'single function; preserve delivery0; deployment needs approval'},null,2)+'\n');
console.log(JSON.stringify({paste_ready_file:path.join(output,'index.ts'),bundle_sha256:digest(code),offline_checks_passed:7,production_deployed:false}));
