import {authStatus} from './authSecurity.mjs';
import {startPolling} from './workspace.mjs';

export const teamInspectionGuidance='New inspections are created in Personal Workspace. Switch to Personal to run an inspection, then share the result with your team.';

// Presence only comes from the SDK; authorization comes from the native RPC.
// A failed/denied signed-in check must never become anonymous Demo access.
export async function loadInspectionAccess(client){
 const {data,error}=await client.auth.getSession();if(error)throw error;
 if(!data.session)return {state:'guest'};
 const p=await authStatus(client);
 if(p.revoked)return {state:'revoked'};
 if(!p.approved)return {state:p.request_status==='rejected'?'rejected':'pending'};
 if(typeof p.mfa_required!=='boolean')return {state:'unavailable'};
 if(p.mfa_required&&!p.aal2)return {state:'mfa'};
 return {state:p.authorized&&['staff','developer'].includes(p.role)?'authorized':'denied'};
}

export function watchInspectionAccess(load,onChange,options={}){
 const target=options.target||window;let generation=0,stopped=false;
 async function refresh(){
  const issued=++generation;
  try{const value=await load();if(!stopped&&issued===generation)onChange(value)}
  catch{if(!stopped&&issued===generation)onChange({state:'unavailable'})}
 }
 const poll=startPolling(refresh,{...options,target,onState:state=>{
  if(state.state==='offline'&&!stopped){generation++;onChange({state:'unavailable'})}
 }});
 const changed=()=>{generation++;onChange({state:'checking'});poll.refresh()};
 target.addEventListener('defectrag-auth-change',changed);
 return ()=>{stopped=true;generation++;poll.stop();target.removeEventListener('defectrag-auth-change',changed)};
}

export function inspectionReadiness({health,workspace,access={state:'checking'},files=[],categoryValid=true,batch='',multiple=false,retry=false,busy=false,ragBusy=false,recordLoading=false,offline=false,connectionFailed=false}){
 const teamRestricted=Boolean(health?.personal_workspace_enabled&&workspace==='team');
 const blocked=(code,reason)=>({disabled:true,code,reason,teamRestricted});
 if(busy)return blocked('processing','An inspection is processing. Wait for it to finish before starting another.');
 if(ragBusy)return blocked('evidence_processing','The Evidence Assistant is processing. Wait for it to finish before starting an inspection.');
 if(recordLoading)return blocked('record_loading','A saved inspection is loading. Wait for it to finish before starting another.');
 if(teamRestricted)return blocked('team',teamInspectionGuidance);
 if(!health)return blocked('connecting','Connecting to the inspection service. Wait for the connection or use Retry refresh.');
 if(connectionFailed||health.status!=='ok'||health.encoder_configured===false)return blocked('service','The inspection service is temporarily unavailable. Reconnect or use Retry refresh.');
 if(offline&&health.mode==='cloud_session_workspace')return blocked('offline','The cloud inspection service is offline. Reconnect before running an inspection.');
 if(health.mode==='cloud_session_workspace'&&health.auth_workflow_enabled){
  const reasons={checking:'Checking account permissions before inspection.',pending:'Staff access is pending approval. Open Staff workspace to view the request. Sign out to use public Demo Mode.',
   rejected:'Staff access was rejected. Protected inspections are unavailable. Sign out to use public Demo Mode.',revoked:'Staff access was revoked. Protected inspections are unavailable.',
   mfa:'Verify the authenticator in Staff workspace before running an inspection.',denied:'This account does not have permission to run protected inspections.',
   unavailable:'Account authorization is temporarily unavailable. Reconnect or open Staff workspace and retry.'};
  if(!['guest','authorized'].includes(access.state))return blocked(access.state,reasons[access.state]||reasons.denied);
 }
 if(!categoryValid)return blocked('category','Choose a supported product category.');
 if(!retry){
  if(!files.length)return blocked('images','Choose an image before running an inspection.');
  if(!multiple&&files.length!==1)return blocked('single','Choose one image, or use Batch monitoring for multiple images.');
  if(files.length>20)return blocked('count','Choose up to 20 images per batch.');
  if(files.some(f=>f.size<=0||f.size>10*1024*1024))return blocked('size','Use non-empty images up to 10 MB each.');
  if(files.some(f=>f.type?!['image/jpeg','image/png','image/webp'].includes(f.type):! /\.(jpe?g|png|webp)$/i.test(f.name)))return blocked('format','Choose JPEG, PNG or WebP images.');
  if(files.reduce((sum,f)=>sum+f.size,0)>20*1024*1024)return blocked('total','Keep the total batch upload within 20 MB.');
  if(multiple&&!batch.trim())return blocked('batch','Add a batch label before inspecting this batch.');
  if(batch.length>80)return blocked('batch_length','Keep the batch label within 80 characters.');
 }
 return {disabled:false,code:'ready',reason:'',teamRestricted};
}
