import React,{useState} from 'react';
import {reviewBody,reviewStatuses,reviewDecisions} from './workflow.mjs';

export default function ReviewForm({current,onSave,disabled=false}){
 const [status,setStatus]=useState(current?.status||'Needs review');
 const [decision,setDecision]=useState(current?.decision||'Pending');
 const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 return <section className="review-form"><h3>Human review</h3>
  {current&&<p className="caption"><strong>{current.status} · {current.decision}</strong> · {current.reviewer} · {new Date(current.created_at).toLocaleString()}{current.note&&<><br/>{current.note}</>}</p>}
  <p className="caption">Human decisions are recorded separately from the model verdict. Acceptance depends on the applicable quality process.</p>
  <form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{reviewBody(status,decision,note);await onSave({status,decision,note});setNote('')}catch(err){setError(err.message)}finally{setBusy(false)}}}>
   <div className="filters"><label className="field">Review status<select value={status} disabled={disabled||busy} onChange={e=>{setStatus(e.target.value);setDecision(e.target.value==='Reviewed'?'Hold':'Pending')}}>{reviewStatuses.map(value=><option key={value}>{value}</option>)}</select></label>
   <label className="field">Human decision<select value={decision} disabled={disabled||busy||status!=='Reviewed'} onChange={e=>setDecision(e.target.value)}>{(status==='Reviewed'?reviewDecisions.slice(1):['Pending']).map(value=><option key={value}>{value}</option>)}</select></label></div>
   <div className="question-form"><input aria-label="Review decision note" value={note} maxLength={1000} disabled={disabled||busy} placeholder="Optional reason or review evidence…" onChange={e=>setNote(e.target.value)}/><button className="primary" disabled={disabled||busy}>{busy?'Saving review…':'Save review'}</button></div>
   {error&&<p role="alert" className="error">{error}</p>}
  </form>
 </section>;
}
