// Receipt for the local FastAPI dashboard only. Cloud builds use configFile:false.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const textTypes=new Set(['.js','.mjs','.jsx','.ts','.tsx','.css','.svg','.html','.json','.md','.txt']);
const fixed=['frontend/index.html','frontend/package.json','frontend/package-lock.json','frontend/vite.config.js','frontend/localBuild.mjs'];
async function inputs(root){
 const names=[...fixed];
 async function walk(folder){
  for(const item of await fs.readdir(path.join(root,folder),{withFileTypes:true})){
   if(item.isSymbolicLink())throw Error('Local UI inputs cannot be symlinks');
   const name=folder+'/'+item.name;
   if(item.isDirectory())await walk(name);
   else if(item.isFile()&&name!=='frontend/public/config.js')names.push(name);
  }
 }
 await walk('frontend/src');await walk('frontend/public');
 const result={};
 for(const name of names.sort()){
  const bytes=await fs.readFile(path.join(root,name));
  result[name]=hash(textTypes.has(path.extname(name))?Buffer.from(bytes.toString('utf8').replaceAll('\r\n','\n')):bytes);
 }
 return result;
}
export function localBuildReceipt(){
 let root,output,before,mode;
 return {name:'defectrag-local-build-receipt',apply:'build',enforce:'post',
  configResolved(config){root=path.resolve(config.root,'..');output=path.resolve(config.root,config.build.outDir);mode=config.mode},
  async buildStart(){before=await inputs(root)},
  async writeBundle(options,bundle){
   const after=await inputs(root);
   if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Dashboard sources changed during build; rebuild');
   const files={};
   for(const [name,item] of Object.entries(bundle))files[name]=hash(item.type==='chunk'?item.code:item.source);
   await fs.writeFile(path.join(output,'local-ui-build.json'),JSON.stringify({schema:1,protocol:1,mode,sources:after,files},null,2)+'\n');
  }
 };
}
