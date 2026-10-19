import React,{useState} from 'react';
import {shareInspection,workspaceChanged} from './cloud.js';

export default function WorkspaceShare({record,messages,url,api,enabled,onChanged,onNotice}){
 const [include,setInclude]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const team=record.workspace==='team';
 async function save(personalOnly=false){
  setBusy(true);setError('');
  try{
   const response=enabled?await api(`/api/inspections/${record.id}/${personalOnly?'save-personal':'share'}`,{
    method:'POST',headers:{'Content-Type':'application/json'},body:personalOnly?undefined:JSON.stringify({include_conversation:include})
   }):await shareInspection(record,messages,url);
   workspaceChanged();
   onNotice(personalOnly?'Saved privately to this account.':response.alreadyShared?'This inspection is already in Team workspace.':'Explicit team copy saved. Personal notes and later conversations remain private.');
   await onChanged();
  }catch(err){setError(err.message+' Sign in with an approved account if required.')}
  finally{setBusy(false)}
 }
 return <div><p className="caption">{record.storage==='supabase_personal'?'Storage: private account · Supabase':record.storage==='supabase'?'Storage: shared team · Supabase':record.storage==='browser_session'?'Storage: temporary browser workspace':'Storage: local device'}</p>
  <div className="button-row">{enabled&&record.storage==='browser_session'&&<button className="secondary" disabled={busy} onClick={()=>save(true)}>Save to Personal</button>}
   <button className="secondary" disabled={busy||(enabled&&team)} onClick={()=>save()}>{busy?'Saving…':enabled&&team?'Shared team record':'Share with staff'}</button>
  </div>
  {enabled&&!team&&<label className="caption"><input type="checkbox" style={{width:16,height:16,minHeight:16,padding:0,marginRight:6,verticalAlign:'middle'}} checked={include} disabled={busy} onChange={e=>setInclude(e.target.checked)}/> Include saved conversation in the team copy</label>}
  {error&&<p className="error" role="alert">{error}</p>}
 </div>;
}
