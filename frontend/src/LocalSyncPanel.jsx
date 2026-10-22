import React,{useState} from 'react';
import {synchronizationText} from './localSync.mjs';

export default function LocalSyncPanel({status,onRetry,onResolve,onBackup,onListImports,onImport,canImport,refreshing}){
 const [selected,setSelected]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[imports,setImports]=useState(null),[checked,setChecked]=useState([]);
 async function listImports(){setBusy(true);setError('');try{setImports(await onListImports())}catch{setError('Local-only history could not be listed. Verify account access.')}finally{setBusy(false)}}
 async function importSelected(){setBusy(true);setError('');try{await onImport(checked);setImports(null);setChecked([])}catch{setError('Import could not be confirmed. Previously saved local history is retained.')}finally{setBusy(false)}}
 async function resolve(choice){
  setBusy(true);setError('');
  try{await onResolve(selected,choice);setSelected(null)}catch{setError('Resolution could not be confirmed. Both copies are retained.')}finally{setBusy(false)}
 }
 return <section className="note" role="status"><div><strong>Private local and cloud synchronization</strong>
  <p>{synchronizationText(status)}</p>
  <button className="text-button" disabled={refreshing||busy} onClick={onRetry}>{refreshing?'Synchronizing…':'Check synchronization'}</button>
  {canImport&&<button className="text-button" disabled={busy} onClick={listImports}>Import existing local history</button>}
  {status?.last_backup&&<button className="text-button" disabled={busy} onClick={()=>onBackup(status.last_backup)}>Download recovery backup</button>}
  {imports&&<div><p>Select up to 10 of the latest 500 local-only inspections to copy privately into this account. Existing local files stay unchanged. Original operator identity is unverified; no team sharing occurs.</p>
   {imports.map(row=><label className="caption" key={row.id}><input type="checkbox" style={{width:16,height:16,minHeight:16,padding:0,marginRight:6,verticalAlign:'middle'}} checked={checked.includes(row.id)} disabled={busy||(!checked.includes(row.id)&&checked.length>=10)} onChange={e=>setChecked(e.target.checked?[...checked,row.id]:checked.filter(id=>id!==row.id))}/>{row.category} · {row.id.slice(0,8)} · {new Date(row.created_at).toLocaleString()}</label>)}
   <button className="secondary" disabled={busy||!checked.length} onClick={importSelected}>Confirm private import</button>{' '}
   <button className="text-button" disabled={busy} onClick={()=>setImports(null)}>Cancel import</button>
  </div>}
  {status?.conflicts?.map(row=><button className="text-button" key={row.inspection_id} disabled={busy} onClick={()=>setSelected(row.inspection_id)}>Review conflict · {row.inspection_id.slice(0,8)}</button>)}
  {selected&&<div><p>Choosing cloud replaces the active local view; the previous local changes remain in a recovery backup. Retrying local changes applies those operations against the current cloud revision and may still conflict.</p>
   <button className="secondary" disabled={busy} onClick={()=>resolve('cloud')}>Use cloud version</button>{' '}
   <button className="secondary" disabled={busy} onClick={()=>resolve('retry_local')}>Retry local changes</button>{' '}
   <button className="text-button" disabled={busy} onClick={()=>setSelected(null)}>Cancel</button>
  </div>}
  {error&&<p role="alert">{error}</p>}
 </div></section>;
}
