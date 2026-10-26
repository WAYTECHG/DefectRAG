import {friendlyError,resultLabel} from './userLanguage.mjs';
import React,{useEffect,useRef,useState} from 'react';
import {shareInspection,workspaceChanged} from './cloud.js';
import {createOperationGuard} from './workspace.mjs';
import {personalSaveAccess,storageDescription} from './inspectionUX.mjs';

export default function WorkspaceShare({record,messages,url,api,enabled,local=false,access={state:'checking'},onChanged,onNotice}){
 const [include,setInclude]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const operations=useRef(null);
 if(!operations.current)operations.current=createOperationGuard();
 useEffect(()=>()=>operations.current.invalidate(),[record.id,record.workspace]);
 const team=record.workspace==='team';
 const permission=personalSaveAccess(access.state);
 async function save(personalOnly=false){
  if(enabled&&!permission.allowed){setError(permission.reason);return}
  const isCurrent=operations.current.begin();
  setBusy(true);setError('');
  try{
   const response=enabled?await api(`/api/inspections/${record.id}/${personalOnly?'save-personal':'share'}`,{
    method:'POST',headers:{'Content-Type':'application/json'},body:personalOnly?undefined:JSON.stringify({include_conversation:include})
   }):await shareInspection(record,messages,url);
   workspaceChanged();
   if(!isCurrent())return;
   onNotice(personalOnly?'Saved in Personal Workspace. Only this account can see it.':response.alreadyShared?'This inspection is already in Team workspace.':'A separate copy has been shared with the team. Personal notes and later conversations stay private.');
   await onChanged();
  }catch(err){if(isCurrent())setError(err.message+' Sign in with an approved account if required.')}
  finally{if(isCurrent())setBusy(false)}
 }
 return <div><p className="caption">{storageDescription(record.storage,local)}</p>
  {enabled&&!permission.allowed&&<p className="caption" id="personal-save-reason">{permission.reason} <a href="#team">Open Staff workspace</a></p>}
  <div className="button-row">{enabled&&record.storage==='browser_session'&&<button className="secondary" aria-describedby={!permission.allowed?'personal-save-reason':undefined} disabled={busy||!permission.allowed} onClick={()=>save(true)}>Save to Personal</button>}
   <button className="secondary" disabled={busy||(enabled&&(team||!permission.allowed))} onClick={()=>save()}>{busy?'Saving…':enabled&&team?'Already shared with team':'Share with team'}</button>
  </div>
  {enabled&&!team&&permission.allowed&&<label className="caption"><input type="checkbox" style={{width:16,height:16,minHeight:16,padding:0,marginRight:6,verticalAlign:'middle'}} checked={include} disabled={busy} onChange={e=>setInclude(e.target.checked)}/> Also share the saved assistant conversation</label>}
  {error&&<p className="error" role="alert">{friendlyError(error)}</p>}
 </div>;
}
