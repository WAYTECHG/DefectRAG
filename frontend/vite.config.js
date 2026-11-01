import { defineConfig } from 'vite';
import {execSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {localBuildReceipt} from './localBuild.mjs';

// Shown in Help & references and in "Copy details", so a problem report says
// exactly which build someone was using.
function buildInfo(){
 const version=JSON.parse(readFileSync(new URL('./package.json',import.meta.url),'utf8')).version;
 let commit='local';
 try{commit=execSync('git rev-parse --short HEAD',{stdio:['ignore','pipe','ignore']}).toString().trim()||'local'}catch{}
 return {version,commit,built:new Date().toISOString().slice(0,10)};
}

export default defineConfig({base:'./',define:{__APP_BUILD__:JSON.stringify(buildInfo())},plugins:[localBuildReceipt()],server:{proxy:{'/api':'http://127.0.0.1:8765'}}});
