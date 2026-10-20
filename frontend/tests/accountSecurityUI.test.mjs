import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

// Render the real JSX using the existing Vite/esbuild and React dependencies.
// No browser, authentication request, mail, database or service starts.
const root=fileURLToPath(new URL('..',import.meta.url));
const result=await build({stdin:{contents:"import Component from './src/AccountSecurity.jsx'; export default Component;",resolveDir:root,loader:'jsx'},
 bundle:true,write:false,platform:'node',format:'cjs',external:['react']});
const require=createRequire(new URL('../package.json',import.meta.url));
const module={exports:{}};new Function('require','module','exports',result.outputFiles[0].text)(require,module,module.exports);
const Component=module.exports.default,React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
const render=props=>renderToStaticMarkup(React.createElement(Component,{client:{},onChange(){},...props}));
test('registration stays hidden during MFA bootstrap unless separately enabled',()=>{
 globalThis.window={DEFECTRAG_PUBLIC_CONFIG:{authWorkflowEnabled:true}};
 const html=render({user:null});assert.ok(html.includes('Self-registration is not enabled'));
 assert.ok(!html.includes('Register account')&&!html.includes('New password'));
});
test('enabled registration uses existing dashboard classes and accessible labelled fields',()=>{
 window.DEFECTRAG_PUBLIC_CONFIG.registrationEnabled=true;
 const html=render({user:null});
 for(const phrase of ['login-form','Display name','Email','New password','Register account','Demo Mode'])assert.ok(html.includes(phrase));
 assert.ok(!html.includes('Staff access management'));
});
test('unverified client metadata cannot expose developer management on first render',()=>{
 const html=render({user:{id:'fixture',email:'test@example.invalid',user_metadata:{role:'developer'}}});
 assert.ok(html.includes('Account access &amp; security'));
 assert.ok(!html.includes('Staff access management')&&!html.includes('Approve access'));
 assert.ok(html.includes('Set up authenticator'));
});
