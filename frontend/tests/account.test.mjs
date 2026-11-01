import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {accountSummary,loadAccount,roleLabel} from '../src/account.mjs';

test('summary names the signed-in person and role, and falls back to the email', () => {
 assert.deepEqual(accountSummary(null),{signedIn:false,name:'',role:'',text:'Not signed in'});
 const named=accountSummary({user:{id:'1',email:'a@b.co'},staff:{display_name:'  Wilbert Andrew ',role:'developer'}});
 assert.equal(named.text,'Signed in as Wilbert Andrew · Developer');assert.equal(named.email,'a@b.co');
 assert.equal(accountSummary({user:{id:'1',email:'a@b.co'},staff:null}).text,'Signed in as a@b.co');
 assert.equal(accountSummary({user:{id:'1',email:'a@b.co'},staff:{display_name:'',role:'staff'}}).text,'Signed in as a@b.co · Staff');
 assert.equal(roleLabel('unknown'),'');
});

test('loadAccount reads only the local session, never fails the page, and tolerates blocked staff rows', async () => {
 const client=(session,staff)=>({auth:{getSession:async()=>session},from:()=>({select:()=>({eq:()=>({maybeSingle:async()=>staff})})})});
 assert.equal(await loadAccount(client({data:{session:null},error:null})),null);
 assert.equal(await loadAccount(client({data:null,error:new Error('x')})),null);
 const user={id:'u1',email:'a@b.co'};
 assert.deepEqual(await loadAccount(client({data:{session:{user}},error:null},{data:{display_name:'W',role:'staff'},error:null})),{user,staff:{display_name:'W',role:'staff'}});
 assert.equal((await loadAccount(client({data:{session:{user}},error:null},{data:null,error:{message:'denied'}}))).staff,null);
 const throwing={auth:{getSession:async()=>({data:{session:{user}},error:null})},from:()=>{throw new Error('boom')}};
 assert.equal((await loadAccount(throwing)).staff,null);
});

test('the app shows the account in the top bar and offers a bulk "Mark all as seen" that confirms first', async () => {
 const main=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.ok(main.includes('Signed in as <strong>{who.name}</strong>'));
 assert.ok(main.includes("onClick={()=>go('team')}><UserCircle"));
 assert.ok(main.includes("setSeenAll({phase:'confirm',done:0,total:0})"),'bulk action asks for confirmation');
 assert.ok(main.includes("api('/api/alerts/'+id+'/acknowledge',{method:'POST'})"),'bulk action reuses the per-alert endpoint');
 assert.ok(main.includes('Promise.allSettled'),'one failure must not hide the others');
 assert.ok(main.includes("setNotice('')"),'status notices clear when changing page');
});
