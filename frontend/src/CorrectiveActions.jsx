import {friendlyError,deliveryLabel,eventLabel} from './userLanguage.mjs';
import React,{useEffect,useRef,useState} from 'react';
import {cloudClient,workspaceChanged} from './cloud.js';
import {caseCanEdit,caseCreationGate,caseDraftError,caseMetrics,caseRpc,latestDefectReview,nextCaseStates} from './correctiveActions.mjs';
import {startPolling} from './workspace.mjs';
import {focusInspectionDetails} from './teamNavigation.mjs';

export default function CorrectiveActions({user,inspection,notes=[],inspections=[],inspectionLoading=false,onSelectInspection,onEvidence}){
 const generation=useRef(0),saving=useRef(false),previousInspection=useRef(inspection?.id);
 const caseDetails=useRef(null),casePanel=useRef(null);
 const [access,setAccess]=useState('checking');
 const [cases,setCases]=useState([]),[people,setPeople]=useState([]),[selected,setSelected]=useState('');
 const [history,setHistory]=useState([]),[events,setEvents]=useState([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [description,setDescription]=useState(''),[owner,setOwner]=useState(''),[supervisor,setSupervisor]=useState('');
 const [priority,setPriority]=useState('Normal'),[due,setDue]=useState(''),[confirmed,setConfirmed]=useState(false);
 const [state,setState]=useState(''),[note,setNote]=useState(''),[editVersion,setEditVersion]=useState(null);
 const [detailRefresh,setDetailRefresh]=useState(0),[editOwner,setEditOwner]=useState(''),[editSupervisor,setEditSupervisor]=useState(''),[editDue,setEditDue]=useState('');
 const current=cases.find(c=>c.id===selected),review=latestDefectReview(notes),metrics=caseMetrics(cases);
 const creation=caseCreationGate(inspection,notes,cases,inspectionLoading);
 const draftError=caseDraftError({description,owner,supervisor,priority,due},people);
 const creationBlocked=!creation.ready?creation.reason:draftError||(!confirmed?'Confirm that the saved Staff review identifies a defect before creating the case.':'');
 const canEdit=caseCanEdit(current,user.id,people.some(p=>p.user_id===user.id&&p.role==='developer'));
 const editConflict=!!current&&editVersion!==null&&editVersion!==current.version;
 async function load(){
  const g=++generation.current,client=await cloudClient();
  const permission=await client.rpc('defectrag_ca_staff');
  if(g!==generation.current)return;
  if(permission.error||permission.data!==true){setAccess('denied');setCases([]);setPeople([]);setSelected('');setHistory([]);setEvents([]);throw new Error('Sign in with an approved Staff account and verify the security code before opening corrective actions.')}
  const results=await Promise.all([client.from('corrective_actions').select('*').order('created_at',{ascending:false}).limit(500),
   client.from('staff_members').select('user_id,display_name,role,revoked_at').is('revoked_at',null)]);
  if(g!==generation.current)return;
  if(results.some(r=>r.error)){setAccess('unavailable');setCases([]);setPeople([]);setSelected('');setHistory([]);setEvents([]);throw results.find(r=>r.error).error}
  setAccess('authorized');setCases(results[0].data||[]);setPeople(results[1].data||[]);setError('');setDetailRefresh(value=>value+1);
 }
 useEffect(()=>{const poll=startPolling(load,{onState:s=>{if(s.error){setAccess('unavailable');setError(s.error);setCases([]);setPeople([]);setSelected('');setHistory([]);setEvents([])}}});
  return()=>{poll.stop();generation.current++};
 },[user.id]);
 useEffect(()=>{const changed=()=>{generation.current++;setAccess('checking');setCases([]);setPeople([]);setSelected('');setHistory([]);setEvents([]);load().catch(e=>setError(e.message))};window.addEventListener('defectrag-auth-change',changed);return()=>window.removeEventListener('defectrag-auth-change',changed)},[user.id]);
 useEffect(()=>{
  if(previousInspection.current&&previousInspection.current!==inspection?.id){setDescription('');setOwner('');setSupervisor('');setDue('');setPriority('Normal')}
  previousInspection.current=inspection?.id;setConfirmed(false);
 },[inspection?.id]);
 useEffect(()=>{setConfirmed(false)},[review?.id]);
 useEffect(()=>{if(access==='authorized')focusInspectionDetails(casePanel.current)},[access,inspection?.id,review?.id]);
 function resetCaseDraft(){setNote('');setState(current?.state||'');setEditOwner(current?.owner_id||'');setEditSupervisor(current?.supervisor_id||'');setEditDue('');setEditVersion(current?.version??null)}
 useEffect(resetCaseDraft,[current?.id]);
 useEffect(()=>{if(current)focusInspectionDetails(caseDetails.current)},[current?.id]);
 useEffect(()=>{let active=true;const issued=generation.current;setHistory([]);setEvents([]);if(!current||access!=='authorized')return;
  cloudClient().then(client=>Promise.all([
   client.from('corrective_action_history').select('*').eq('case_id',current.id).order('version'),
   client.from('corrective_action_events').select('id,case_id,version,kind,status,attempts,last_error,created_at').eq('case_id',current.id).order('created_at',{ascending:false})
  ])).then(values=>{if(!active||issued!==generation.current)return;if(values.some(r=>r.error))throw values.find(r=>r.error).error;setHistory(values[0].data||[]);setEvents(values[1].data||[])}).catch(e=>{if(active&&issued===generation.current)setError(e.message)});
  return()=>{active=false};
 },[current?.id,current?.version,detailRefresh,user.id,access]);
 async function task(action){if(saving.current)return;saving.current=true;setBusy(true);setError('');try{await action();await load();workspaceChanged()}catch(e){setError(e.message||'Corrective action request failed.')}finally{saving.current=false;setBusy(false)}}
 const name=id=>people.find(p=>p.user_id===id)?.display_name||'Former / unavailable staff';
 return <section className="card case-workspace" ref={casePanel} tabIndex={-1} aria-label="Corrective Actions workspace"><div className="section-title"><div><h2>Corrective Actions</h2><p>Track work needed after a Staff review confirms a defect. Assign someone to fix it, set a due date, and keep a record of progress.</p></div><button className="secondary" disabled={busy} onClick={()=>task(load)}>Refresh cases</button></div>
 {error&&<div className="error" role="alert">{friendlyError(error)}</div>}
 {access==='checking'&&<p role="status">Checking Staff access and the security code…</p>}
 {access!=='checking'&&access!=='authorized'&&<p className="note">Open Staff workspace to check account approval and enter the security code. Then return here and try again.</p>}
 {access==='authorized'&&<>
 <p className="caption">Showing up to 500 cases available to this account. Open: {metrics.open} · Resolved / closed: {metrics.resolved} · Overdue: {metrics.overdue} · Average resolution: {metrics.averageResolutionHours===null?'No resolved cases':metrics.averageResolutionHours.toFixed(1)+' hours'}. Email delivery is separate from whether the case has been saved.</p>
 <h3>Create and assign a case</h3>
 <p className="caption">1. Choose a Team inspection. 2. Save its defect review. 3. Assign the work and deadline.</p>
 {onSelectInspection&&<label className="field">Team inspection<select value={inspection?.id||''} disabled={busy||inspectionLoading} onChange={e=>onSelectInspection(e.target.value)}><option value="">Choose a shared product inspection</option>{inspections.filter(row=>!row.archived_at).map(row=><option key={row.id} value={row.id}>{row.payload?.category||'Product'} · {row.id.slice(0,8)} · {new Date(row.created_at).toLocaleString()}</option>)}</select></label>}
 {onSelectInspection&&!inspections.some(row=>!row.archived_at)&&<p className="note">No active Team inspections are available. Open a saved Personal inspection and choose Share with team before creating a case.</p>}
 <p className="note" id="case-creation-guidance" role="status">{creation.reason}</p>
 <p className="caption">Assignment fields can be filled in as a draft. Nothing is saved or emailed until Create corrective action succeeds. Unsaved drafts stay on this page. Reloading, signing out or losing verified access can discard them.</p>
 {!people.length&&<p className="note">No active Staff are available for assignment. Refresh cases or contact the workspace administrator. No account permissions will be changed here.</p>}
 {inspection&&!inspection.archived_at&&!inspectionLoading&&<button className="secondary" disabled={busy} onClick={()=>onEvidence?.(inspection.id)}>Open photo and Staff review</button>}
 {creation.existingCaseId&&<button className="secondary" onClick={()=>setSelected(creation.existingCaseId)}>Open existing case</button>}
 <form className="login-form" aria-label="Assign corrective action" aria-describedby="case-creation-guidance case-submit-guidance" onSubmit={e=>{e.preventDefault();if(creationBlocked||busy||saving.current)return;return task(async()=>{
  const client=await cloudClient();const id=await caseRpc(client,'defectrag_create_corrective_action',{p_inspection:inspection.id,p_review:creation.review.id,p_confirmed:confirmed,p_owner:owner,p_supervisor:supervisor,p_priority:priority,p_description:description,p_due:new Date(due).toISOString()});setSelected(id);setDescription('');setConfirmed(false);
 })}}>
 <label className="field">What needs fixing?<textarea disabled={busy} required minLength={10} maxLength={2000} value={description} onInput={e=>setDescription(e.target.value)} onChange={e=>setDescription(e.target.value)}/></label>
 <label className="field">Person responsible<select disabled={busy} required value={owner} onChange={e=>setOwner(e.target.value)}><option value="">Choose active staff</option>{people.map(p=><option key={p.user_id} value={p.user_id}>{p.display_name}</option>)}</select></label>
 <label className="field">Supervisor<select disabled={busy} required value={supervisor} onChange={e=>setSupervisor(e.target.value)}><option value="">Choose active staff</option>{people.map(p=><option key={p.user_id} value={p.user_id}>{p.display_name}</option>)}</select></label>
 <label className="field">Priority<select disabled={busy} value={priority} onChange={e=>setPriority(e.target.value)}>{['Low','Normal','High','Critical'].map(p=><option key={p}>{p}</option>)}</select></label>
 <label className="field">Due date and time<input disabled={busy} type="datetime-local" required value={due} onInput={e=>setDue(e.target.value)} onChange={e=>setDue(e.target.value)}/></label>
 <p className="caption">Times use this device’s time zone. Choose a future deadline within the next year. The deadline is saved with the case.</p>
 <p className="note">Email reminders require administrator activation. Saving this case does not send an email by itself. The current n8n workflow targets the supervisor; it does not yet email the person responsible automatically. Confirm delivery with the supervisor separately.</p>
 <label><input type="checkbox" disabled={busy||!creation.ready} checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> A Staff review has confirmed a defect that needs fixing. An unusual inspection result alone is not enough.</label>
 <p className="note" id="case-submit-guidance" role="status">{creationBlocked?'Cannot create yet: '+creationBlocked:'Ready to save the assignment. No email is sent by this button.'}</p>
 <button className="primary" disabled={busy||!!creationBlocked}>Create corrective action</button></form>
 <h3 className="section-gap">Saved cases</h3>
 <div className="table-wrap"><table><thead><tr><th>Case</th><th>Status</th><th>Owner</th><th>Priority</th><th>Due</th><th/></tr></thead><tbody>{cases.map(c=><tr key={c.id}><td>{c.id.slice(0,8)}</td><td>{c.state}{!['Resolved','Closed','Cancelled'].includes(c.state)&&Date.parse(c.due_at)<Date.now()?' · Overdue':''}</td><td>{name(c.owner_id)}</td><td>{c.priority}</td><td>{new Date(c.due_at).toLocaleString()}</td><td><button className="text-button" onClick={()=>setSelected(c.id)}>Details</button></td></tr>)}</tbody></table>{!cases.length&&<p className="caption">No cases are available to this account yet.</p>}</div>
 {current&&<div className="cloud-message" ref={caseDetails} tabIndex={-1} aria-label="Corrective action case details"><div className="section-title"><h3>Case {current.id.slice(0,8)} · {current.state}</h3><button className="text-button" onClick={()=>setSelected('')}>Close details</button></div><p>{current.description}</p><p>Person responsible: {name(current.owner_id)} · Supervisor: {name(current.supervisor_id)} · Due: {new Date(current.due_at).toLocaleString()}</p><p>Confirmed by: {name(current.confirmed_by)}</p><button className="secondary" onClick={()=>onEvidence(current.inspection_id)}>Open the linked photo and review</button>
 {nextCaseStates(current.state).length>0&&!canEdit&&<p className="note">Only the person responsible, the supervisor or a Developer can change this case after verifying their security code. Other Staff can read it.</p>}
 {!nextCaseStates(current.state).length&&<p className="note">This case is {current.state.toLowerCase()}. Its saved assignment and history are available to read; further updates are not permitted.</p>}
 {editConflict&&canEdit&&<p className="note" role="status">This case changed while the update was being drafted. The draft has been kept; it has not been saved. Copy any text needed before loading the latest case. <button className="secondary" disabled={busy} onClick={()=>{resetCaseDraft();setError('')}}>Load latest case and replace draft</button></p>}
 {nextCaseStates(current.state).length>0&&canEdit&&<form className="login-form" onSubmit={e=>{e.preventDefault();task(async()=>{
  if(editConflict)throw new Error('The case changed. Load the latest case before saving.');
  const client=await cloudClient();const version=await caseRpc(client,'defectrag_update_corrective_action',{p_id:current.id,p_version:editVersion,p_state:state,p_note:note,p_owner:editOwner,p_supervisor:editSupervisor,p_due:editDue?new Date(editDue).toISOString():null});setEditVersion(version);setNote('');setEditDue('');
 })}}><label className="field">Case status<select disabled={busy||editConflict} value={state} onChange={e=>setState(e.target.value)}>{nextCaseStates(current.state).map(s=><option key={s}>{s}</option>)}</select></label>
 <label className="field">Owner<select disabled={busy||editConflict} required value={editOwner} onChange={e=>setEditOwner(e.target.value)}><option value="">Choose active staff</option>{people.map(p=><option key={p.user_id} value={p.user_id}>{p.display_name}</option>)}</select></label>
 <label className="field">Supervisor<select disabled={busy||editConflict} required value={editSupervisor} onChange={e=>setEditSupervisor(e.target.value)}><option value="">Choose active staff</option>{people.map(p=><option key={p.user_id} value={p.user_id}>{p.display_name}</option>)}</select></label>
 <label className="field">Change due date and time (optional)<input disabled={busy||editConflict} type="datetime-local" value={editDue} onInput={e=>setEditDue(e.target.value)} onChange={e=>setEditDue(e.target.value)}/></label>
 <label className="field">What changed or was fixed?<textarea disabled={busy} required minLength={3} maxLength={2000} value={note} onInput={e=>setNote(e.target.value)} onChange={e=>setNote(e.target.value)}/></label><button className="primary" disabled={busy||!state||editConflict}>Save case update</button></form>}
 <h3>Status history</h3>{history.map(h=><p key={h.id}><strong>{h.state}</strong> · {name(h.actor_id)} · {new Date(h.created_at).toLocaleString()}<br/>{h.note}{h.snapshot&&<small><br/>Owner: {name(h.snapshot.owner_id)} · Supervisor: {name(h.snapshot.supervisor_id)} · Due: {new Date(h.snapshot.due_at).toLocaleString()}</small>}</p>)}
 <h3>Email delivery</h3><p className="caption">Waiting emails have not been sent. If delivery fails or is uncertain, contact the workspace administrator. The case stays saved even when the email service is unavailable.</p>{events.map(e=><p key={e.id}>{eventLabel(e.kind)} · {deliveryLabel(e.status)} · attempts {e.attempts}{e.last_error?' · '+friendlyError(e.last_error):''}</p>)}</div>}
 </>}
 </section>;
}
