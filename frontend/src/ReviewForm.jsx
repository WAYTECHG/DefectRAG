import {friendlyError,resultLabel} from './userLanguage.mjs';
import React,{useState} from 'react';
import {decisionLabel,reviewBody,reviewStatuses,reviewDecisions} from './workflow.mjs';

export default function ReviewForm({current,onSave,disabled=false,demo=false}){
 const [status,setStatus]=useState(current?.status||'Needs review');
 const [decision,setDecision]=useState(current?.decision||'Pending');
 const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 return <section className="review-form" data-tour="review"><h3>{demo?'Demo review · this browser only':'Staff review'}</h3>
  {demo&&<p className="note">Try recording a review here. It stays with this demo result and is not an official Staff review, Team decision or corrective action.</p>}
  {current&&<p className="caption"><strong>{current.status} · {decisionLabel(current.decision)}</strong> · {current.reviewer} · {new Date(current.created_at).toLocaleString()}{current.note&&<><br/>{current.note}</>}</p>}
  <p className="caption">Check the photo and result, then record the review. The inspection result stays unchanged. Choose Reviewed, then the decision about the product: Accept when there is no defect, Hold when more checks are needed, or Reject when a defect is confirmed. Only a confirmed defect can start a corrective action.</p>
  <form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{reviewBody(status,decision,note);await onSave({status,decision,note});setNote('')}catch(err){setError(err.message)}finally{setBusy(false)}}}>
   <div className="filters"><label className="field">Review status<select value={status} disabled={disabled||busy} onChange={e=>{setStatus(e.target.value);setDecision(e.target.value==='Reviewed'?'Hold':'Pending')}}>{reviewStatuses.map(value=><option key={value}>{value}</option>)}</select></label>
   <label className="field">Review decision<select value={decision} disabled={disabled||busy||status!=='Reviewed'} onChange={e=>setDecision(e.target.value)}>{(status==='Reviewed'?reviewDecisions.slice(1):['Pending']).map(value=><option key={value} value={value}>{decisionLabel(value)}</option>)}</select></label></div>
   <div className="question-form"><input aria-label="Review decision note" value={note} maxLength={1000} disabled={disabled||busy} placeholder="Add a reason or what was checked…" onChange={e=>setNote(e.target.value)}/><button className="primary" disabled={disabled||busy}>{busy?'Saving review…':'Save review'}</button></div>
   {error&&<p role="alert" className="error">{friendlyError(error)}</p>}
  </form>
 </section>;
}
