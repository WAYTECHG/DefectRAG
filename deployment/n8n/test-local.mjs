// Run ONLY in a disposable `docker run --network none` container. This harness
// never reads existing n8n config/credentials and never contacts Supabase.
import fs from 'node:fs/promises';
import http from 'node:http';
import net from 'node:net';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec=promisify(execFile);
if(process.env.DEFECTRAG_ISOLATED_N8N_TEST!=='1')throw Error('Disposable isolated test container required');
const event={event_id:'11111111-1111-4111-8111-111111111111',lease_token:'22222222-2222-4222-8222-222222222222',case_id:'33333333-3333-4333-8333-333333333333',kind:'created',version:1};
const callbackSecret='isolated-fixture-callback-secret-only';
let state=null,confirmed=true,failSMTP=false,failFinish=false,accepted=0,callbackCalls=0;
const bridge=http.createServer(async(req,res)=>{
 const chunks=[];for await(const chunk of req)chunks.push(chunk);
 const b=JSON.parse(Buffer.concat(chunks).toString());
 if(req.headers.authorization!=='Bearer '+callbackSecret||req.headers['x-defectrag-operation']!=='effect'||!confirmed||b.event_id!==event.event_id||b.lease_token!==event.lease_token){res.writeHead(403);res.end('{}');return}
 callbackCalls++;res.setHeader('Content-Type','application/json');
 if(b.operation==='finish'){
  if(failFinish){res.writeHead(503);res.end('{}');return}
  assert.equal(state,'processing');assert.ok(b.receipt);state='done';res.end('{"done":true}');return;
 }
 if(state==='done'){res.end('{"execute":false,"done":true}');return}
 if(state){res.end('{"execute":false,"done":false,"manual_review":true}');return}
 state='processing';res.end(JSON.stringify({execute:true,done:false,recipient_email:'supervisor@example.invalid',case_id:event.case_id,kind:'created',state:'Open',priority:'High',due_at:'2026-10-21T00:00:00Z'}));
});
const smtp=net.createServer(socket=>{
 socket.write('220 fixture.local ESMTP\r\n');let buffer='',data=false;
 socket.on('data',chunk=>{
  buffer+=chunk.toString();if(buffer.length>1024*1024){socket.destroy();return}
  for(;;){const index=buffer.indexOf('\r\n');if(index<0)break;const line=buffer.slice(0,index);buffer=buffer.slice(index+2);
   if(data){if(line==='.'){data=false;accepted++;socket.write('250 2.0.0 accepted by isolated sink\r\n')}continue}
   if(/^EHLO|^HELO/.test(line))socket.write('250-fixture.local\r\n250 SIZE 1048576\r\n');
   else if(/^MAIL FROM:/.test(line))socket.write('250 OK\r\n');
   else if(/^RCPT TO:/.test(line))socket.write(failSMTP?'550 fixture rejection\r\n':'250 OK\r\n');
   else if(line==='DATA'){data=true;socket.write('354 End with dot\r\n')}
   else if(line==='QUIT'){socket.end('221 bye\r\n')}
   else socket.write('250 OK\r\n');
  }
 });
});
await new Promise(resolve=>bridge.listen(18081,'127.0.0.1',resolve));
await new Promise(resolve=>smtp.listen(12525,'127.0.0.1',resolve));
const credentials=[{id:'ca_fixture_callback',name:'CA fixture callback',type:'httpHeaderAuth',data:{name:'Authorization',value:'Bearer '+callbackSecret}},
 {id:'ca_fixture_smtp',name:'CA fixture sink',type:'smtp',data:{host:'127.0.0.1',port:12525,secure:false,disableStartTls:true,user:'',password:''}}];
