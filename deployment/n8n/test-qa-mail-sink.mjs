import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import {once} from 'node:events';
import {startQASink} from './qa-mail-sink.mjs';
test('actual SMTP sink accepts one synthetic envelope, refuses others and never relays',async()=>{
 const sink=await startQASink({smtpPort:0,statusPort:0,lifetimeMs:10000});
 const socket=net.createConnection({host:'127.0.0.1',port:sink.smtpPort});
 let buffer='',waiting=[];
 socket.on('data',chunk=>{buffer+=chunk.toString();drain()});
 function drain(){for(;;){const match=buffer.match(/^([\s\S]*?\r\n)/);if(!match||!waiting.length)break;buffer=buffer.slice(match[1].length);waiting.shift()(match[1].trim())}}
 const line=()=>new Promise(resolve=>{waiting.push(resolve);drain()});
 async function command(text,prefix){socket.write(text+'\r\n');assert.ok((await line()).startsWith(prefix));}
 try{
  await once(socket,'connect');
  assert.ok((await line()).startsWith('220'));
  await command('EHLO fixture','250-');assert.ok((await line()).startsWith('250 '));
  await command('MAIL FROM:<fixture@example.invalid> SIZE=1024','250');
  await command('RCPT TO:<not-allowed@example.invalid>','550');
  await command('RCPT TO:<supervisor@example.invalid>','250');
  await command('DATA','354');await command('Subject: QA only\r\n\r\nSynthetic\r\n.','250');
  await command('RCPT TO:<supervisor@example.invalid>','550');
  const status=await(await fetch('http://127.0.0.1:'+sink.statusPort+'/status')).json();
  assert.equal(status.accepted,1);assert.equal(status.rejectedRecipients,2);assert.equal(status.realEmailsSent,0);assert.equal(status.rawContentStored,false);
  assert.equal((await fetch('http://127.0.0.1:'+sink.statusPort+'/status',{method:'POST'})).status,404);
 }finally{socket.destroy();sink.close()}
});
