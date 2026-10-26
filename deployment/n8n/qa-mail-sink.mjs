// LOCAL SMTP SINK ONLY. No relay, DNS resolution, cloud client or stored body.
import http from 'node:http';
import net from 'node:net';
import {pathToFileURL} from 'node:url';
export async function startQASink({smtpPort=12526,statusPort=18082,lifetimeMs=1800000}={}){
 const sockets=new Set();let accepted=0,rejectedRecipients=0;
 const status=()=>({mode:'LOCAL QA MAIL SINK ONLY',processId:process.pid,accepted,rejectedRecipients,realEmailsSent:0,rawContentStored:false});
 const smtp=net.createServer(socket=>{
  sockets.add(socket);socket.on('close',()=>sockets.delete(socket));socket.on('error',()=>{});
  socket.setTimeout(10000,()=>socket.destroy());socket.write('220 qa-sink.invalid ESMTP\r\n');
  let buffer='',data=false,sender=false,recipient=false,bytes=0;
  socket.on('data',chunk=>{
   bytes+=chunk.length;if(bytes>65536){socket.destroy();return}buffer+=chunk.toString('utf8');
   for(;;){const n=buffer.indexOf('\r\n');if(n<0)break;const line=buffer.slice(0,n);buffer=buffer.slice(n+2);
    if(data){if(line==='.'){data=false;if(accepted===0){accepted++;socket.write('250 accepted by local QA sink\r\n')}else socket.write('550 Single-message slot already consumed\r\n')}continue}
    if(/^(EHLO|HELO)\b/i.test(line))socket.write('250-qa-sink.invalid\r\n250 SIZE 65536\r\n');
    else if(/^MAIL FROM:<fixture@example\.invalid>(?: SIZE=\d{1,5})?$/i.test(line)&&Number(line.match(/ SIZE=(\d+)/i)?.[1]||0)<=65536){sender=true;recipient=false;socket.write('250 OK\r\n')}
    else if(/^RCPT TO:<supervisor@example\.invalid>$/i.test(line)&&sender&&accepted===0){recipient=true;socket.write('250 OK\r\n')}
    else if(/^MAIL FROM:|^RCPT TO:/i.test(line)){rejectedRecipients++;socket.write('550 Fixed synthetic envelope only; no relay\r\n')}
    else if(line==='DATA'&&sender&&recipient){data=true;socket.write('354 End with dot\r\n')}
    else if(line==='QUIT')socket.end('221 bye\r\n');
    else if(line==='RSET'){sender=false;recipient=false;socket.write('250 OK\r\n')}
    else socket.write('500 Unsupported\r\n');
   }
  });
 });
 const server=http.createServer((req,res)=>{
  res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');
  if(req.method==='GET'&&req.url==='/status'){res.end(JSON.stringify(status()));return}
  res.writeHead(404);res.end('{}');
 });
 try{
  await new Promise((r,j)=>{smtp.once('error',j);smtp.listen(smtpPort,'127.0.0.1',r)});
  await new Promise((r,j)=>{server.once('error',j);server.listen(statusPort,'127.0.0.1',r)});
 }catch(e){smtp.close();server.close();throw e}
 const close=()=>{clearTimeout(timer);for(const s of sockets)s.destroy();smtp.close();server.close()};
 const timer=setTimeout(close,lifetimeMs);
 return {close,status,smtpPort:smtp.address().port,statusPort:server.address().port};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 if(process.env.DEFECTRAG_LOCAL_QA_MAIL_SINK!=='1')throw Error('Explicit local sink flag required');
 const sink=await startQASink();console.log(JSON.stringify({...sink.status(),bound:'127.0.0.1 inside n8n container',expiresMinutes:30}));
 process.once('SIGINT',sink.close);process.once('SIGTERM',sink.close);
}
