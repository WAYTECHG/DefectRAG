// INACTIVE QA ONLY. Outbound local sender pulls one approved event; no scheduler.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const PROJECT='https://zrzqpbcomlorfzszolrs.supabase.co';
const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
function matches(header,key){
 if(typeof key!=='string'||key.length<32||key.length>256||/[^\x21-\x7e]/.test(key)||typeof header!=='string'||header.length!==key.length+7)return false;
 const expected='Bearer '+key;let diff=0;for(let i=0;i<expected.length;i++)diff|=header.charCodeAt(i)^expected.charCodeAt(i);return diff===0;
}
function exactKeys(b,keys){return b&&typeof b==='object'&&!Array.isArray(b)&&Object.keys(b).sort().join('|')===[...keys].sort().join('|');}
async function readBody(request){
 const reader=request.body?.getReader();if(!reader)throw Error('body');let timer;
 const chunks=[];let size=0;
 try{return await Promise.race([(async()=>{
  for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>2048){await reader.cancel();throw Error('body')}chunks.push(value)}
  const data=new Uint8Array(size);let offset=0;for(const c of chunks){data.set(c,offset);offset+=c.length}
  return JSON.parse(new TextDecoder().decode(data));
 })(),new Promise((_,reject)=>{timer=setTimeout(()=>{reader.cancel().catch(()=>{});reject(Error('body'))},2000)})]);}
 finally{clearTimeout(timer);reader.releaseLock();}
}
export async function handleCAQA(request,{env={},fetcher=fetch}={}){
 if(request.method!=='POST')return reply({error:'method_not_allowed'},405);
 if(env.DEFECTRAG_CA_QA_ENABLED!=='1')return reply({error:'qa_disabled'},503);
 const operation=request.headers.get('X-DefectRAG-Operation');
 if(!['claim','effect','finalize'].includes(operation))return reply({error:'invalid_operation'},400);
 const workerKey=env.DEFECTRAG_CA_QA_WORKER_SECRET,callbackKey=env.DEFECTRAG_CA_QA_CALLBACK_SECRET;
 if(!matches('Bearer '+workerKey,workerKey)||!matches('Bearer '+callbackKey,callbackKey)||workerKey===callbackKey)return reply({error:'qa_configuration'},503);
 const key=operation==='effect'?env.DEFECTRAG_CA_QA_CALLBACK_SECRET:env.DEFECTRAG_CA_QA_WORKER_SECRET;
 if(!matches(request.headers.get('Authorization'),key))return reply({error:'unauthorized'},401);
 if(!UUID.test(env.DEFECTRAG_CA_QA_EVENT_ID||'')||env.SUPABASE_URL?.replace(/\/$/,'')!==PROJECT||!env.SUPABASE_SERVICE_ROLE_KEY)return reply({error:'qa_configuration'},503);
 let b;try{b=await readBody(request)}catch{return reply({error:'invalid_event'},400)}
 if(b?.event_id!==env.DEFECTRAG_CA_QA_EVENT_ID)return reply({error:'wrong_qa_event'},403);
 let name,params;
 if(operation==='claim'){
  if(!exactKeys(b,['event_id']))return reply({error:'invalid_event'},400);
  name='defectrag_ca_qa_claim';params={p_event:b.event_id};
 }else{
  if(!UUID.test(b.lease_token||''))return reply({error:'invalid_event'},400);
  if(operation==='effect'){
   if(!['begin','finish'].includes(b.operation)||!exactKeys(b,b.operation==='begin'?['event_id','lease_token','operation']:['event_id','lease_token','operation','receipt'])||
      b.operation==='finish'&&(typeof b.receipt!=='string'||b.receipt.length<1||b.receipt.length>200||/[\r\n]/.test(b.receipt)))return reply({error:'invalid_event'},400);
   name='defectrag_ca_qa_effect';params={p_event:b.event_id,p_lease:b.lease_token,p_finish:b.operation==='finish',p_receipt:b.operation==='finish'?b.receipt:null};
  }else{
   if(!exactKeys(b,['event_id','lease_token','completed'])||typeof b.completed!=='boolean')return reply({error:'invalid_event'},400);
   name='defectrag_ca_qa_finish';params={p_event:b.event_id,p_lease:b.lease_token,p_success:b.completed};
  }
 }
 const controller=new AbortController();let timer;
 try{
  const result=await Promise.race([(async()=>{
   const r=await fetcher(PROJECT+'/rest/v1/rpc/'+name,{method:'POST',redirect:'error',signal:controller.signal,
    headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:'Bearer '+env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'},body:JSON.stringify(params)});
   if(!r.ok)throw Error('rpc');return r.json();
  })(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('timeout'))},10000)})]);
  if(operation==='claim'){
   if(result?.event_id!==b.event_id||!UUID.test(result.lease_token||'')||!UUID.test(result.case_id||'')||
      !['created','updated'].includes(result.kind)||!Number.isInteger(result.version)||result.version<1)throw Error('result');
   return reply(Object.fromEntries(['event_id','lease_token','case_id','kind','version'].map(k=>[k,result[k]])));
  }
  if(operation==='finalize'){if(typeof result!=='boolean')throw Error('result');return reply({acknowledged:result});}
  if(typeof result?.done!=='boolean')throw Error('result');
  if(result.execute===true){
   if(result.done!==false||!UUID.test(result.case_id||'')||!['created','updated'].includes(result.kind)||
      !['Open','Assigned','In Progress'].includes(result.state)||!['Low','Normal','High','Critical'].includes(result.priority)||typeof result.due_at!=='string'||!Number.isFinite(Date.parse(result.due_at)))throw Error('result');
   return reply({execute:true,done:false,recipient_email:'supervisor@example.invalid',
    ...Object.fromEntries(['case_id','kind','state','priority','due_at'].map(k=>[k,result[k]]))});
  }
  return reply({done:result.done,...(result.execute===false?{execute:false}:{}),...(result.manual_review===true?{manual_review:true}:{})});
 }catch{return reply({error:'qa_request_denied_or_unavailable'},503)}
 finally{clearTimeout(timer)}
}
