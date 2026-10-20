import React,{useEffect,useState} from 'react';
import {authStatus,decideAccess,enrollTotp,registerAccount,submitAccessRequest,verifyTotp} from './authSecurity.mjs';

// Uses existing dashboard classes; no new theme/layout system or auth vendor.
export default function AccountSecurity({client,user,onChange}){
 const [status,setStatus]=useState(null),[factors,setFactors]=useState([]),[unfinished,setUnfinished]=useState([]),[enrollment,setEnrollment]=useState(null);
 const [code,setCode]=useState(''),[factorId,setFactorId]=useState(''),[name,setName]=useState('');
 const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
 const [directory,setDirectory]=useState([]),[delivery,setDelivery]=useState([]);
 const registrationEnabled=window.DEFECTRAG_PUBLIC_CONFIG?.registrationEnabled===true;
 async function refresh(){
  if(!user){setStatus(null);setDirectory([]);setDelivery([]);return}
  const posture=await authStatus(client);setStatus(posture);
  const {data,error}=await client.auth.mfa.listFactors();if(error)throw error;
  const verified=(data.totp||[]).filter(f=>f.status==='verified');setFactors(verified);
  setUnfinished((data.all||[]).filter(f=>f.factor_type==='totp'&&f.status==='unverified'));
  setFactorId(previous=>verified.some(f=>f.id===previous)?previous:verified[0]?.id||'');
  if(posture.role==='developer'&&posture.approved&&posture.aal2){
   const [members,messages]=await Promise.all([client.rpc('defectrag_access_directory'),client.rpc('defectrag_notification_status')]);
   if(members.error)throw members.error;if(messages.error)throw messages.error;
   setDirectory(members.data||[]);setDelivery(messages.data||[]);
  }else{setDirectory([]);setDelivery([])}
 }
 async function run(action){setBusy(true);setNotice('');try{await action()}catch(error){setNotice(error.message||'Security request failed.')}finally{setBusy(false)}}
 useEffect(()=>{let active=true;
  setEnrollment(null);setCode('');setDirectory([]);setDelivery([]);
  if(client&&user)refresh().catch(error=>{if(active)setNotice(error.message)});
  else setStatus(null);
  return()=>{active=false};
 },[client,user?.id]);
 async function verified(){
  await verifyTotp(client,enrollment?.id||factorId,code);setCode('');setEnrollment(null);
  await refresh();onChange();setNotice('Authenticator verified. Account approval still controls staff access.');
 }
 return <div className="section-gap">
  <h3>Account access & security</h3>
  {notice&&<p className="note" role="status">{notice}</p>}
  {!user?registrationEnabled?<form className="login-form" onSubmit={event=>{event.preventDefault();run(async()=>{
   await registerAccount(client,{email,password,displayName:name,redirectTo:location.origin+location.pathname});
   setPassword('');setNotice('If registration is available, check the email for confirmation. Sign in afterward and submit the staff access request. Registration does not grant staff access.');
  })}}><p>Register an account to request staff access. Public Demo Mode does not require registration.</p>
   <label className="field">Display name<input value={name} onChange={e=>setName(e.target.value)} maxLength={80} autoComplete="name" required/></label>
   <label className="field">Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" required/></label>
   <label className="field">New password<input type="password" minLength={12} value={password} onChange={e=>setPassword(e.target.value)} autoComplete="new-password" required/></label>
   <button className="secondary" disabled={busy||!client}>Register account</button>
  </form>:<p className="caption">Self-registration is not enabled. Existing approved accounts can sign in below. Public Demo Mode remains accessible.</p>:<>
   <p>Access: <strong>{status?.revoked?'revoked':status?.approved?'approved':status?.request_status||'not requested'}</strong> · Authenticator: <strong>{status?.aal2?'verified session':'session not verified'}</strong></p>
   <button className="secondary" disabled={busy} onClick={()=>run(refresh)}>Refresh account status</button>
   {status&&!status.approved&&!status.revoked&&!status.request_status&&<form className="login-form" onSubmit={event=>{event.preventDefault();run(async()=>{await submitAccessRequest(client,name);await refresh();setNotice('Access request saved. Staff data remains unavailable until developer approval.');onChange()})}}>
    <label className="field">Display name<input value={name} maxLength={80} onChange={e=>setName(e.target.value)} required/></label>
    <button className="primary" disabled={busy||!status.registration_enabled||!status.email_verified}>Request staff access</button>
   </form>}
   <p className="caption">Enrollment does not grant membership. Keep the authenticator available before mandatory MFA is enabled. Lost-factor recovery requires the workspace administrator; password reset does not remove MFA.</p>
   {!enrollment&&!factors.length&&!unfinished.length&&<button className="secondary" disabled={busy} onClick={()=>run(async()=>setEnrollment(await enrollTotp(client)))}>Set up authenticator</button>}
   {!enrollment&&unfinished.map(f=><p key={f.id} className="caption">An unfinished enrollment exists. <button className="text-button" disabled={busy} onClick={()=>run(async()=>{const {error}=await client.auth.mfa.unenroll({factorId:f.id});if(error)throw error;await refresh()})}>Cancel unfinished setup</button></p>)}
   {enrollment&&<div className="note"><div><p>Scan this QR code in an authenticator. Keep it private and verify a code to finish enrollment.</p><img src={enrollment.totp.qr_code} width="200" height="200" alt="Private authenticator enrollment QR code"/><button className="text-button" disabled={busy} onClick={()=>run(async()=>{
    const {error}=await client.auth.mfa.unenroll({factorId:enrollment.id});if(error)throw error;setEnrollment(null);setCode('');
   })}>Cancel unfinished enrollment</button></div></div>}
   {(enrollment||factors.length>0)&&<form className="login-form" onSubmit={event=>{event.preventDefault();run(verified)}}>
    {!enrollment&&<label className="field">Authenticator<select value={factorId} onChange={e=>setFactorId(e.target.value)}>{factors.map(f=><option key={f.id} value={f.id}>{f.friendly_name||'Authenticator'}</option>)}</select></label>}
    <label className="field">Six-digit code<input inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={e=>setCode(e.target.value)} required/></label>
    <button className="primary" disabled={busy}>Verify authenticator</button>
   </form>}
   {status?.role==='developer'&&status.approved&&status.aal2&&<>
    <h3 className="section-gap">Staff access management</h3><p>Only pending requests can be approved or rejected. Revocation retains inspection history and blocks new protected operations.</p>
    <div className="table-wrap"><table><thead><tr><th>Account</th><th>Status</th><th>Role</th><th>Action</th></tr></thead><tbody>{directory.map(row=><tr key={row.user_id}><td>{row.display_name}<br/><small>{row.email}</small></td><td>{row.status}</td><td>{row.role||'applicant'}</td><td>{row.user_id!==user.id&&(row.status==='pending'?['approve','reject']:row.status==='approved'?['revoke']:[]).map(action=><button key={action} className="text-button" disabled={busy} onClick={()=>{
     if(!window.confirm(`${action[0].toUpperCase()+action.slice(1)} access for ${row.display_name}?`))return;
     run(async()=>{await decideAccess(client,row,action);await refresh();onChange();setNotice('Access decision saved. Notification delivery is tracked separately.');});
    }}>{action}</button>)}</td></tr>)}</tbody></table></div>
    <h3 className="section-gap">Notification delivery</h3><p className="caption">Queued messages wait while the notification service is offline. Sent means the mail provider accepted the message, not proof of inbox delivery.</p>
    <div className="table-wrap"><table><thead><tr><th>Event</th><th>Delivery</th><th>Attempts</th><th/></tr></thead><tbody>{delivery.map(row=><tr key={row.id}><td>{row.kind}</td><td>{row.status}</td><td>{row.attempts}</td><td>{row.status==='dead'&&<button className="text-button" disabled={busy} onClick={()=>run(async()=>{const {error}=await client.rpc('defectrag_retry_notification',{p_id:row.id});if(error)throw error;await refresh()})}>Retry delivery</button>}</td></tr>)}</tbody></table></div>
   </>}
  </>}
 </div>;
}
