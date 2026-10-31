// Guided practice on the real screens. While a lesson runs, every dashboard API
// call and Supabase client call is answered by this in-memory store instead of
// the server: no AI run, saving, sharing, publishing or email happens.
import {nextCaseStates} from './correctiveActions.mjs';
import {parseReview,reviewBody} from './workflow.mjs';

const ME='00000000-0000-4000-8000-00000000a001',ALEX='00000000-0000-4000-8000-00000000a002',SAM='00000000-0000-4000-8000-00000000a003';
export const practicePeople=Object.freeze([{user_id:ME,display_name:'You (practice)',role:'staff',revoked_at:null},
 {user_id:ALEX,display_name:'Alex (practice)',role:'staff',revoked_at:null},{user_id:SAM,display_name:'Sam (practice)',role:'staff',revoked_at:null}]);
// Saved public teaching measurement (showcase record 7dbb6f27…), not a new prediction.
export const PRACTICE_EXAMPLE=Object.freeze({category:'candle',verdict:'Anomalous',score:0.046729326248168945,threshold:0.04235455393791199,
 uncertainty_margin:0.0021177276968955996,inference_ms:34.73,model_id:'dinov3-normal-bank-candle-v1'});
const EXAMPLE=PRACTICE_EXAMPLE;
let active=null;
export const practiceActive=()=>active!==null;
const emit=(event,detail={})=>{try{active?.onEvent?.({type:'complete',event,...detail})}catch{/* Lesson display only. */}};
const uid=()=>crypto.randomUUID();
const now=()=>new Date().toISOString();
const ended=()=>{throw new Error('The practice lesson has ended. Normal work is available again.')};

export function startPracticeMode({assets={},metadata={},onEvent}={}){
 active={onEvent,assets,metadata,records:[],messages:{},reviews:{},alerts:[],shared:[],notes:[],cases:[],history:[],events:[],
  batches:{},publications:{},listeners:new Set()};
}
export function stopPracticeMode(){active=null}

function record(id,batch=''){
 return {...EXAMPLE,id,batch,created_at:now(),storage:'browser_session',workspace:'personal',
  image_url:active.assets.original||'',heatmap_url:active.assets.heatmap||'',report_url:'#practice-report-not-saved'};
}
const summary=r=>Object.fromEntries(['id','created_at','category','batch','verdict','score','threshold','inference_ms','model_id','image_url','heatmap_url'].map(k=>[k,r[k]]));
const json=options=>{try{return JSON.parse(options?.body||'{}')}catch{return {}}};
function stats(){
 const counts={};for(const r of active.records)counts[r.verdict]=(counts[r.verdict]||0)+1;
 const batches=[...new Set(active.records.map(r=>r.batch).filter(Boolean))].map(batch=>({batch}));
 return {total:active.records.length,counts,batches};
}

