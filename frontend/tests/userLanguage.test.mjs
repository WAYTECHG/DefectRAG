import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resultLabel,environmentLabel,answerLabel,friendlyError,deliveryLabel} from '../src/userLanguage.mjs';
import {synchronizationText} from '../src/localSync.mjs';
import {storageDescription} from '../src/inspectionUX.mjs';

test('plain display labels preserve stored verdicts and distinguish local, cloud and saved examples',()=>{
 const stored=['Good','Anomalous','Uncertain'];assert.deepEqual(stored.map(resultLabel),['Looks normal','Unusual appearance','Needs a closer look']);assert.deepEqual(stored,['Good','Anomalous','Uncertain']);
 assert.equal(environmentLabel({mode:'local_single_user'}),'THIS COMPUTER');assert.equal(environmentLabel({mode:'cloud_session_workspace'}),'ONLINE APP');assert.equal(environmentLabel(null),'CONNECTING…');assert.equal(environmentLabel(null,true),'SAVED EXAMPLES');
 assert.equal(answerLabel('retrieval_only'),'REFERENCE INFORMATION');assert.equal(answerLabel('measurement_only'),'INSPECTION RESULT');assert.equal(answerLabel('abstained'),'NO SUPPORTED ANSWER');
 assert.equal(deliveryLabel('queued'),'Waiting to send');assert.equal(deliveryLabel('delivered'),'Accepted by email service');
});

test('errors give actionable guidance without displaying infrastructure internals or claiming success',()=>{
 for(const technical of ['Supabase request failed (403, 42501); no durable success was reported.','RPC schema cache PGRST202: hidden_function','Postgres constraint internal_name','JWT expired']){
  const display=friendlyError(technical);assert.doesNotMatch(display,/Supabase|PGRST|42501|hidden_function|internal_name|Postgres|JWT|RPC/);assert.doesNotMatch(display,/successfully saved|email sent/);
 }
 assert.match(friendlyError('Invalid login credentials'),/email or password/);
 assert.match(friendlyError('Invalid TOTP code'),/latest six-digit code/);
 assert.match(friendlyError('row-level security policy denied'),/account|Account/);
 assert.match(friendlyError('Case changed; refresh before updating'),/not been confirmed/);
 assert.match(friendlyError('GPU quota exceeded'),/usage limit/);
 assert.match(friendlyError('Reassign revoked owner/supervisor before proceeding'),/Choose currently approved Staff/);
 assert.match(friendlyError('Latest reviewed Reject disposition by active staff required'),/Reviewed and Reject/);
 assert.match(friendlyError('Invalid case transition'),/choose an available status/);
 assert.match(friendlyError('An audit note is required'),/short note/);
 assert.equal(friendlyError('Choose up to 20 images.'),'Choose up to 20 images.');
});

test('save guidance distinguishes private online, local-only, queued changes, conflict and public sharing',()=>{
 assert.match(storageDescription('supabase_personal'),/Only this account can see/);assert.match(storageDescription('supabase'),/Approved Staff can see/);
 assert.match(storageDescription('browser_session',true),/Saved only on this computer/);assert.match(storageDescription('browser_session'),/may disappear/);
 assert.match(synchronizationText({pending:2,last_synchronized:'old'}),/waiting to be confirmed online/);assert.doesNotMatch(synchronizationText({pending:2}),/up to date/);
 assert.match(synchronizationText({state:'conflict',last_synchronized:'old'}),/Both copies are kept/);assert.doesNotMatch(synchronizationText({scan_in_progress:true}),/up to date/);
 assert.match(synchronizationText({last_synchronized:'confirmed'}),/Team sharing is still a separate choice/);
});

const require=createRequire(new URL('../package.json',import.meta.url)),React=require('react'),render=require('react-dom/server').renderToStaticMarkup;
async function help(props){const out=await build({entryPoints:[fileURLToPath(new URL('../src/StaffHelp.jsx',import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',external:['react']});const m={exports:{}};new Function('require','module','exports',out.outputFiles[0].text)(require,m,m.exports);return render(React.createElement(m.exports.default,props))}
test('staff help explains the whole task path for both runtimes and keeps technical material optional',async()=>{
 for(const mode of ['local_single_user','cloud_session_workspace']){
  const html=await help({health:{mode}});for(const phrase of ['Start an inspection','Check the result','Keep work private','Review shared work','Track a corrective action','request access','security code'])assert.ok(html.includes(phrase),phrase);
  assert.match(html,/<details[^>]*><summary>Technical background and references/);assert.doesNotMatch(html,/<details[^>]*\bopen/);
  assert.match(html,/does not examine the photo itself/);assert.match(html,/does not remove this check/);assert.match(html,/does not approve the product/);
 }
 const online=await help({health:{mode:'cloud_session_workspace'}});assert.match(online,/may disappear when the app restarts/);
 const local=await help({health:{mode:'local_single_user'}});assert.match(local,/work stays on this computer/);
});

test('cloud publisher shares staff wording instead of injecting outdated engineering instructions',async()=>{
 const builder=await readFile(new URL('../../deployment/space/build_ui.mjs',import.meta.url),'utf8');assert.ok(builder.includes(".replace('return fetch(url(path),options)','return spaceFetch(url(path),options)')"));assert.doesNotMatch(builder,/Live ZeroGPU inference|explicit retrieval fallback|shared Supabase/);
 const main=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');assert.ok(main.includes('environmentLabel(health,SHOWCASE)'));assert.ok(main.includes('<StaffHelp health={health} showcase={SHOWCASE}/>'));assert.ok(main.includes('Results for the app’s inspection settings'));assert.ok(!main.includes('Show detailed measurements and technical test settings'));assert.ok(main.includes("Model: {result.model_id||'Not recorded'}"));
 // Native state/permission values remain in the source; these are display changes.
 assert.ok(main.includes("access.state==='authorized'&&activeWorkspace()==='personal'"));assert.ok(main.includes('value={v}>{resultLabel(v)}'));
});
