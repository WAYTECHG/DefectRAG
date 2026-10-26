import React,{useEffect,useRef} from 'react';
import {ArrowLeft,BookOpen,CheckCircle,ScanLine,X} from 'lucide-react';
import InspectionViewer from './InspectionViewer.jsx';
import InspectionAction from './InspectionAction.jsx';
import {practiceRecord,tutorialSteps} from './tutorial.mjs';
import {nextCaseStates} from './correctiveActions.mjs';
import practiceOriginal from './practiceAssets/candle-original.jpg';
import practiceHeatmap from './practiceAssets/candle-heatmap.jpg';
import practiceNormal from './practiceAssets/candle-normal.jpg';

const staticUrl=path=>path,people=['Alex (practice)','Sam (practice)'];
export default function GuidedPractice({state,page,onAction,onReturn,onDismiss}){
 const root=useRef(null),heading=useRef(null),steps=tutorialSteps(),step=steps[state.step];
 const complete=(event,extra={})=>onAction({type:'complete',event,...extra});
 const field=(name,value)=>onAction({type:'field',name,value});
 function chooseTomorrow(){
  const due=new Date();due.setDate(due.getDate()+1);due.setHours(12,0,0,0);
  const pad=value=>String(value).padStart(2,'0');
  field('due',`${due.getFullYear()}-${pad(due.getMonth()+1)}-${pad(due.getDate())}T12:00`);
 }
 const cls=(target,base='')=>base+(step.target===target?' guided-target':'');
 useEffect(()=>{
  if(page!==step.page)return;
  heading.current?.focus({preventScroll:true});
  (step.target==='history-nav'?document:root.current)?.querySelector('[data-practice-target="'+step.target+'"]')?.scrollIntoView({block:'nearest',behavior:'instant'});
 },[state.step,page,step.page,step.target]);
 useEffect(()=>{const escape=e=>{if(e.key==='Escape'&&!document.querySelector('dialog[open]'))onDismiss()};window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape)},[onDismiss]);
 const submit=event=>e=>{e.preventDefault();complete(event)};
 const record={...practiceRecord,image_url:practiceOriginal,heatmap_url:practiceHeatmap};
 return <section ref={root} className="guided-practice" aria-label="Guided practice workspace">
  <section className="card guided-coach" aria-labelledby="practice-heading">
   <div className="section-title"><span className="subtle-tag"><BookOpen size={14}/> PRACTICE · STEP {state.step+1} OF {steps.length}</span><button type="button" className="text-button" onClick={onDismiss}><X size={15}/> Skip tutorial</button></div>
   <progress aria-label="Practice progress" value={state.step+1} max={steps.length}/>
   <h2 ref={heading} tabIndex={-1} id="practice-heading">{step.title}</h2><p aria-live="polite">{step.instruction}</p>
   <div className="guided-footer"><small>Practice only · nothing is saved online, shared or emailed.</small><button type="button" className="text-button" disabled={state.step===0} onClick={()=>onAction({type:'back'})}><ArrowLeft size={15}/> Previous step</button></div>
  </section>
  {state.error&&<p className="error" role="alert">{state.error}</p>}
  {page!==step.page?<section className="card"><h2>Continue the current practice step</h2><p>The lesson is waiting on another page. Normal workspace controls return after the lesson ends.</p><button type="button" className="primary" onClick={onReturn}>Return to current step</button></section>:<>
  {page==='inspect'&&<>
   <div className="inspection-grid"><section className="card upload-card"><div className="section-title"><h2>Add a product photo</h2><span className="subtle-tag">PRACTICE COPY</span></div>
    <label data-practice-target="product" className={cls('product','field')}>Product category<select value={state.category} disabled={step.event!=='product'} onChange={e=>{field('category',e.target.value);if(e.target.value==='candle')complete('product')}}><option value="">Choose the product</option><option value="capsules">Capsules</option><option value="candle">Candle</option><option value="pcb1">PCB 1</option></select></label>
    <div data-practice-target="photo" className={cls('photo','guided-photo')}><img src={record.image_url} alt="Public Candle sample photo"/><button type="button" className="secondary" disabled={step.event!=='photo'} onClick={()=>complete('photo')}>{state.photo?'Sample photo selected':'Use sample photo'}</button><p className="caption">Public VisA sample · Zou et al., ECCV 2022 · CC BY 4.0. Personal photos are not used in this lesson.</p></div>
    <div data-practice-target="run" className={cls('run')}><InspectionAction readiness={{disabled:step.event!=='inspect'||!state.photo,reason:!state.photo?'Choose the product and sample photo first.':step.event!=='inspect'?'Follow the highlighted practice action.':''}} busy={false} multiple={false} onRun={()=>complete('inspect')}/></div>
   </section><section className="card result-card"><div className="section-title"><h2>Inspection result</h2><span className="subtle-tag">SAVED TEACHING EXAMPLE</span></div>
    {state.inspected?<><h3>Unusual appearance found</h3><p>Historical model: {record.model_id}</p><p className="caption">{record.source} These are historical example measurements, not the current operating limits.</p>
     <div data-practice-target="compare" className={cls('compare')}><InspectionViewer record={record} url={staticUrl} heatmap={true} onComparisonUsed={()=>complete('compare',{value:true})}/></div>
     <div className="score-grid"><div><small>Difference score</small><strong>{record.score.toFixed(4)}</strong></div><div><small>Historical review limit</small><strong>{record.threshold.toFixed(4)}</strong></div></div>
     <p className="note">A higher score means more difference from normal examples. It is not an accuracy percentage or the chance of a defect. Highlights need a human check.</p>
    </>:<div className="empty"><ScanLine size={30}/><p>The saved example opens after Run inspection.</p></div>}
   </section></div>
   {state.inspected&&<section data-practice-target="ask" className={cls('ask','card')}><h2>Evidence Assistant</h2><form onSubmit={submit('ask')}><label className="field">Question about this result<input value={state.question} maxLength={300} disabled={step.event!=='ask'} placeholder="For example: What do the highlights mean?" onChange={e=>field('question',e.target.value)}/></label><button className="primary" disabled={step.event!=='ask'||state.question.trim().length<3}>Ask</button></form>{state.answer&&<div className="cloud-message"><strong>Teaching answer · prepared text, not a live AI response</strong><p>The highlights show patches that differ from normal examples. The historical score is above this example’s review limit. Neither the score nor the highlight identifies a named defect or its cause. In normal use, the Evidence Assistant explains measurements using its retrieved references; it does not examine the photo itself.</p></div>}</section>}
   {state.answer&&<section className="card"><h2>Keep or share this result</h2><p>Personal and Team copies stay separate. Practice copies last only while this lesson is open.</p><div className="button-row"><p role="status">Private practice copy kept for this lesson. Normal signed-in inspections save automatically; online save status still needs checking.</p><button data-practice-target="share" type="button" className={cls('share','secondary')} disabled={step.event!=='share'} onClick={()=>complete('share')}>Share with team (practice)</button></div></section>}
  </>}
  {page==='history'&&<section data-practice-target="history" className={cls('history','card')}><h2>Saved inspections · practice only</h2><p>Personal Workspace · temporary lesson copy. Real private history is not displayed.</p><div className="table-wrap"><table><thead><tr><th>Inspection</th><th>Product</th><th>Result</th><th/></tr></thead><tbody><tr><td>Practice Candle</td><td>Candle</td><td>Unusual appearance</td><td><button type="button" className="text-button" onClick={()=>complete('open')}>Open inspection</button></td></tr></tbody></table></div></section>}
  {page==='team'&&<section data-practice-target="review" className={cls('review','card')}><h2>Staff review · practice only</h2><p>This is the explicitly shared lesson copy. Real Team reviews require an approved account and its authenticator check.</p><img className="guided-thumb" src={record.image_url} alt="Shared practice Candle photo"/><form className="login-form" onSubmit={submit('review')}>
   <label className="field">Review status<select value={state.reviewStatus} onChange={e=>field('reviewStatus',e.target.value)}>{['Needs review','In review','Reviewed'].map(s=><option key={s}>{s}</option>)}</select></label>
   <label className="field">Decision<select value={state.decision} onChange={e=>field('decision',e.target.value)}>{['Pending','Hold','Accept','Reject'].map(s=><option key={s}>{s}</option>)}</select></label>
   <label className="field">Review note<textarea value={state.reviewNote} maxLength={1000} onChange={e=>field('reviewNote',e.target.value)} placeholder="Describe what needs a closer check."/></label><button className="primary">Save review (practice)</button>
  </form></section>}
  {page==='cases'&&<section className="card"><h2>Corrective Actions · practice only</h2><p>Fictional assignments. No real case, access permission or notification is created.</p>
   {step.event==='case'?<form data-practice-target="case" className={cls('case','login-form')} onSubmit={submit('case')}>
    <label className="field">What needs fixing?<textarea value={state.description} maxLength={2000} onChange={e=>field('description',e.target.value)}/></label>
    <label className="field">Person responsible<select value={state.owner} onChange={e=>field('owner',e.target.value)}><option value="">Choose practice staff</option>{people.map(p=><option key={p}>{p}</option>)}</select></label>
    <label className="field">Supervisor<select value={state.supervisor} onChange={e=>field('supervisor',e.target.value)}><option value="">Choose practice staff</option>{people.map(p=><option key={p}>{p}</option>)}</select></label>
    <label className="field">Due date and time<input type="datetime-local" value={state.due} onChange={e=>field('due',e.target.value)}/></label><button type="button" className="secondary" onClick={chooseTomorrow}>Use tomorrow at noon</button>
    <label className="guided-consent"><input type="checkbox" checked={state.confirmed} onChange={e=>field('confirmed',e.target.checked)}/> The practice review confirms a defect that needs fixing.</label><button className="primary">Create corrective action (practice)</button>
   </form>:<><p><strong>Case PRACTICE-01 · {state.caseState}</strong></p><p>{state.description}</p><p>Owner: {state.owner} · Supervisor: {state.supervisor}</p>
    <form data-practice-target="progress" className={cls('progress','login-form')} onSubmit={submit(step.event)}>
     <label className="field">Case status<select value={state.caseChoice} onChange={e=>field('caseChoice',e.target.value)}><option value="">Choose next status</option>{nextCaseStates(state.caseState).map(s=><option key={s}>{s}</option>)}</select></label>
     <label className="field">What changed or was fixed?<textarea maxLength={1000} value={state.caseNote} onChange={e=>field('caseNote',e.target.value)}/></label><button className="primary">Save case update (practice)</button>
    </form><h3>Status history</h3>{state.caseHistory.map((h,i)=><p key={i}><strong>{h.state}</strong> · {h.note}</p>)}</>}
  </section>}
  {page==='batch'&&<section data-practice-target="batch" className={cls('batch','card')}><h2>Create a batch · practice only</h2><p>Check several new photos together under a distinct batch name. This lesson reuses two saved examples.</p><form className="login-form" onSubmit={submit('batch')}><label className="field">Batch label<input value={state.batchName} maxLength={80} onChange={e=>field('batchName',e.target.value)} placeholder="For example: Training batch 01"/></label><button type="button" className="secondary" onClick={()=>onAction({type:'batch-photos'})}>{state.batchPhotos?'Two sample photos selected':'Add two sample photos'}</button>{state.batchPhotos&&<div className="button-row"><img className="guided-thumb" src={record.image_url} alt="Unusual Candle batch sample"/><img className="guided-thumb" src={practiceNormal} alt="Normal Candle batch sample"/></div>}<button className="primary">Inspect batch</button></form></section>}
  {page==='alerts'&&<section data-practice-target="alert" className={cls('alert','card')}><h2>Inspections needing review · practice only</h2><p>{state.batchDone?'Practice batch finished: two saved example results. One has unusual appearance.':'An unusual practice result needs attention.'}</p><div className="alert-row"><div><strong>Unusual appearance found · Practice Candle</strong><p>Marking an alert as seen does not approve the product.</p></div><button type="button" className="secondary" onClick={()=>complete('alert')}>Mark as seen</button></div></section>}
  {page==='gallery'&&<section data-practice-target="gallery" className={cls('gallery','card')}><h2>Community gallery · public sharing</h2><p>A public copy is separate from private Personal history and authorized Team work. Publishing needs explicit permission for the photo. Visible private details within a photo can still be seen.</p><p>This lesson does not publish anything.</p><form onSubmit={submit('gallery')}><label className="guided-consent"><input type="checkbox" checked={state.publicConsent} onChange={e=>field('publicConsent',e.target.checked)}/> A gallery copy would be visible to anyone.</label><button className="primary">Continue</button></form></section>}
  {page==='overview'&&<section data-practice-target="finish" className={cls('finish','card')}><CheckCircle size={32}/><h2>Practice complete</h2><p>The lesson covered an inspection, image comparison, a teaching answer, private history, explicit Team sharing, Staff review, a corrective action through closure, batch inspection and alerts.</p><p>No real records were saved, shared, reviewed, changed or published. No AI allowance or email delivery was used. Practice data will now be discarded.</p><button type="button" className="primary" onClick={onDismiss}>Finish tutorial</button></section>}
  </>}
 </section>;
}
