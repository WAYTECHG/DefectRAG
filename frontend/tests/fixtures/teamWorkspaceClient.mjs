// In-memory SOFTWARE FIXTURE. No Supabase URL, key, network or real records.
import {reviewBody} from '../../src/workflow.mjs';
export function teamFixture(role='developer'){
 const id='a'.repeat(32),owner='11111111-1111-4111-8111-111111111111',other='22222222-2222-4222-8222-222222222222';
 let actor={id:owner,email:'fixture@example.invalid'},mode=role,seq=0;
 const f={requests:[],role:()=>mode,actor:()=>actor,
  inspection:{id,owner_id:owner,created_at:'2026-10-26T08:00:00Z',image_path:'fixture/image.jpg',heatmap_path:'fixture/heatmap.jpg',archived_at:null,
   payload:{id,category:'pcb1',verdict:'Anomalous',score:.2,threshold:.1,uncertainty_margin:.005,batch:'SYNTHETIC NAV QA',model_id:'software-fixture',inference_ms:1,created_at:'2026-10-26T08:00:00Z'},conversation:[]},
  notes:[],cases:[],history:[],events:[]};
 const people=()=>[{user_id:owner,display_name:'QA owner',role:mode==='developer'?'developer':'staff',revoked_at:null},
  {user_id:other,display_name:'QA supervisor',role:'staff',revoked_at:null},
  {user_id:'33333333-3333-4333-8333-333333333333',display_name:'QA unassigned',role:'staff',revoked_at:null}];
 const allowed=()=>['developer','owner','supervisor','unassigned'].includes(mode);
 const aal2=()=>mode!=='mfa';
 const posture=()=>({approved:!['pending','guest','revoked'].includes(mode),authorized:allowed(),aal2:aal2(),mfa_required:true,registration_enabled:false,
  role:mode==='developer'?'developer':'staff',revoked:mode==='revoked',request_status:mode==='pending'?'pending':'approved'});
 const listeners=new Set();
 const session=()=>mode==='guest'?null:{user:actor,access_token:'SOFTWARE_FIXTURE_NOT_A_JWT'};
 function query(table){
  const filters=[];let single=false,insert;
  const q={select(){return q},order(){return q},limit(){return q},is(k,v){filters.push([k,v]);return q},not(k,_,v){filters.push([k,'NOT',v]);return q},
   eq(k,v){filters.push([k,v]);return q},single(){single=true;return q},maybeSingle(){single=true;return q},insert(value){insert=value;return q},
   then(resolve,reject){return Promise.resolve().then(()=>{
    f.requests.push({table,insert:insert?structuredClone(insert):undefined});
    if(!allowed())return {data:null,error:new Error('Approved Staff and TOTP MFA required')};
    if(insert){if(table!=='staff_notes')throw Error('Fixture does not support this write');const row={...insert,id:'note-'+(++seq),created_at:new Date(Date.now()+seq).toISOString()};f.notes.push(row);return {data:row,error:null}}
    let rows=({staff_members:people(),shared_inspections:[f.inspection],staff_notes:f.notes,corrective_actions:f.cases,corrective_action_history:f.history,corrective_action_events:f.events})[table]||[];
    rows=rows.filter(row=>filters.every(([key,v,n])=>v==='NOT'?row[key]!==n:(row[key]??null)===v));
    return {data:single?rows[0]||null:structuredClone(rows),error:single&&!rows.length?new Error('Not available in this workspace'):null};
   }).then(resolve,reject)}};return q;
 }
 f.client={auth:{getUser:async()=>({data:{user:session()?.user||null}}),getSession:async()=>({data:{session:session()},error:null}),
  onAuthStateChange(fn){listeners.add(fn);return {data:{subscription:{unsubscribe(){listeners.delete(fn)}}}}},
  mfa:{listFactors:async()=>({data:{totp:[{id:'fixture-factor',friendly_name:'QA authenticator',status:'verified'}],all:[]},error:null})}},
  from:query,storage:{from:()=>({download:async()=>({data:new Blob(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="180"><rect width="480" height="180" fill="#eeecff"/><text x="30" y="95" font-size="22" fill="#30365a">Synthetic navigation test image</text></svg>'],{type:'image/svg+xml'}),error:null}),createSignedUrl:async()=>({data:{signedUrl:'/fixture-image.svg'}})})},
  async rpc(name,payload){
   f.requests.push({rpc:name,payload:payload?structuredClone(payload):undefined});
   if(name==='defectrag_auth_status')return {data:posture(),error:null};
   if(name==='defectrag_ca_staff')return {data:allowed()&&aal2(),error:null};
   if(!allowed()||!aal2())return {data:null,error:new Error('Approved Staff and TOTP MFA required')};
   if(name==='defectrag_access_directory'||name==='defectrag_notification_status')return {data:[],error:null};
   if(name==='defectrag_workspace_stats')return {data:{total:1},error:null};
   if(name==='defectrag_create_corrective_action'){
    const reviewed=f.notes.at(-1)?.body===reviewBody('Reviewed','Reject')||f.notes.at(-1)?.body?.includes('"decision":"Reject"');
    if(!payload.p_confirmed||!reviewed)return {error:new Error('Explicit confirmation and latest reviewed Reject required')};
    const row={id:'44444444-4444-4444-8444-444444444444',inspection_id:id,owner_id:payload.p_owner,supervisor_id:payload.p_supervisor,confirmed_by:actor.id,
     description:payload.p_description,priority:payload.p_priority,due_at:payload.p_due,state:'Open',version:1,created_at:new Date().toISOString()};
    f.cases.push(row);f.history.push({id:'history-1',case_id:row.id,version:1,state:'Open',actor_id:actor.id,created_at:row.created_at,note:'Synthetic case created'});return {data:row.id,error:null};
   }
   if(name==='defectrag_update_corrective_action'){
    const c=f.cases.find(c=>c.id===payload.p_id);
    if(!c||!['developer'].includes(mode)&&![c.owner_id,c.supervisor_id].includes(actor.id))return {error:new Error('Assigned editor required')};
    if(c.version!==payload.p_version)return {error:new Error('Case changed; refresh before updating')};
    c.state=payload.p_state;c.version++;f.history.push({id:'history-'+c.version,case_id:c.id,version:c.version,state:c.state,actor_id:actor.id,created_at:new Date().toISOString(),note:payload.p_note});return {data:c.version,error:null};
   }
   return {data:[],error:null};
  }};
 f.currentStaff=async()=>{if(!allowed())throw Error('Approved Staff and TOTP MFA required');return {client:f.client,user:actor,staff:people().find(p=>p.user_id===actor.id)}};
 f.setRole=next=>{mode=next;actor={id:next==='unassigned'?'33333333-3333-4333-8333-333333333333':next==='supervisor'?other:owner,email:'fixture@example.invalid'};for(const fn of listeners)fn('SIGNED_IN',session())};
 return f;
}
