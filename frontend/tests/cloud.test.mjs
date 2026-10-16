import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=(await readFile(new URL('../src/cloud.js',import.meta.url),'utf8')).replaceAll('import.meta.env','({})');
globalThis.window={DEFECTRAG_PUBLIC_CONFIG:{}};
const {cloudConfigured,cloudClient}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('unconfigured cloud makes no request and rejects a client',async()=>{
  assert.equal(cloudConfigured(),false);
  await assert.rejects(cloudClient(),/not connected/);
});
test('only public keys are accepted; legacy service-role keys are rejected',()=>{
  const config=window.DEFECTRAG_PUBLIC_CONFIG;
  config.supabaseUrl='https://example.supabase.co';
  for(const key of ['sb_secret_test','', 'header.'+btoa(JSON.stringify({role:'service_role'}))+'.signature']){
    config.supabasePublishableKey=key;assert.equal(cloudConfigured(),false);
  }
  for(const key of ['sb_publishable_test','header.'+btoa(JSON.stringify({role:'anon'}))+'.signature']){
    config.supabasePublishableKey=key;assert.equal(cloudConfigured(),true);
  }
});
