import { defineConfig } from 'vite';
import {localBuildReceipt} from './localBuild.mjs';
export default defineConfig({base:'./',plugins:[localBuildReceipt()],server:{proxy:{'/api':'http://127.0.0.1:8765'}}});
