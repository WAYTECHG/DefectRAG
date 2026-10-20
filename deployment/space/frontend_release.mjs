// Offline build/verification manifests. Importing this module performs no work.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const receiptFile=output=>output+'.build.json';
const textExtensions=new Set(['.js','.jsx','.mjs','.json','.html','.css','.svg','.md','.txt']);
function relativeFile(value){
 if(typeof value!=='string'||!value||value.includes('\\')||path.posix.isAbsolute(value)||value.split('/').some(p=>!p||p==='.'||p==='..')||value.includes(':'))throw new Error('Unsafe manifest path');
 return value;
}
async function walk(directory,prefix=''){
 const files=[];
 for(const item of await fs.readdir(directory,{withFileTypes:true})){
  if(item.isSymbolicLink())throw new Error('Build inputs must not contain symlinks');
  const name=prefix+item.name;
  if(item.isDirectory())files.push(...await walk(path.join(directory,item.name),name+'/'));
  else if(item.isFile())files.push(name);
 }
 return files.sort();
}
export async function sourceFingerprint(root=ROOT){
 const names=['frontend/index.html','frontend/package.json','frontend/package-lock.json','frontend/vite.config.js',
  'deployment/zerogpu_phase1/client/package.json','deployment/zerogpu_phase1/client/package-lock.json'];
 for(const folder of ['frontend/src','frontend/public','frontend/tests'])for(const name of await walk(path.join(root,folder)))
  if(folder+'/'+name!=='frontend/public/config.js')names.push(folder+'/'+name);
 for(const name of await walk(path.join(root,'deployment/space')))
  if(!name.includes('/')&&/\.(js|mjs)$/.test(name))names.push('deployment/space/'+name);
 // Worker tests import this module; bind their tested dependency, too.
 names.push('deployment/supabase/functions/staff-notifications/worker.mjs','deployment/n8n/staff-notifications.json');
 names.push('deployment/supabase/functions/staff-notifications/direct-email.mjs');
 const hash=createHash('sha256');
 for(const name of names.sort()){
  let bytes=await fs.readFile(path.join(root,name));
  if(textExtensions.has(path.extname(name)))bytes=Buffer.from(bytes.toString('utf8').replaceAll('\r\n','\n'));
  hash.update(name+'\0'+digest(bytes)+'\n');
 }
 return hash.digest('hex');
}
async function fileHashes(output,names){
 const resolved=await fs.realpath(output),hashes={};
 for(const name of [...new Set(names)].sort()){
  relativeFile(name);const file=path.join(output,name),actual=await fs.realpath(file);
  if(!actual.startsWith(resolved+path.sep)||!(await fs.stat(actual)).isFile())throw new Error('Artifact escapes build directory');
  hashes[name]=digest(await fs.readFile(file));
 }
 return hashes;
}
export async function recordBuild(root,output,rollupOutput,before){
 const after=await sourceFingerprint(root);if(before!==after)throw new Error('Source changed during build; rebuild before verification');
 const publicFiles=await walk(path.join(root,'frontend/public'));
 const files=await fileHashes(output,[...rollupOutput.map(item=>item.fileName),...publicFiles,'index.html','config.js']);
 if(!Object.keys(files).some(name=>name.startsWith('assets/')&&name.endsWith('.js')))throw new Error('Missing compiled React application');
 const manifest={schema:1,source_fingerprint:after,files,verified:false};
 await fs.writeFile(receiptFile(output),JSON.stringify(manifest,null,2)+'\n');
 return manifest;
}
export async function validateBuild(root,output,{requireVerified=true}={}){
 const manifest=JSON.parse(await fs.readFile(receiptFile(output),'utf8'));
 if(manifest.schema!==1||!manifest.files||manifest.source_fingerprint!==await sourceFingerprint(root))throw new Error('Frontend source/test inputs changed; rebuild and verify');
 if(requireVerified&&manifest.verified!==true)throw new Error('Frontend build has no successful verification');
 const actual=await fileHashes(output,Object.keys(manifest.files));
 if(JSON.stringify(actual)!==JSON.stringify(manifest.files))throw new Error('Frontend build/configuration changed after verification');
 return manifest;
}
export async function verifyBuild(root,output){
 await validateBuild(root,output,{requireVerified:false});
 const tests=(await walk(path.join(root,'frontend/tests'))).filter(name=>name.endsWith('.test.mjs')).map(name=>'tests/'+name);
 const result=spawnSync(process.execPath,['--test',...tests],{cwd:path.join(root,'frontend'),encoding:'utf8',timeout:60000});
 if(result.status!==0)throw new Error('Frontend verification failed: '+(result.stderr||result.stdout||result.error?.message||'unknown'));
 const manifest=await validateBuild(root,output,{requireVerified:false});
 manifest.verified=true;
 manifest.verification={runner:'node --test',node:process.version,
  tests:Number(result.stdout.match(/tests\s+(\d+)/)?.[1]||0),
  passed:Number(result.stdout.match(/pass\s+(\d+)/)?.[1]||0)};
 await fs.writeFile(receiptFile(output),JSON.stringify(manifest,null,2)+'\n');
 return {manifest,summary:result.stdout.split('\n').filter(line=>/tests |pass |fail /.test(line)).join('\n')};
}
export async function stageBuild(root,source,destination){
 if(path.resolve(source)===path.resolve(destination))throw new Error('Stage from a separate tested build');
 const manifest=await validateBuild(root,source);
 // Fail closed rather than overwriting an installed configuration with blanks.
 const existing=await fs.readFile(path.join(destination,'config.js')).catch(error=>{if(error.code!=='ENOENT')throw error;return null});
 if(existing&&digest(existing)!==manifest.files['config.js'])throw new Error('Release configuration differs; build with the existing public config before staging');
 for(const name of Object.keys(manifest.files)){
  const target=path.join(destination,relativeFile(name));await fs.mkdir(path.dirname(target),{recursive:true});
  // Check ancestors before writing; never follow an existing outward symlink.
  const actualParent=await fs.realpath(path.dirname(target)),base=await fs.realpath(destination);
  if(actualParent!==base&&!actualParent.startsWith(base+path.sep))throw new Error('Stage path escapes destination');
  const current=await fs.lstat(target).catch(error=>{if(error.code!=='ENOENT')throw error;return null});
  if(current?.isSymbolicLink())throw new Error('Stage target is a symlink');
  await fs.copyFile(path.join(source,name),target);
 }
 // Commit receipt last. Partial staging cannot pass publisher validation.
 await validateBuild(root,source);
 await fs.writeFile(receiptFile(destination),JSON.stringify(manifest,null,2)+'\n');
 return validateBuild(root,destination);
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const [command,input,output]=process.argv.slice(2);
  const build=path.resolve(input||path.join(ROOT,'development-support/space/ui-dist'));
  if(command==='verify'){const result=await verifyBuild(ROOT,build);console.log(result.summary)}
  else if(command==='stage'){const result=await stageBuild(ROOT,build,path.resolve(output||path.join(ROOT,'development-support/space/ui-dist')));console.log(JSON.stringify({verified:true,files:Object.keys(result.files).length}))}
  else if(command==='check')console.log(JSON.stringify(await validateBuild(ROOT,build)));
  else throw new Error('Use verify, stage or check [build directory] [stage directory]');
 }catch(error){console.error(error.message);process.exitCode=1}
}
