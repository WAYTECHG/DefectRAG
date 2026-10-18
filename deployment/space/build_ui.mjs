import path from 'node:path';
import fs from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
const folder=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(folder,'../..');
const {build}=await import(pathToFileURL(path.join(root,'frontend/node_modules/vite/dist/node/index.js')));
const output=path.join(root,'development-support/space/ui-dist');
await build({root:path.join(root,'frontend'),configFile:false,base:'./',
 resolve:{alias:{'@gradio/client':path.join(root,'deployment/zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js')}},
 build:{outDir:output,emptyOutDir:false},plugins:[{name:'space-transport',enforce:'pre',transform(code,id){
  if(id.replaceAll('\\','/')===path.join(root,'frontend/src/ArchiveDialog.jsx').replaceAll('\\','/')){
   return code.replace('All local inspections matching your current history filters will be archived, including matches beyond the first 500 displayed rows. They will disappear from the active history and review queue.',
    'Matching browser records will leave active history. For signed-in staff, this archives up to 500 matching visible records that you own, or records authorized for a developer.')
    .replace('This action does not change cloud records.','Signed-in staff archives affect their shared Supabase records; developer recovery follows workspace permissions.');
  }
  if(id.replaceAll('\\','/')===path.join(root,'frontend/src/cloud.js').replaceAll('\\','/')){
   return code.replace('const {url,key}=cloudConfig();return createClient(url,key);',
    "const {url,key}=cloudConfig(); const client=createClient(url,key); client.auth.onAuthStateChange((event)=>{if(['SIGNED_IN','SIGNED_OUT','TOKEN_REFRESHED'].includes(event))setTimeout(()=>window.dispatchEvent(new CustomEvent('defectrag-auth-change',{detail:{event}})),0)}); return client;");
  }
  if(id.replaceAll('\\','/')!==path.join(root,'frontend/src/main.jsx').replaceAll('\\','/'))return;
  if(!code.includes('const response=await fetch(url(path),options);'))throw new Error('Review changed API boundary');
  return `import {spaceFetch,spaceUrl} from ${JSON.stringify(path.join(folder,'transport.js').replaceAll('\\','/'))};\n`+code
   .replace('const response=await fetch(url(path),options);','const response=await spaceFetch(url(path),options);')
   .replace('const url=assetUrl;','const url=spaceUrl;')
   .replace('useEffect(()=>{refresh();const listener=',"useEffect(()=>{const update=e=>{refresh();if(e.detail?.event==='SIGNED_OUT'){setResult(null);setMessages([])}};window.addEventListener('defectrag-auth-change',update);return()=>window.removeEventListener('defectrag-auth-change',update)},[]); useEffect(()=>{refresh();const listener=")
   .replace('setResult(r);setMessages([]);go(\'inspect\');setFiles([]);',"setResult(r);setMessages([]);go('inspect');setFiles([]); if(r.storage==='supabase'){try{setResult(await api('/api/inspections/'+r.id))}catch(e){setError(e.message)}}")
   .replace('href={url(`/api/inspections/${result.id}/report`)}','href={url(result.report_url||`/api/inspections/${result.id}/report`)}')
   .replace('Local inference · images stay on this device','Live ZeroGPU inference · browser history is temporary; sign in for persistent staff records')
   .replace('Private on this device','Private browser session')
   .replaceAll('LOCAL DEVELOPMENT','LIVE CLOUD')
   .replace('The first request also loads the local encoder.','GPU jobs may wait for shared capacity and your available quota.')
   .replaceAll('LOCAL LLM','LIVE LLM')
   .replaceAll('RUNS LOCALLY','LIVE INSPECTION')
   .replace('Local generation','Evidence generation')
   .replace('Qwen via Ollama; retrieval fallback','Qwen in this Space; explicit retrieval fallback')
   .replace('Saved in your local log','Saved in your current workspace')
   .replace('Local workspace online','Browser workspace online')
   .replace('This build is a single-user local workspace. A separate free static showcase is included. Public live inference requires an isolated API and per-user storage.','This cloud build isolates anonymous browser sessions. Staff records use the configured Supabase workspace when its persistence adapter is enabled. A separate static showcase and the local application remain preserved.')
   .replace('Ollama / Qwen 2.5 3B','ZeroGPU / Qwen3 4B (cloud)')
   .replace('Archived local inspections','Archived workspace inspections')
   .replace('Restore archived local inspections, conversations and review alerts.','Restore archived workspace inspections, conversations and review alerts.')
   .replace('This recovery page controls the local single-user workspace. Cloud recovery is separately restricted to the developer role.','Anonymous browser recovery is temporary. Signed-in staff recovery follows the Supabase developer permissions.')
   .replace('Local review queue','Workspace review queue')
   .replace('Retrieving evidence and validating a local answer…','Retrieving evidence and validating the answer…');
 }}]});
// Config is supplied separately from the existing installation, never from .env.
const config=process.env.DEFECTRAG_PUBLIC_CONFIG_FILE;
if(config)await fs.copyFile(config,path.join(output,'config.js'));
console.log('Space build saved separately; original CSS and both existing builds preserved.');
