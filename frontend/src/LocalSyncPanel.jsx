import {friendlyError,resultLabel} from './userLanguage.mjs';
import React,{useState} from 'react';
import {synchronizationText} from './localSync.mjs';

export default function LocalSyncPanel({status,onRetry,onResolve,onBackup,onListImports,onImport,canImport,refreshing}){
 const [selected,setSelected]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[imports,setImports]=useState(null),[checked,setChecked]=useState([]);
 async function listImports(){setBusy(true);setError('');try{setImports(await onListImports())}catch{setError('Saved work on this computer could not be listed. Check the sign-in in Staff workspace.')}finally{setBusy(false)}}
 async function importSelected(){setBusy(true);setError('');try{await onImport(checked);setImports(null);setChecked([])}catch{setError('The copy could not be confirmed. The original work is still saved on this computer.')}finally{setBusy(false)}}
 async function resolve(choice){
  setBusy(true);setError('');
  try{await onResolve(selected,choice);setSelected(null)}catch{setError('The chosen copy could not be saved. Both copies have been kept.')}finally{setBusy(false)}
 }
 return <section className="note" role="status"><div><strong>Keep private work up to date across devices</strong>
  <p>{synchronizationText(status)}</p>
  <button className="text-button" disabled={refreshing||busy} onClick={onRetry}>{refreshing?'Checking saved changes…':'Check saved changes'}</button>
  {canImport&&<button className="text-button" disabled={busy} onClick={listImports}>Copy older work into this account</button>}
  {status?.last_backup&&<button className="text-button" disabled={busy} onClick={()=>onBackup(status.last_backup)}>Download backup copy</button>}
  {imports&&<div><p>Choose up to 10 inspections to copy into this private account. This list shows the latest 500 saved only on this computer. Originals stay here. Only select work that belongs in this account; the original inspector cannot be checked. Nothing is shared with the team.</p>
   {imports.map(row=><label className="caption" key={row.id}><input type="checkbox" style={{width:16,height:16,minHeight:16,padding:0,marginRight:6,verticalAlign:'middle'}} checked={checked.includes(row.id)} disabled={busy||(!checked.includes(row.id)&&checked.length>=10)} onChange={e=>setChecked(e.target.checked?[...checked,row.id]:checked.filter(id=>id!==row.id))}/>{row.category} · {row.id.slice(0,8)} · {new Date(row.created_at).toLocaleString()}</label>)}
   <button className="secondary" disabled={busy||!checked.length} onClick={importSelected}>Copy selected inspections</button>{' '}
   <button className="text-button" disabled={busy} onClick={()=>setImports(null)}>Cancel</button>
  </div>}
  {status?.conflicts?.map(row=><button className="text-button" key={row.inspection_id} disabled={busy} onClick={()=>setSelected(row.inspection_id)}>Compare saved changes · {row.inspection_id.slice(0,8)}</button>)}
  {selected&&<div><p>This inspection was changed in two places. Use the online copy to replace the copy shown on this computer; the previous changes are kept in a backup. Or try saving the computer’s changes again. If they still overlap, both copies will be kept for another review.</p>
   <button className="secondary" disabled={busy} onClick={()=>resolve('cloud')}>Use online copy</button>{' '}
   <button className="secondary" disabled={busy} onClick={()=>resolve('retry_local')}>Try saving this computer’s changes</button>{' '}
   <button className="text-button" disabled={busy} onClick={()=>setSelected(null)}>Cancel</button>
  </div>}
  {error&&<p role="alert">{friendlyError(error)}</p>}
 </div></section>;
}
