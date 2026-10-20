import test from 'node:test';
import assert from 'node:assert/strict';
import {authWorkflowEnabled,authStatus,requireStaff,registerAccount,submitAccessRequest,enrollTotp,verifyTotp,decideAccess,privateTeamImages} from '../src/authSecurity.mjs';

test('new authentication workflow is disabled unless explicitly configured',()=>{
 globalThis.window={};assert.equal(authWorkflowEnabled(),false);
 window.DEFECTRAG_PUBLIC_CONFIG={authWorkflowEnabled:'true'};assert.equal(authWorkflowEnabled(),false);
 window.DEFECTRAG_PUBLIC_CONFIG.authWorkflowEnabled=true;assert.equal(authWorkflowEnabled(),true);
 delete window.DEFECTRAG_PUBLIC_CONFIG;
});
for(const state of ['pending','rejected','revoked'])test(`${state} account is denied even with AAL2`,async()=>{
 const client={rpc:async()=>({data:{approved:false,authorized:false,aal2:true,request_status:state,revoked:state==='revoked'}})};
 await assert.rejects(requireStaff(client),/pending, rejected or revoked/);
});
test('approved AAL1 denied when mandatory MFA is on; AAL2 accepted',async()=>{
 const state={approved:true,authorized:true,aal2:false,mfa_required:true,revoked:false};
 const client={rpc:async()=>({data:state})};
 await assert.rejects(requireStaff(client),/authenticator/);
 state.aal2=true;assert.equal(await requireStaff(client),state);
 state.revoked=true;await assert.rejects(requireStaff(client),/revoked/);
});
test('unavailable or malformed authorization never grants access',async()=>{
 for(const reply of [{error:new Error('expired')},{data:null},{data:{approved:true}}])await assert.rejects(authStatus({rpc:async()=>reply}));
});
test('registration uses Supabase without role metadata, invitations or membership inserts',async()=>{
 const calls=[];const client={auth:{signUp:async payload=>{calls.push(payload);return {data:{session:null}}}},rpc:()=>assert.fail('No verified session')};
 assert.deepEqual(await registerAccount(client,{email:'new@example.invalid',password:'long-fixture-password',displayName:'Applicant',redirectTo:'https://example.invalid/'}),{confirmationRequired:true});
 assert.deepEqual(calls,[{email:'new@example.invalid',password:'long-fixture-password',options:{emailRedirectTo:'https://example.invalid/'}}]);
 await assert.rejects(registerAccount(client,{password:'short',displayName:'Applicant'}));assert.equal(calls.length,1);
});
test('verified registration submits only own bounded access request via RPC',async()=>{
 const calls=[];const client={auth:{signUp:async()=>({data:{session:{}}})},rpc:async(name,payload)=>{calls.push([name,payload]);return {data:{request_status:'pending'}}}};
 await registerAccount(client,{email:'new@example.invalid',password:'long-fixture-password',displayName:' Applicant '});
 assert.deepEqual(calls,[['defectrag_request_access',{p_display_name:'Applicant'}]]);
 await assert.rejects(submitAccessRequest({rpc:async()=>({error:new Error('Email confirmation required')})},'Applicant'),/confirmation/);
});
test('TOTP enrollment delegates to native Supabase and verifies exact challenge',async()=>{
 const calls=[];const client={auth:{mfa:{
  enroll:async p=>{calls.push(['enroll',p]);return {data:{id:'factor',totp:{qr_code:'fixture'}}}},
  challenge:async p=>{calls.push(['challenge',p]);return {data:{id:'challenge'}}},
  verify:async p=>{calls.push(['verify',p]);return {data:{access_token:'opaque-supabase-session'}}},
 }}};
 await enrollTotp(client);await verifyTotp(client,'factor','123456');
 assert.deepEqual(calls,[['enroll',{factorType:'totp',friendlyName:'DefectRAG authenticator'}],['challenge',{factorId:'factor'}],['verify',{factorId:'factor',challengeId:'challenge',code:'123456'}]]);
 await assert.rejects(verifyTotp(client,'factor','abcd'),/six-digit/);assert.equal(calls.length,3);
});
test('wrong and expired TOTP errors cannot report a successful session upgrade',async()=>{
 for(const message of ['Invalid code','Expired challenge']){
  const client={auth:{mfa:{challenge:async()=>({data:{id:'c'}}),verify:async()=>({error:new Error(message)})}}};
  await assert.rejects(verifyTotp(client,'f','123456'),new RegExp(message));
 }
 await assert.rejects(verifyTotp({auth:{mfa:{challenge:async()=>({error:new Error('rate limited')}),verify:()=>assert.fail('No verification')}}},'f','123456'),/rate limited/);
});
test('developer decisions use versioned RPC; unauthorized/conflicting decisions surface denial',async()=>{
 const calls=[];const client={rpc:async(name,payload)=>{calls.push([name,payload]);return {data:{status:'approved'}}}};
 for(const action of ['approve','reject','revoke'])await decideAccess(client,{user_id:'applicant',version:3},action);
 assert.ok(calls.every(([name,payload])=>name==='defectrag_decide_access'&&payload.p_version===3&&payload.p_user_id==='applicant'));
 await assert.rejects(decideAccess(client,{},'promote'));assert.equal(calls.length,3);
 for(const error of ['Developer AAL2 required','Request changed'])await assert.rejects(decideAccess({rpc:async()=>({error:new Error(error)})},{},'approve'),new RegExp(error));
});
test('private team images use authenticated downloads and release partial blob URLs',async()=>{
 const original=URL.createObjectURL,originalRevoke=URL.revokeObjectURL;const downloaded=[],revoked=[];
 URL.createObjectURL=blob=>'blob:'+blob;URL.revokeObjectURL=url=>revoked.push(url);
 try{
  let fail=false;const client={storage:{from:bucket=>({download:async path=>{downloaded.push([bucket,path]);return fail&&path==='heatmap'?{error:new Error('Access denied')}:{data:path}}})}};
  assert.deepEqual(await privateTeamImages(client,{image_path:'image',heatmap_path:'heatmap'}),['blob:image','blob:heatmap']);
  fail=true;await assert.rejects(privateTeamImages(client,{image_path:'image',heatmap_path:'heatmap'}),/Access denied/);
  assert.deepEqual(revoked,['blob:image']);assert.ok(downloaded.every(([bucket])=>bucket==='team-inspections'));
 }finally{URL.createObjectURL=original;URL.revokeObjectURL=originalRevoke}
});