// Same shape as the dashboard api(): resolves with the response "data".
export async function practiceApi(path,options={}){
 if(!active)ended();
 const url=new URL(path,'https://practice.invalid'),p=url.pathname,method=(options.method||'GET').toUpperCase();
 const m=p.match(/^\/api\/inspections\/([^/]+)(?:\/([a-z-]+))?$/);
 if(p==='/api/health')return {status:'ok',mode:'cloud_session_workspace',encoder_configured:true,auth_workflow_enabled:true,personal_workspace_enabled:true,local_sync_enabled:false,practice:true};
 if(p==='/api/samples')return active.metadata.samples||[];
 if(p==='/api/evaluation')return active.metadata.evaluation||{categories:{}};
 if(p==='/api/benchmark/official')return active.metadata.official||null;
 if(p==='/api/stats')return stats();
 if(p==='/api/inspections')return active.records.map(summary);
 if(p==='/api/alerts')return active.alerts.map(a=>({...a}));
 if(p==='/api/archives')return [];
 if(p==='/api/workspace')return {workspace:'personal',role:'staff',practice:true};
 if(p==='/api/gallery')return {items:[],total:0,offset:0,enabled:true};
 if(p==='/api/batch-name')return {available:!active.records.some(r=>r.batch.trim().toLowerCase()===String(url.searchParams.get('name')||'').trim().toLowerCase())};
 if(p==='/api/inspect'&&method==='POST'){
  const form=options.body,category=form?.get?.('category'),batch=String(form?.get?.('batch')||'').trim();
  if(category!=='candle')throw new Error('In this lesson, choose Candle and a Candle sample photo. Practice shows a saved Candle example.');
  const r=record(uid().replaceAll('-',''),batch);active.records.unshift(r);active.messages[r.id]=[];
  active.alerts.unshift({id:uid(),inspection_id:r.id,kind:r.verdict,created_at:r.created_at,acknowledged:null});
  if(batch){active.batches[batch]=(active.batches[batch]||0)+1;if(active.batches[batch]>=2)emit('batch')}else emit('inspect');
  return {...r};
 }
 if(p==='/api/assistant'&&method==='POST'){
  const {inspection_id,question}=json(options);
  const answer={mode:'retrieval_only',answer:'Practice answer, prepared text and not a live AI answer. The difference score is above the review limit, so the photo looks unusual compared with normal Candle examples. Highlighted areas show where it differs; a Staff member must check the product before any decision. The score is not an accuracy or defect probability.',evidence:[],trace:['practice lesson','no AI call']};
  active.messages[inspection_id]=[...(active.messages[inspection_id]||[]),{role:'user',question},{role:'assistant',...answer}];
  emit('ask');return answer;
 }
 const alert=p.match(/^\/api\/alerts\/([^/]+)\/acknowledge$/);
 if(alert&&method==='POST'){const a=active.alerts.find(a=>a.id===alert[1]);if(a)a.acknowledged=now();emit('alert');return {acknowledged:true}}
 const gallery=p.match(/^\/api\/gallery\/([^/]+)\/withdraw$/);
 if(gallery){for(const k of Object.keys(active.publications))if(active.publications[k].id===gallery[1])active.publications[k]={...active.publications[k],visible:false};return {withdrawn:true}}
 if(m){
  const r=active.records.find(r=>r.id===m[1]);if(!r)throw Object.assign(new Error('Practice inspection not found.'),{status:404});
  const action=m[2];
  if(!action)return {...r};
  if(action==='messages')return [...(active.messages[r.id]||[])];
  if(action==='reviews')return [...(active.reviews[r.id]||[])];
  if(action==='review'&&method==='POST'){const v=json(options);reviewBody(v.status,v.decision,v.note||'');const saved={...v,id:uid(),created_at:now(),reviewer:'You (practice)'};active.reviews[r.id]=[...(active.reviews[r.id]||[]),saved];return saved}
  if(action==='save-personal'&&method==='POST')return {saved:true};
  if(action==='share'&&method==='POST'){
   if(active.shared.some(s=>s.id===r.id))return {alreadyShared:true};
   const {image_url,heatmap_url,report_url,...payload}=r;
   active.shared.unshift({id:r.id,owner_id:ME,payload,conversation:json(options).include_conversation?active.messages[r.id]:[],image_path:'practice/original',heatmap_path:'practice/heatmap',created_at:now(),archived_at:null});
   emit('share');return {alreadyShared:false};
  }
  if(action==='publication'){
   if(method==='POST'){if(json(options).consent!==true)throw new Error('Confirm that the copy may be public.');active.publications[r.id]={id:uid(),visible:true,practice:true};emit('gallery');return active.publications[r.id]}
   return {enabled:true,publication:active.publications[r.id]||null};
  }
 }
 if(p==='/api/history/archive'||p==='/api/history/restore')return {archived:0,restored:0};
 throw new Error('This action is not part of the practice lesson. Finish or skip the tutorial to use it normally.');
}
// request() callers expect a Response (spreadsheet download).
export async function practiceRequest(path,options){
 if(!active)ended();
 if(new URL(path,'https://practice.invalid').pathname==='/api/export.csv')
  return new Response('practice_note\nPractice data is not exported. Finish the tutorial to download real history.\n',{status:200,headers:{'Content-Type':'text/csv'}});
 return new Response(JSON.stringify({data:await practiceApi(path,options)}),{status:200,headers:{'Content-Type':'application/json'}});
}