await fs.writeFile('/tmp/ca-fixture-credentials.json',JSON.stringify(credentials));
const production=JSON.parse(await fs.readFile('/input/corrective-actions.json','utf8'));
const results=[];
async function run(label,{ok=true,malformed=false}={}){
 const workflow=structuredClone(production);workflow.id='CAFixture';workflow.name='CA isolated fixture';
 const trigger=workflow.nodes.find(n=>n.name==='Authenticated case event');trigger.type='n8n-nodes-base.manualTrigger';trigger.typeVersion=1;trigger.parameters={};delete trigger.credentials;
 workflow.nodes.push({id:'fixture-input',name:'Fixture input',type:'n8n-nodes-base.code',typeVersion:2,position:[100,100],parameters:{jsCode:'return [{json:{body:'+JSON.stringify({...event,...(malformed?{kind:'AI_prediction'}:{})})+'}}];'}});
 workflow.connections['Authenticated case event'].main[0][0].node='Fixture input';workflow.connections['Fixture input']={main:[[{node:'Validate case event',type:'main',index:0}]]};
 for(const node of workflow.nodes){
  if(node.type==='n8n-nodes-base.httpRequest'){node.parameters.url='http://127.0.0.1:18081/effect';node.credentials={httpHeaderAuth:{id:'ca_fixture_callback',name:'CA fixture callback'}}}
  if(node.type==='n8n-nodes-base.emailSend'){node.parameters.fromEmail='fixture@example.invalid';node.credentials={smtp:{id:'ca_fixture_smtp',name:'CA fixture sink'}}}
  if(node.type==='n8n-nodes-base.respondToWebhook'){node.type='n8n-nodes-base.noOp';node.typeVersion=1;node.parameters={}}
 }
 await fs.writeFile('/tmp/ca-fixture-workflow.json',JSON.stringify([workflow]));
 await exec('n8n',['import:workflow','--input=/tmp/ca-fixture-workflow.json'],{timeout:45000});
 let success=true,output='';try{const r=await exec('n8n',['execute','--id=CAFixture','--rawOutput'],{timeout:45000,maxBuffer:4*1024*1024});output=r.stdout}catch(e){success=false;output=(e.stdout||'')+(e.stderr||'')}
 await fs.writeFile('/output/last-fixture-execution.txt',output);
 if(output.includes('"error":')||output.includes('Execution error'))success=false;
 if(success!==ok||(!results.length&&callbackCalls===0))throw Error(label+' unexpected workflow result: '+output.slice(-9000));
 results.push({scenario:label,passed:true,acceptedByLocalSink:accepted});console.log(label+': passed');
}
try{
 await exec('n8n',['import:credentials','--input=/tmp/ca-fixture-credentials.json'],{timeout:45000});
 await run('confirmed case sends one notification');assert.equal(accepted,1);assert.equal(state,'done');
 await run('duplicate event does not send again');assert.equal(accepted,1);
 confirmed=false;await run('unconfirmed backend event denied',{ok:false});assert.equal(accepted,1);confirmed=true;
 await run('raw prediction event rejected',{ok:false,malformed:true});assert.equal(accepted,1);
 state=null;failSMTP=true;await run('SMTP failure is not completion',{ok:false});assert.equal(accepted,1);assert.equal(state,'processing');failSMTP=false;
 await run('ambiguous effect cannot automatically replay',{ok:false});assert.equal(accepted,1);
 state=null;failFinish=true;await run('accepted email with lost receipt remains ambiguous',{ok:false});assert.equal(accepted,2);failFinish=false;
 await run('lost-receipt retry does not duplicate email',{ok:false});assert.equal(accepted,2);
 const report={mode:'actual isolated n8n + SMTP sink; simulated Supabase callbacks',externalNetworking:'none',realEmailsSent:0,acceptedByLocalSink:accepted,callbackCalls,results,limitations:['Production webhook trigger replaced with manual fixture trigger','Final webhook response replaced with no-op','Supabase SQL/RLS not executed','No external ticket connector configured']};
 await fs.writeFile('/output/n8n-local-result.json',JSON.stringify(report,null,2)+'\n');
 console.log('All isolated n8n scenarios passed. No external email or database access.');
}finally{bridge.close();smtp.close()}
