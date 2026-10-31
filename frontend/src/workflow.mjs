// A context is invalidated before a different inspection or identity is displayed.
export function createRequestScope(){
 let generation=0;
 return {invalidate(){generation++},capture(){const issued=generation;return()=>issued===generation}};
}

export const REVIEW_PREFIX='DEFECTRAG_REVIEW_V1:';
export const reviewStatuses=['Needs review','In review','Reviewed'];
export const reviewDecisions=['Pending','Hold','Accept','Reject'];
// Display wording only. Saved review bodies keep the original decision values.
const decisionWording={Pending:'Pending',Hold:'Hold: needs more checks',Accept:'Accept: no defect',Reject:'Reject: defect confirmed'};
export const decisionLabel=decision=>decisionWording[decision]||decision;
export function reviewBody(status,decision,note=''){
 if(!reviewStatuses.includes(status)||!reviewDecisions.includes(decision)||
    (status==='Reviewed')===(decision==='Pending')||note.length>1000)
   throw new Error('Choose a review status and a compatible decision.');
 return REVIEW_PREFIX+JSON.stringify({status,decision,note:note.trim()});
}
export function parseReview(row,directory={}){
 if(!row.body?.startsWith(REVIEW_PREFIX))return null;
 try{
  const value=JSON.parse(row.body.slice(REVIEW_PREFIX.length));
  reviewBody(value.status,value.decision,value.note||'');
  return {...value,reviewer:directory[row.author_id]||'Staff member',reviewer_id:row.author_id,created_at:row.created_at};
 }catch{return null}
}

export const isQuotaError=message=>/exceeded.*(?:ZeroGPU|GPU).*(?:limit|quota)|(?:ZeroGPU|GPU).*(?:quota|limit).*exceed/i.test(message);
export function recordSummary(record){
 return Object.fromEntries(['id','created_at','category','batch','verdict','score','threshold','inference_ms','model_id','storage'].filter(k=>record[k]!==undefined).map(k=>[k,record[k]]));
}
export function newBatch(files,category,batch){
 return {version:1,id:crypto.randomUUID(),category,batch,updated_at:new Date().toISOString(),
  items:files.map(file=>({id:crypto.randomUUID().replaceAll('-',''),filename:file.name,file,status:'pending'}))};
}
export function batchView(job){
 return {batch:job.batch,records:job.items.filter(i=>i.status==='completed').map(i=>i.record),
  errors:job.items.filter(i=>['failed','pending','running'].includes(i.status)).map(i=>({filename:i.filename,status:i.status,message:i.message||(i.status==='running'?'Inspection in progress; no result has been saved yet.':'Pending inspection; no prediction has been made.')}))};
}
// Checkpoint before and after each item. Completed items are never resubmitted.
export async function continueBatch(job,inspect,checkpoint,isCurrent=()=>true){
 let current={...job,items:job.items.map(item=>({...item}))};
 for(let index=0;index<current.items.length;index++){
  const item=current.items[index];
  if(item.status==='completed')continue;
  if(!isCurrent())break;
  item.status='running';delete item.message;
  await checkpoint(structuredClone(current));
  try{
   item.record=recordSummary(await inspect(item.file,current.category,current.batch,item.id));
   item.status='completed';delete item.file;
  }catch(error){
   item.status='failed';item.message=String(error?.message||'Inspection failed');
   const quota=isQuotaError(item.message);
   if(quota){
    item.message='GPU allowance is currently unavailable. Open the Hugging Face Space while signed in, or retry after quota resets. Supabase staff login uses a separate account.';
    for(const pending of current.items.slice(index+1))if(pending.status!=='completed'){
     pending.status='pending';pending.message='Not submitted because GPU quota is unavailable. Retry when quota returns.';
    }
    await checkpoint(structuredClone(current));break;
   }
  }
  current.updated_at=new Date().toISOString();
  await checkpoint(structuredClone(current));
 }
 return current;
}
