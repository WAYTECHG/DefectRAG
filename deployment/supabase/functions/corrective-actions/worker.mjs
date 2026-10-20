// Purpose-limited server bridge. n8n never receives a Supabase service key.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
function secret(a,b){if(typeof b!=='string'||b.length<32||typeof a!=='string'||a.length!==b.length+7)return false;let diff=0;const expected='Bearer '+b;for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^expected.charCodeAt(i);return diff===0}
function endpoint(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.hash)throw Error('configuration');return u.href}
export async function handleCA(request,{env,fetcher=fetch,now=()=>performance.now(),budgetMs=100000}){
 if(request.method!=='POST')return reply({error:'method_not_allowed'},405);
 if(env.DEFECTRAG_CA_AUTOMATION_ENABLED!=='1')return reply({error:'automation_disabled'},503);
 const callback=request.headers.get('X-DefectRAG-Operation')==='effect';
 const required=callback?env.DEFECTRAG_CA_CALLBACK_SECRET:env.DEFECTRAG_CA_WORKER_SECRET;
 if(!secret(request.headers.get('Authorization'),required))return reply({error:'unauthorized'},401);
 const deadline=now()+Math.min(100000,Math.max(1,budgetMs));
 async function call(url,options,ms=15000){
  const remaining=Math.min(ms,deadline-now());if(remaining<=0)throw Error('deadline');
  const controller=new AbortController();let timer;
  try{return await Promise.race([(async()=>{const r=await fetcher(url,{...options,signal:controller.signal,redirect:'error'});if(!r.ok)throw Error('http');return await r.json()})(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('timeout'))},remaining)})])}finally{clearTimeout(timer)}
 }
 try{
  const base=new URL(endpoint(env.SUPABASE_URL)).origin;
  if(!env.SUPABASE_SERVICE_ROLE_KEY)throw Error('configuration');
  const rpc=(name,body)=>call(base+'/rest/v1/rpc/'+name,{method:'POST',headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:'Bearer '+env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(callback){
   // Bound body consumption as well as size, even for chunked input.
   const reader=request.body?.getReader();if(!reader)return reply({error:'invalid_event'},400);
   let timer;const chunks=[];let size=0;
   try{await Promise.race([(async()=>{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>2048)throw Error('body_limit');chunks.push(value)}})(),new Promise((_,reject)=>{timer=setTimeout(()=>{reader.cancel().catch(()=>{});reject(Error('timeout'))},Math.min(3000,Math.max(1,deadline-now())))})])}finally{clearTimeout(timer);reader.releaseLock()}
   const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length}
   const b=JSON.parse(new TextDecoder().decode(bytes));
   if(!UUID.test(b.event_id)||!UUID.test(b.lease_token)||!['begin','finish'].includes(b.operation)||
    (b.operation==='finish'&&(typeof b.receipt!=='string'||b.receipt.length<1||b.receipt.length>200||/[\r\n]/.test(b.receipt))))return reply({error:'invalid_event'},400);
   const result=await rpc('defectrag_ca_effect',{p_event:b.event_id,p_lease:b.lease_token,p_effect:'notification',p_finish:b.operation==='finish',p_receipt:b.operation==='finish'?b.receipt:null});
   return reply(result);
  }
  // Four sequential operations require 85s worst-case plus safety margin.
  if(deadline-now()<90000)return reply({claimed:0,budgetLimited:true});
  const hook=endpoint(env.DEFECTRAG_CA_N8N_URL);
  if(!env.DEFECTRAG_CA_N8N_SECRET||env.DEFECTRAG_CA_N8N_SECRET.length<32)throw Error('configuration');
  await rpc('defectrag_ca_schedule',{});
  const event=await rpc('defectrag_ca_claim',{});
  if(!event)return reply({claimed:0});
  if(!UUID.test(event.event_id)||!UUID.test(event.lease_token)||!UUID.test(event.case_id)||!['created','updated','reminder','overdue'].includes(event.kind)||!Number.isInteger(event.version))throw Error('invalid_event');
  // Explicit projection; never forward any unexpected database fields.
  const payload=Object.fromEntries(['event_id','lease_token','case_id','kind','version','state','priority','due_at'].map(k=>[k,event[k]]));
  let success=false;
  try{const receipt=await call(hook,{method:'POST',headers:{'Content-Type':'application/json','X-DefectRAG-CA-Key':env.DEFECTRAG_CA_N8N_SECRET,'Idempotency-Key':event.event_id},body:JSON.stringify(payload)},40000);success=receipt?.event_id===event.event_id&&receipt.completed===true}catch{}
  // SQL independently checks the effect ledger; webhook success alone cannot
  // mark delivery sent. An ambiguous side effect is quarantined, never replayed.
  const finished=await rpc('defectrag_ca_finish',{p_event:event.event_id,p_lease:event.lease_token,p_success:success});
  return reply({claimed:1,workflowCompleted:success,acknowledged:finished===true});
 }catch{return reply({error:'automation_unavailable'},503)}
}
