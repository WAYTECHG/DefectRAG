import path from 'node:path';
import fs from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {sourceFingerprint,recordBuild} from './frontend_release.mjs';
const folder=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(folder,'../..');
const {build}=await import(pathToFileURL(path.join(root,'frontend/node_modules/vite/dist/node/index.js')));
const output=process.env.DEFECTRAG_SPACE_BUILD_OUT?path.resolve(process.env.DEFECTRAG_SPACE_BUILD_OUT):path.join(root,'development-support/space/ui-dist');
// Vite copies public/config.js, which is deliberately blank in source control.
// Preserve installed public settings before building; never read secrets from .env.
const publicConfigFile=process.env.DEFECTRAG_PUBLIC_CONFIG_FILE;
const preservedConfig=await fs.readFile(publicConfigFile||path.join(output,'config.js'),'utf8').catch(error=>{
 if(publicConfigFile)throw error;
 return 'window.DEFECTRAG_PUBLIC_CONFIG = {supabaseUrl:"",supabasePublishableKey:""};\n';
});
if(publicConfigFile&&!preservedConfig.includes('sb_publishable_'))throw new Error('Expected the existing Supabase public configuration.');
const fingerprint=await sourceFingerprint(root);
let transported=false;
const result=await build({root:path.join(root,'frontend'),configFile:false,base:'./',
 resolve:{alias:{'@gradio/client':path.join(root,'deployment/zerogpu_phase1/client/node_modules/@gradio/client/dist/index.js')}},
 build:{outDir:output,emptyOutDir:false},plugins:[{name:'space-transport',enforce:'pre',transform(code,id){
  // Windows paths are case-insensitive: a build started from "desktop\defectrag-v2"
  // must still match Vite's real-cased "Desktop\DefectRAG-v2" module id.
  const same=(a,b)=>{a=a.replaceAll('\\','/');b=b.replaceAll('\\','/');return process.platform==='win32'?a.toLowerCase()===b.toLowerCase():a===b};
  if(!same(id,path.join(root,'frontend/src/main.jsx')))return;
  transported=true;
  if(!code.includes('return fetch(url(path),options)'))throw new Error('Review changed API boundary');
  return `import {spaceFetch,spaceUrl} from ${JSON.stringify(path.join(folder,'transport.js').replaceAll('\\','/'))};\n`+code
   .replace('return fetch(url(path),options)','return spaceFetch(url(path),options)')
   .replace('const url=assetUrl;','const url=spaceUrl;')
   .replace('href={url(`/api/inspections/${result.id}/report`)}','href={url(result.report_url||`/api/inspections/${result.id}/report`)}');

 }}]});
// Without the transport the cloud app cannot reach the queue or send the guest
// workspace header; never record such a build as releasable.
if(!transported)throw new Error('Space transport was not applied to main.jsx; build refused.');
// Config is supplied separately from the existing installation, never from .env.
await fs.writeFile(path.join(output,'config.js'),preservedConfig);
await recordBuild(root,output,Array.isArray(result)?result.flatMap(value=>value.output):result.output,fingerprint);
console.log('Separate cloud build recorded. Verify and stage it before publishing; existing builds remain preserved.');