// Minimal Supabase-shaped client for Team and Corrective Actions pages.
function tableRows(table){
 return ({shared_inspections:active.shared,staff_notes:active.notes,staff_members:practicePeople,corrective_actions:active.cases,
  corrective_action_history:active.history,corrective_action_events:active.events})[table]||[];
}
function query(table){
 const filters=[];let single=false,insert,limit=Infinity,order=null;
 const q={select(){return q},order(key,{ascending=true}={}){order=[key,ascending];return q},limit(n){limit=n;return q},
  is(k,v){filters.push(row=>(row[k]??null)===v);return q},not(k,_,v){filters.push(row=>(row[k]??null)!==v);return q},
  eq(k,v){filters.push(row=>row[k]===v);return q},in(k,v){filters.push(row=>v.includes(row[k]));return q},
  like(k,v){const prefix=String(v).replace(/%$/,'');filters.push(row=>String(row[k]).startsWith(prefix));return q},
  single(){single=true;return q},maybeSingle(){single='maybe';return q},insert(value){insert=value;return q},
  then(resolve,reject){return Promise.resolve().then(()=>{
   if(!active)ended();
   if(insert){
    if(table!=='staff_notes')throw new Error('Practice does not save this change.');
    const row={...insert,author_id:ME,id:uid(),created_at:now()};active.notes.push(row);
    const review=parseReview(row);if(review)emit('review',{status:review.status,decision:review.decision});
    return {data:row,error:null};
   }
   let rows=tableRows(table).filter(row=>filters.every(f=>f(row)));
   if(order)rows=[...rows].sort((a,b)=>String(a[order[0]]).localeCompare(String(b[order[0]]))*(order[1]?1:-1));
   rows=structuredClone(rows.slice(0,limit));
   if(single)return {data:rows[0]||null,error:single===true&&!rows.length?new Error('Not available in this practice workspace'):null};
   return {data:rows,error:null};
  }).then(resolve,reject)}};
 return q;
}
async function rpc(name,args={}){
 if(!active)ended();
 if(name==='defectrag_auth_status')return {data:{approved:true,authorized:true,aal2:true,mfa_required:true,role:'staff',revoked:false,registration_enabled:false,email_verified:true,request_status:'approved'},error:null};
 if(name==='defectrag_ca_staff')return {data:true,error:null};
 const fail=message=>({data:null,error:new Error(message)});
 if(name==='defectrag_create_corrective_action'){
  const note=active.notes.find(n=>n.id===args.p_review),review=note&&parseReview(note);
  if(!review||review.status!=='Reviewed'||review.decision!=='Reject'||note.inspection_id!==args.p_inspection)return fail('A case needs a saved review of Reviewed with “Reject: defect confirmed”.');
  if(args.p_confirmed!==true)return fail('Confirm the defect before creating the case.');
  if(active.cases.some(c=>c.review_id===args.p_review))return fail('This saved review already has a case.');
  const id=uid(),created=now(),c={id,inspection_id:args.p_inspection,review_id:args.p_review,owner_id:args.p_owner,supervisor_id:args.p_supervisor,confirmed_by:ME,
   priority:args.p_priority,description:args.p_description,due_at:args.p_due,state:'Open',version:1,created_at:created,resolved_at:null};
  active.cases.unshift(c);active.history.push({id:uid(),case_id:id,version:1,actor_id:ME,state:'Open',note:'Human-confirmed defect; case created',created_at:created,snapshot:{owner_id:c.owner_id,supervisor_id:c.supervisor_id,due_at:c.due_at}});
  active.events.push({id:uid(),case_id:id,version:1,kind:'created',status:'suppressed',attempts:0,last_error:null,created_at:created});
  emit('case');return {data:id,error:null};
 }
 if(name==='defectrag_update_corrective_action'){
  const c=active.cases.find(c=>c.id===args.p_id);if(!c)return fail('Practice case not found.');
  if(c.owner_id!==ME&&c.supervisor_id!==ME)return fail('Only the person responsible, the supervisor or a Developer can change this case. In this lesson, choose You (practice) as person responsible or supervisor.');
  if(c.version!==args.p_version)return fail('The case changed. Load the latest case before saving.');
  if(!nextCaseStates(c.state).includes(args.p_state)||String(args.p_note||'').trim().length<3)return fail('Choose an allowed next status and describe what changed.');
  Object.assign(c,{state:args.p_state,version:c.version+1,owner_id:args.p_owner||c.owner_id,supervisor_id:args.p_supervisor||c.supervisor_id,due_at:args.p_due||c.due_at,
   resolved_at:['Resolved','Closed'].includes(args.p_state)?c.resolved_at||now():null});
  active.history.push({id:uid(),case_id:c.id,version:c.version,actor_id:ME,state:c.state,note:String(args.p_note).trim(),created_at:now(),snapshot:{owner_id:c.owner_id,supervisor_id:c.supervisor_id,due_at:c.due_at}});
  emit('lifecycle',{state:c.state});return {data:c.version,error:null};
 }
 return fail('This action is not part of the practice lesson.');
}
export function practiceClient(){
 if(!active)ended();
 const user={id:ME,email:'you@practice.invalid'};
 return {auth:{getUser:async()=>({data:{user},error:null}),getSession:async()=>({data:{session:{user,access_token:'PRACTICE_NOT_A_TOKEN'}},error:null}),
   onAuthStateChange(){return {data:{subscription:{unsubscribe(){}}}}},signOut:async()=>({error:null}),
   mfa:{listFactors:async()=>({data:{totp:[{id:'practice-factor',friendly_name:'Practice authenticator',status:'verified'}],all:[]},error:null})}},
  from:query,rpc,
  storage:{from:()=>({download:async path=>{const source=path.endsWith('heatmap')?active?.assets.heatmap:active?.assets.original;
   try{return {data:await (await fetch(source)).blob(),error:null}}catch(error){return {data:null,error}}},
   createSignedUrl:async path=>({data:{signedUrl:path.endsWith('heatmap')?active?.assets.heatmap:active?.assets.original},error:null})})}};
}
export async function practiceStaff(){const client=practiceClient();return {client,user:{id:ME,email:'you@practice.invalid'},staff:practicePeople[0]}}
