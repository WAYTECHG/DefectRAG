import React,{useEffect,useState} from 'react';
import {Users,Cloud,LogIn,LogOut,RefreshCw,ArchiveRestore,Archive,Send,ShieldCheck,ExternalLink,LoaderCircle} from 'lucide-react';
import {cloudConfigured,cloudClient,currentStaff} from './cloud.js';

export default function TeamWorkspace(){
 const [user,setUser]=useState(null),[staff,setStaff]=useState(null),[rows,setRows]=useState([]),[directory,setDirectory]=useState({});
 const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [archived,setArchived]=useState(false),[selected,setSelected]=useState(null),[images,setImages]=useState([]),[notes,setNotes]=useState([]),[note,setNote]=useState('');
 const [recovery,setRecovery]=useState(false),[newPassword,setNewPassword]=useState(''),[confirm,setConfirm]=useState(false);
 const configured=cloudConfigured();
 async function task(action){setBusy(true);setError('');try{await action()}catch(e){setError(e.message||'Team request failed.')}finally{setBusy(false)}}
 async function refresh(){
   const {client,staff:member}=await currentStaff();setStaff(member);
   let query=client.from('shared_inspections').select('*').order('created_at',{ascending:false}).limit(200);
   query=archived?query.not('archived_at','is',null):query.is('archived_at',null);
   const [{data,error:queryError},{data:people,error:peopleError}]=await Promise.all([query,client.from('staff_members').select('*')]);
   if(queryError)throw queryError;if(peopleError)throw peopleError;
   setRows(data||[]);setDirectory(Object.fromEntries((people||[]).map(p=>[p.user_id,p.display_name])));
 }
 useEffect(()=>{if(!configured)return;let cancelled=false,subscription;
  cloudClient().then(async client=>{
   subscription=client.auth.onAuthStateChange((event,session)=>{if(!cancelled){setUser(session?.user||null);if(event==='PASSWORD_RECOVERY')setRecovery(true)}}).data.subscription;
   const {data}=await client.auth.getUser();if(!cancelled)setUser(data.user);
  }).catch(e=>{if(!cancelled)setError(e.message)});
  return()=>{cancelled=true;subscription?.unsubscribe()};
 },[configured]);
 useEffect(()=>{if(!user)return;let cancelled=false;
  refresh().catch(e=>{if(!cancelled)setError(e.message)});
  const timer=setInterval(()=>refresh().catch(e=>{if(!cancelled)setError(e.message)}),15000);
  return()=>{cancelled=true;clearInterval(timer)};
 },[user?.id,archived]);
 async function open(row){await task(async()=>{
  const client=await cloudClient();const bucket=client.storage.from('team-inspections');
  const urls=await Promise.all([row.image_path,row.heatmap_path].map(path=>bucket.createSignedUrl(path,900)));
  if(urls.some(r=>r.error))throw new Error('Private images could not be loaded. Check staff/storage policies.');
  const {data,error}=await client.from('staff_notes').select('*').eq('inspection_id',row.id).order('created_at');
  if(error)throw error;setSelected(row);setImages(urls.map(r=>r.data.signedUrl));setNotes(data||[]);
 })}
 async function archiveMine(){await task(async()=>{
  const client=await cloudClient();const ids=rows.filter(r=>r.owner_id===user.id).map(r=>r.id);
  if(ids.length){const {error}=await client.rpc('archive_team_inspections',{p_ids:ids});if(error)throw error;}
  setSelected(null);setConfirm(false);await refresh();
 })}
 if(!configured)return <section className="card cloud-setup"><div className="setup-icon"><Cloud size={32}/></div><span className="eyebrow">TEAM WORKSPACE</span><h2>One shared view of inspection.</h2><p>The staff workspace is ready to connect to your own Supabase project. No cloud project or account has been created for you.</p><div className="setup-grid">{[['01','Create a free project','Use your Supabase account and select an eligible Free plan.'],['02','Set up staff access','Run the supplied schema, add your developer account and invite colleagues.'],['03','Connect this dashboard','Add the project URL and publishable key to config.js, then reload.']].map(([n,t,d])=><div key={n}><b>{n}</b><h3>{t}</h3><p>{d}</p></div>)}</div><a className="primary" href="https://supabase.com/dashboard" target="_blank" rel="noreferrer">Open Supabase <ExternalLink size={16}/></a><p className="caption">Setup files: deployment/SUPABASE_SETUP.md and deployment/supabase.sql. Never place a service-role key in the browser. Local inspection works without cloud setup.</p></section>;
 return <><section className="card"><div className="section-title"><div><h2><Users size={21}/> Staff workspace</h2><p>Signed-in staff share saved inspections and review notes. Live AI runs on the connected inspection backend.</p></div><span className="subtle-tag"><Cloud size={13}/> SUPABASE</span></div>
 {error&&<div className="error" role="alert">{error}</div>}
 {!user?<form className="login-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.auth.signInWithPassword({email,password});if(error)throw error;setPassword('')})}}><label className="field">Work email<input type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label className="field">Password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<LogIn size={17}/>} Sign in</button><button type="button" className="text-button" disabled={!email||busy} onClick={()=>task(async()=>{const client=await cloudClient();const {error}=await client.auth.resetPasswordForEmail(email,{redirectTo:location.origin+location.pathname});if(error)throw error;setError('Password reset requested. Check your email.')})}>Reset password</button><p className="caption">Accounts must be invited and approved by your workspace developer. Signing up alone does not grant staff access.</p></form>:<>
 <div className="team-toolbar"><div><ShieldCheck size={18}/><strong>{staff?.display_name||user.email}</strong><span className="subtle-tag">{staff?.role||'CHECKING MEMBERSHIP'}</span></div><button className="secondary" disabled={busy} onClick={()=>task(refresh)}><RefreshCw size={16}/> Refresh</button><button className="secondary" onClick={()=>task(async()=>{const client=await cloudClient();await client.auth.signOut();setRows([]);setSelected(null);setStaff(null)})}><LogOut size={16}/> Sign out</button></div>
 {recovery&&<form className="login-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.auth.updateUser({password:newPassword});if(error)throw error;setNewPassword('');setRecovery(false)})}}><label className="field">Set a new password<input type="password" minLength={12} autoComplete="new-password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>Save password</button></form>}
 <div className="team-toolbar"><span>Latest {rows.length} shared records · refreshes every 15 seconds</span>{staff?.role==='developer'&&<button className="secondary" onClick={()=>{setArchived(!archived);setSelected(null)}}><ArchiveRestore size={16}/>{archived?'Active history':'Developer recovery'}</button>}{!archived&&<button className="secondary danger" disabled={busy||!rows.some(r=>r.owner_id===user.id)} onClick={()=>setConfirm(true)}><Archive size={16}/> Archive my visible history</button>}</div>
 {confirm&&<div className="note"><div><strong>Archive your visible records?</strong><p>They will leave the shared active history. Original files and conversations remain recoverable by a developer. Other staff members’ records will stay active.</p><div className="button-row"><button className="primary" disabled={busy} onClick={archiveMine}>Archive my records</button><button className="secondary" onClick={()=>setConfirm(false)}>Cancel</button></div></div></div>}
 <div className="table-wrap"><table><thead><tr><th>Inspection</th><th>Product</th><th>Result</th><th>Shared by</th><th>Saved</th><th/></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><strong>{row.id.slice(0,8)}</strong></td><td>{row.payload.category}</td><td><span className={'badge '+row.payload.verdict?.toLowerCase()}>{row.payload.verdict}</span></td><td>{directory[row.owner_id]||'Staff member'}</td><td>{new Date(row.created_at).toLocaleString()}</td><td><button className="text-button" onClick={()=>open(row)}>Review</button>{archived&&staff?.role==='developer'&&<button className="text-button" disabled={busy} onClick={()=>task(async()=>{const client=await cloudClient();const {error}=await client.rpc('restore_team_inspections',{p_ids:[row.id]});if(error)throw error;await refresh()})}>Restore</button>}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty"><Cloud size={30}/><p>{archived?'No archived records to recover.':'No shared inspections yet. In the local app, open a result and select Share with staff.'}</p></div>}</div>
 </>}
 </section>{user&&selected&&<section className="card"><div className="section-title"><div><h2>Shared inspection · {selected.id.slice(0,8)}</h2><p>Saved snapshot from {directory[selected.owner_id]||'a colleague'}. This page does not run a new prediction.</p></div><button className="text-button" onClick={()=>setSelected(null)}>Close</button></div><div className="shared-images">{images.map((src,i)=><img key={src} src={src} alt={i?'Saved anomaly heatmap':'Saved inspected product'}/>)}</div><div className="observation"><strong>SAVED MEASUREMENTS</strong><span>{selected.payload.verdict} · score {Number(selected.payload.score).toFixed(5)} · threshold {Number(selected.payload.threshold).toFixed(5)}</span></div><h3 className="section-gap">Recorded evidence</h3>{selected.conversation?.length?selected.conversation.map((m,i)=><p className="cloud-message" key={i}><strong>{m.role==='user'?'Inspector':'Evidence Assistant'}: </strong>{m.question||m.answer}</p>):<p className="caption">No conversation was included when this inspection was shared.</p>}<h3 className="section-gap">Staff review notes</h3>{notes.map(n=><div className="cloud-message" key={n.id}><strong>{directory[n.author_id]||'Staff member'}</strong><p>{n.body}</p><small>{new Date(n.created_at).toLocaleString()}</small></div>)}{!selected.archived_at&&<form className="question-form" onSubmit={e=>{e.preventDefault();task(async()=>{const client=await cloudClient();const {error}=await client.from('staff_notes').insert({inspection_id:selected.id,author_id:user.id,body:note.trim()});if(error)throw error;setNote('');await open(selected)})}}><input aria-label="Staff review note" maxLength={2000} placeholder="Add a review note for your colleagues…" value={note} onChange={e=>setNote(e.target.value)}/><button className="primary" disabled={busy||!note.trim()}><Send size={16}/> Add note</button></form>}</section>}</>;
}
