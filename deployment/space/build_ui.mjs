import path from 'node:path';
import fs from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
const folder=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(folder,'../..');
const {build}=await import(pathToFileURL(path.join(root,'frontend/node_modules/vite/dist/node/index.js')));
const output=path.join(root,'development-support/space/ui-dist');
await build({root:path.join(root,'frontend'),configFile:false,base:'./',
 resolve:{alias:{'@gradio/client':path.join(root,'deployment/zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js')}},
 build:{outDir:output,emptyOutDir:false},plugins:[{name:'space-transport',enforce:'pre',transform(code,id){
  if(id.replaceAll('\\','/')!==path.join(root,'frontend/src/main.jsx').replaceAll('\\','/'))return;
  if(!code.includes('const response=await fetch(url(path),options);'))throw new Error('Review changed API boundary');
  return `import {spaceFetch,spaceUrl} from ${JSON.stringify(path.join(folder,'transport.js').replaceAll('\\','/'))};\n`+code
   .replace('const response=await fetch(url(path),options);','const response=await spaceFetch(url(path),options);')
   .replace('const url=assetUrl;','const url=spaceUrl;')
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
   .replace('Retrieving evidence and validating a local answer…','Retrieving evidence and validating the answer…');
 }}]});
// Config is supplied separately from the existing installation, never from .env.
const config=process.env.DEFECTRAG_PUBLIC_CONFIG_FILE;
if(config)await fs.copyFile(config,path.join(output,'config.js'));
console.log('Space build saved separately; original CSS and both existing builds preserved.');
