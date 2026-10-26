import {friendlyError,resultLabel} from './userLanguage.mjs';
import React,{useEffect,useState,useRef} from 'react';
import {Users,Cloud,LogIn,LogOut,RefreshCw,ArchiveRestore,Archive,Send,ShieldCheck,ExternalLink,LoaderCircle} from 'lucide-react';
import {cloudConfigured,cloudClient,currentStaff,workspaceChanged} from './cloud.js';
import ReviewForm from './ReviewForm.jsx';
import CorrectiveActions from './CorrectiveActions.jsx';
import {parseReview,reviewBody} from './workflow.mjs';
import {startPolling} from './workspace.mjs';
import AccountSecurity from './AccountSecurity.jsx';
import {authWorkflowEnabled,privateTeamImages} from './authSecurity.mjs';
import {caseInterfaceEnabled,focusInspectionDetails} from './teamNavigation.mjs';

export default function TeamWorkspace({onOpenInspection,onOpenCorrectiveActions,onChooseInspection,casesView=false,initialInspectionId=null}){
 const selection=useRef(0),selectionUser=useRef(null),loads=useRef(0),selectedRef=useRef(null),imageTime=useRef(0);
 const detailsRef=useRef(null),initialSelection=useRef(null);
 const [detailsOpened,setDetailsOpened]=useState(0),[opening,setOpening]=useState(false);
 const [sync,setSync]=useState({state:'refreshing'});
 const [user,setUser]=useState(null),[staff,setStaff]=useState(null),[rows,setRows]=useState([]),[directory,setDirectory]=useState({});
 const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [archived,setArchived]=useState(false),[selected,setSelected]=useState(null),[images,setImages]=useState([]),[notes,setNotes]=useState([]),[note,setNote]=useState('');
 const [recovery,setRecovery]=useState(false),[newPassword,setNewPassword]=useState(''),[confirm,setConfirm]=useState(false);
 const [securityClient,setSecurityClient]=useState(null);
 const authEnabled=authWorkflowEnabled();
 const casesEnabled=caseInterfaceEnabled(window.DEFECTRAG_PUBLIC_CONFIG);
 useEffect(()=>()=>{images.filter(src=>src.startsWith('blob:')).forEach(src=>URL.revokeObjectURL(src))},[images]);
 useEffect(()=>{selectedRef.current=selected},[selected]);
 useEffect(()=>{if(selected)focusInspectionDetails(detailsRef.current)},[detailsOpened]);
 useEffect(()=>{
  if(!user||!staff||!initialInspectionId)return;
  const key=user.id+':'+initialInspectionId;
  if(initialSelection.current===key)return;
  initialSelection.current=key;open({id:initialInspectionId},{focus:!casesView});
 },[user?.id,staff?.user_id,initialInspectionId]);
 const configured=cloudConfigured();
 async function task(action){setBusy(true);setError('');try{await action()}catch(e){setError(e.message||'Team request failed.')}finally{setBusy(false)}}
 async function refresh(){
   const generation=++loads.current,selectionGeneration=selection.current,selectedID=selectedRef.current?.id;
   const {client,staff:member}=await currentStaff();
   let query=client.from('shared_inspections').select('*').order('created_at',{ascending:false}).limit(200);
   query=archived?query.not('archived_at','is',null):query.is('archived_at',null);
   const [{data,error:queryError},{data:people,error:peopleError},noteResult]=await Promise.all([query,client.from('staff_members').select('*'),selectedID?client.from('staff_notes').select('*').eq('inspection_id',selectedID).order('created_at'):{data:[]}]);
   if(queryError)throw queryError;if(peopleError)throw peopleError;if(noteResult.error)throw noteResult.error;
   if(generation!==loads.current)return;
   setStaff(member);setError('');setRows(data||[]);setDirectory(Object.fromEntries((people||[]).map(p=>[p.user_id,p.display_name])));
   if(selectedID&&selectionGeneration===selection.current){
    const fresh=(data||[]).find(row=>row.id===selectedID);
    if(!fresh){selection.current++;setSelected(null);setImages([]);setNotes([])}
    else{
     setSelected(fresh);setNotes(noteResult.data||[]);
     if(Date.now()-imageTime.current>8*60*1000){
      if(authEnabled){
       const urls=await privateTeamImages(client,fresh);
       if(generation===loads.current&&selectionGeneration===selection.current){setImages(urls);imageTime.current=Date.now()}
       else urls.forEach(src=>URL.revokeObjectURL(src));
      }else{
      const urls=await Promise.all([fresh.image_path,fresh.heatmap_path].map(path=>client.storage.from('team-inspections').createSignedUrl(path,900)));
      if(generation===loads.current&&selectionGeneration===selection.current){if(urls.some(value=>value.error))throw new Error('Shared image links could not refresh.');setImages(urls.map(value=>value.data.signedUrl));imageTime.current=Date.now()}
      }
     }
    }
   }
 }
 useEffect(()=>{if(!configured)return;let cancelled=false,subscription;
  cloudClient().then(async client=>{
   if(!cancelled&&authEnabled)setSecurityClient(client);
   subscription=client.auth.onAuthStateChange((event,session)=>{if(!cancelled){const next=session?.user?.id||null;if(selectionUser.current!==next){selection.current++;loads.current++;setSelected(null);setRows([]);setImages([]);setNotes([]);setStaff(null);selectionUser.current=next}setUser(session?.user||null);if(event==='PASSWORD_RECOVERY')setRecovery(true)}}).data.subscription;
   const {data}=await client.auth.getUser();if(!cancelled)setUser(data.user);
  }).catch(e=>{if(!cancelled)setError(e.message)});
  return()=>{cancelled=true;selection.current++;subscription?.unsubscribe()};
 },[configured]);
 useEffect(()=>{if(!user)return;const poll=startPolling(refresh,{onState:value=>{setSync(value);if(value.error){setError(value.error);if(authEnabled){selection.current++;setRows([]);setDirectory({});setSelected(null);setImages([]);setNotes([]);setStaff(null)}}}});
  return()=>{poll.stop();loads.current++};
 },[user?.id,archived]);
 async function open(row,{focus=true}={}){
  const generation=++selection.current;
  setOpening(true);
  try{await task(async()=>{
   if(generation!==selection.current)return;
   const client=await cloudClient();const bucket=client.storage.from('team-inspections');
   const [{data:fresh,error:recordError},{data,error}]=await Promise.all([
    client.from('shared_inspections').select('*').eq('id',row.id).single(),
    client.from('staff_notes').select('*').eq('inspection_id',row.id).order('created_at')]);
   if(generation!==selection.current)return;
   if(recordError)throw recordError;if(error)throw error;
   const privateUrls=authEnabled?await privateTeamImages(client,fresh):null;
   const urls=privateUrls?privateUrls.map(src=>({data:{signedUrl:src}})):await Promise.all([fresh.image_path,fresh.heatmap_path].map(path=>bucket.createSignedUrl(path,900)));
   if(urls.some(r=>r.error))throw new Error('Private images could not be loaded. Check staff/storage policies.');
   if(generation!==selection.current){privateUrls?.forEach(src=>URL.revokeObjectURL(src));return}
   selectedRef.current=fresh;imageTime.current=Date.now();setSelected(fresh);setImages(urls.map(r=>r.data.signedUrl));setNotes(data||[]);if(focus)setDetailsOpened(value=>value+1);
  })}finally{if(generation===selection.current)setOpening(false)}
 }
 async function archiveMine(){await task(async()=>{
  const client=await cloudClient();const ids=rows.filter(r=>r.owner_id===user.id).map(r=>r.id);
  if(ids.length){const {error}=await client.rpc('archive_team_inspections',{p_ids:ids});if(error)throw error;}
  selection.current++;setSelected(null);setConfirm(false);await refresh();workspaceChanged();
 })}
 if(!configured)return <section className="card cloud-setup"><div className="setup-icon"><Cloud size={32}/></div><span className="eyebrow">TEAM WORKSPACE</span><h2>Team workspace is not available yet.</h2><p>The workspace administrator needs to connect shared storage before Staff can sign in here.</p><div className="setup-grid">{[['01','Connect shared storage','The workspace administrator completes this setup.'],['02','Set up staff access','The administrator sets up approval and account security.'],['03','Connect this dashboard','The administrator connects the app, then Staff can sign in.']].map(([n,t,d])=><div key={n}><b>{n}</b><h3>{t}</h3><p>{d}</p></div>)}</div><a className="primary" href="https://supabase.com/dashboard" target="_blank" rel="noreferrer">Administrator setup <ExternalLink size={16}/></a><p className="caption">Contact the workspace administrator for help. The public demo can be used without Staff access.</p></section>;
 return <><section className="card"><div className="section-title"><div><h2><Users size={21}/> {casesView?'Corrective Actions access':'Staff workspace'}</h2><p>Sign in to review inspections shared with the team. New inspections start in Personal Workspace and are shared only when chosen.</p></div><span className="subtle-tag"><Cloud size={13}/> STAFF ACCESS</span></div>
 {error&&<div className="error" role="alert">{friendlyError(error)}</div>}
 {opening&&<p role="status">Opening the shared photo and review…</p>}
 {casesView&&!casesEnabled&&<p className="note">Corrective Actions has been turned off for this app. Inspections and reviews are still available. Contact the workspace administrator if needed.</p>}
 {authEnabled&&securityClient&&(!casesView||!staff)&&<AccountSecurity key={user?.id||'anonymous'} client={securityClient} user={user} onChange={()=>{workspaceChanged();if(user)task(refresh)}}/>}
 {!user?<form className="login-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.auth.signInWithPassword({email,password});if(error)throw error;setPassword('')})}}><label className="field">Work email<input type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label className="field">Password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<LogIn size={17}/>} Sign in</button><button type="button" className="text-button" disabled={!email||busy} onClick={()=>task(async()=>{const client=await cloudClient();const {error}=await client.auth.resetPasswordForEmail(email,{redirectTo:location.origin+location.pathname});if(error)throw error;setError('Password reset requested. Check the inbox and Spam folder.')})}>Reset password</button><p className="caption">{authEnabled?'A new account needs Developer approval before Staff work is available. Approved Staff must also enter their security code when asked.':'The workspace administrator must approve an account before it can access Staff work.'}</p></form>:<>
 <div className="team-toolbar"><div><ShieldCheck size={18}/><strong>{staff?.display_name||user.email}</strong><span className="subtle-tag">{staff?.role||'CHECKING ACCESS'}</span></div><button className="secondary" disabled={busy} onClick={()=>task(refresh)}><RefreshCw size={16}/> Refresh</button>{!casesView&&staff&&casesEnabled&&<button className="secondary" onClick={()=>onOpenCorrectiveActions?.()}>Open Corrective Actions</button>}{casesView&&staff&&<button className="secondary" onClick={()=>onChooseInspection?.()}>Choose a Team inspection</button>}<button className="secondary" onClick={()=>task(async()=>{const client=await cloudClient();await client.auth.signOut();setRows([]);setSelected(null);setStaff(null)})}><LogOut size={16}/> Sign out</button></div>
 {recovery&&<form className="login-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.auth.updateUser({password:newPassword});if(error)throw error;setNewPassword('');setRecovery(false)})}}><label className="field">Set a new password<input type="password" minLength={12} autoComplete="new-password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>Save password</button></form>}
 {!casesView&&<><div className="team-toolbar"><span role="status">Team Workspace · latest {rows.length} shared inspections · {sync.state==='synced'?'updated at '+new Date(sync.at).toLocaleTimeString():sync.state==='offline'?'offline; shown results may be out of date':sync.state==='stale'?'update failed; shown results may be out of date':'refreshing…'} · checks for changes every 15 seconds</span>{staff?.role==='developer'&&<button className="secondary" onClick={()=>{setArchived(!archived);setSelected(null)}}><ArchiveRestore size={16}/>{archived?'Active history':'Restore archived team work'}</button>}{!archived&&<button className="secondary danger" disabled={busy||!rows.some(r=>r.owner_id===user.id)} onClick={()=>setConfirm(true)}><Archive size={16}/> Archive my shared inspections</button>}</div>
 {confirm&&<div className="note"><div><strong>Archive your visible records?</strong><p>They will leave the shared active history. Original files and conversations remain recoverable by a developer. Other staff members’ records will stay active.</p><div className="button-row"><button className="primary" disabled={busy} onClick={archiveMine}>Archive my records</button><button className="secondary" onClick={()=>setConfirm(false)}>Cancel</button></div></div></div>}
 <div className="table-wrap"><table><thead><tr><th>Inspection</th><th>Product</th><th>Result</th><th>Shared by</th><th>Saved</th><th/></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><strong>{row.id.slice(0,8)}</strong></td><td>{row.payload.category}</td><td><span className={'badge '+row.payload.verdict?.toLowerCase()}>{resultLabel(row.payload.verdict)}</span></td><td>{directory[row.owner_id]||'Staff member'}</td><td>{new Date(row.created_at).toLocaleString()}</td><td><button className="text-button" disabled={busy} onClick={()=>open(row)}>Review</button>{archived&&staff?.role==='developer'&&<button className="text-button" disabled={busy} onClick={()=>task(async()=>{const client=await cloudClient();const {error}=await client.rpc('restore_team_inspections',{p_ids:[row.id]});if(error)throw error;await refresh();workspaceChanged()})}>Restore</button>}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty"><Cloud size={30}/><p>{archived?'No archived records to recover.':'No shared inspections yet. Open an inspection result and select Share with team.'}</p></div>}</div></>}
 </>}
 </section>{casesView&&user&&staff&&casesEnabled&&<CorrectiveActions key={user.id} user={user} inspection={selected} notes={notes} onEvidence={id=>open({id})}/>}
 {user&&selected&&<section className="card" ref={detailsRef} tabIndex={-1} aria-labelledby="shared-inspection-title"><div className="section-title"><div><h2 id="shared-inspection-title">Shared inspection · {selected.id.slice(0,8)}</h2><p>Shared copy from {directory[selected.owner_id]||'a colleague'}. These are saved results. Opening them does not run another inspection.</p></div><div className="button-row">{onOpenInspection&&!selected.archived_at&&<button className="secondary" onClick={()=>onOpenInspection(selected)}>Open full result and assistant</button>}{!casesView&&casesEnabled&&!selected.archived_at&&<button className="secondary" onClick={()=>onOpenCorrectiveActions?.(selected)}>Create or view corrective actions</button>}<button className="text-button" onClick={()=>{selection.current++;selectedRef.current=null;setSelected(null);setImages([]);setNotes([])}}>Close</button></div></div><div className="shared-images">{images.map((src,i)=><img key={src} src={src} alt={i?'Saved highlighted areas':'Saved inspected product'}/>)}</div><div className="observation"><strong>SAVED RESULT</strong><span>{resultLabel(selected.payload.verdict)} · score {Number(selected.payload.score).toFixed(5)} · review limit {Number(selected.payload.threshold).toFixed(5)}</span></div><h3 className="section-gap">Saved assistant conversation</h3>{selected.conversation?.length?selected.conversation.map((m,i)=><p className="cloud-message" key={i}><strong>{m.role==='user'?'Inspector':'Evidence Assistant'}: </strong>{m.question||m.answer}</p>):<p className="caption">No assistant conversation was shared with this inspection.</p>}{!selected.archived_at&&<ReviewForm key={selected.id+String(notes.length)} current={notes.map(n=>parseReview(n,directory)).filter(Boolean).at(-1)} disabled={busy} onSave={async value=>{
 const client=await cloudClient();const {error}=await client.from('staff_notes').insert({inspection_id:selected.id,author_id:user.id,body:reviewBody(value.status,value.decision,value.note)});
 if(error)throw error;await open(selected);workspaceChanged();
 }}/>}<h3 className="section-gap">Team notes</h3>{notes.filter(n=>!parseReview(n,directory)).map(n=><div className="cloud-message" key={n.id}><strong>{directory[n.author_id]||'Staff member'}</strong><p>{n.body}</p><small>{new Date(n.created_at).toLocaleString()}</small></div>)}{!selected.archived_at&&<form className="question-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.from('staff_notes').insert({inspection_id:selected.id,author_id:user.id,body:note.trim()});if(error)throw error;setNote('');await open(selected);workspaceChanged()})}}><input aria-label="Staff review note" maxLength={2000} placeholder="Add a note for the team…" value={note} onChange={e=>setNote(e.target.value)}/><button className="primary" disabled={busy||!note.trim()}><Send size={16}/> Add note</button></form>}</section>}</>;
}
