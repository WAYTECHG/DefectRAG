// Separate output; the production React sources, assets and package files stay intact.
import path from 'node:path';
import fs from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
const folder=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(folder,'../..');
const {build}=await import(pathToFileURL(path.join(root,'frontend/node_modules/vite/dist/node/index.js')));
const output=path.join(root,'development-support/zerogpu-phase1/ui-dist');
const entry=path.join(root,'frontend/src/main.jsx').replaceAll('\\','/');
await build({root:path.join(root,'frontend'),configFile:false,base:'./',
  resolve:{alias:{'@gradio/client':path.join(folder,'client/node_modules/@gradio/client/dist/index.js')}},
  build:{outDir:output,emptyOutDir:false},plugins:[{name:'isolated-phase1-transport',enforce:'pre',
    transform(code,id){if(id.replaceAll('\\','/')!==entry)return;
      const original='const response=await fetch(url(path),options);';
      if(!code.includes(original))throw new Error('Existing API boundary changed; inspect before transforming');
      return `import {phase1Fetch} from ${JSON.stringify(path.join(folder,'transport.js').replaceAll('\\','/'))};\n`+
        code.replace(original,'const response=await phase1Fetch(url(path),options);')
            .replace('Local inference · images stay on this device','Compatibility test · public PCB1 fixture only');
    }}]});
await fs.writeFile(path.join(output,'PHASE1_BUILD.json'),JSON.stringify({isolated:true,
  source_changed:false,transport:'@gradio/client',output},null,2));
