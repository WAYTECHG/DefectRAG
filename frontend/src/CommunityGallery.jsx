import {friendlyError,resultLabel} from './userLanguage.mjs';
import React,{useEffect,useState,useRef} from 'react';
import {startPolling} from './workspace.mjs';

const preview=value=>'data:image/jpeg;base64,'+value;
const score=value=>typeof value==='number'?value.toFixed(5):'—';

export function GalleryUnavailableNotice({local=false}){
 return <p className="note"><span>{local?<>
  Public sharing is not available from this computer yet. Demo results stay here. Account work stays private unless shared separately.{' '}
  <a href="https://wizzas-defectrag.hf.space/#gallery" target="_blank" rel="noreferrer">Open the online community gallery</a> to browse existing public copies. Opening it does not publish a local inspection.
 </>:'The public gallery is not available yet. Other inspection features can still be used.'}</span></p>;
}

export function PublishGalleryPanel({record,api}){
 const [state,setState]=useState(null),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const publishing=useRef(false),version=useRef(0);
 useEffect(()=>{let active=true;const poll=startPolling(async()=>{if(publishing.current)return;const generation=version.current;try{const value=await api(`/api/inspections/${record.id}/publication`);if(active&&generation===version.current){setState(value);setError('')}}catch(err){if(active&&generation===version.current)setError(err.message);throw err}});return()=>{active=false;poll.stop()}},[record.id,api]);
 const publication=state?.publication;
 async function submit(){
  if(publishing.current)return;
  publishing.current=true;version.current++;setBusy(true);setError('');
  try{
   if(publication?.visible){await api(`/api/gallery/${publication.id}/withdraw`,{method:'POST'});setState({...state,publication:{...publication,visible:false}})}
   else {const value=await api(`/api/inspections/${record.id}/publication`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consent})});setState({...state,publication:value});setConsent(false)}
  }catch(err){setError(err.message)}finally{publishing.current=false;setBusy(false)}
 }
 return <section className="card"><div className="section-title"><h2>Publish to community gallery</h2><span className="subtle-tag">OPTIONAL · PUBLIC</span></div>
  <p>Publishing lets anyone see a separate copy of the photo, highlighted areas, product type and result. Private history stays in this workspace.</p>
  <p className="caption">Names, filenames, batch names, conversations and Staff reviews are not included. Anything visible inside the photo can still be seen. Only publish photos that may be shared publicly.</p>
  {!state&&!error&&<p role="status">Checking gallery availability…</p>}
  {state?.enabled===false&&<p className="note">{state.runtime==='local'?'Public sharing is not set up on this computer. This is not caused by using the demo. Results remain saved here. The online app has its own public sharing settings.':'Public sharing is not available in this app yet. Once enabled, demo visitors can publish by choice. Private work stays separate.'}</p>}
  {state?.enabled&&!publication&&<label className="field"><span style={{fontSize:14}}><input type="checkbox" style={{width:18,height:18,minHeight:18,padding:0,marginTop:0,marginRight:8,verticalAlign:"middle"}} checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/> This photo may be shared publicly. Publish the photo, highlighted areas and result for anyone to see.</span></label>}
  {publication&&!publication.visible&&<p role="status" className="note">This publication was withdrawn or moderated. It remains unavailable in the public gallery.</p>}
  {state?.enabled&&(!publication||publication.visible)&&<button className="secondary" disabled={busy||(!publication&&!consent)} onClick={submit}>{busy?'Saving…':publication?'Withdraw public copy':'Publish to community gallery'}</button>}
  {publication?.visible&&<p className="caption">Published. Other visitors can browse this copy in Community gallery. Withdrawal keeps the private inspection. Downloaded or cached copies cannot be recalled.</p>}
  {error&&<p className="error" role="alert">{friendlyError(error)}</p>}
 </section>;
}

export default function CommunityGallery({api,staff=false,local=false}){
 const [offset,setOffset]=useState(0),[revision,setRevision]=useState(0),[data,setData]=useState(null),[selected,setSelected]=useState(''),[detail,setDetail]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const previewHeading=useRef(null),previewTrigger=useRef(null);
 useEffect(()=>{if(selected){previewHeading.current?.focus({preventScroll:true});previewHeading.current?.scrollIntoView({block:'start',behavior:'instant'})}},[selected]);
 function closePreview(){setSelected('');previewTrigger.current?.focus()}
 useEffect(()=>{
  let active=true;setData(null);setError('');
  api(`/api/gallery?offset=${offset}`).then(value=>{if(active)setData(value)}).catch(err=>{if(active)setError(err.message)});
  return()=>{active=false};
 },[api,offset,revision]);
 useEffect(()=>{
  let active=true;setDetail(null);if(!selected)return()=>{active=false};
  api(`/api/gallery/${selected}`).then(value=>{if(active)setDetail(value)}).catch(err=>{if(active)setError(err.message)});
  return()=>{active=false};
 },[api,selected,revision]);
 async function remove(moderate){
  setBusy(true);setError('');
  try{await api(`/api/gallery/${selected}/${moderate?'moderate':'withdraw'}`,{method:'POST'});setSelected('');setRevision(value=>value+1)}
  catch(err){setError(err.message)}finally{setBusy(false)}
 }
 return <>
  <section className="card"><div className="section-title"><h2>Shared by demo visitors</h2><button className="secondary" disabled={busy} onClick={()=>setRevision(value=>value+1)}>Refresh gallery</button></div>
   <p>Only explicitly published inspections appear here. Browsing requires no account. Private guest and staff histories are separate.</p>
   <p className="caption">These are saved results shared by visitors. They are not new inspections or expert product approvals. Visitors choose the product type, which may be incorrect. VisA sample images: Zou et al., ECCV 2022 · CC BY 4.0.</p>
   {error&&<p className="error" role="alert">{friendlyError(error)}</p>}
   {!data&&!error&&<p role="status">Loading public gallery…</p>}
   {data?.enabled===false&&<GalleryUnavailableNotice local={local}/>}
   {data?.enabled&&<><div className="table-wrap"><table><thead><tr><th>Product</th><th>Inspection result</th><th>Score</th><th>Published</th><th>Preview</th></tr></thead><tbody>{data.items.map(item=><tr key={item.id}><td>{item.measurement.category}</td><td>{resultLabel(item.measurement.verdict)}</td><td>{score(item.measurement.score)}</td><td>{new Date(item.created_at).toLocaleString()}</td><td><button className="text-button" disabled={busy} aria-expanded={selected===item.id} aria-controls="public-inspection-preview" onClick={event=>{previewTrigger.current=event.currentTarget;setError('');setSelected(item.id)}}>View image & heatmap</button></td></tr>)}</tbody></table></div>
    {!data.items.length&&<p className="empty">No published inspections on this page. Inspect an image, then choose Publish to community gallery.</p>}
    <div className="button-row"><button className="secondary" disabled={!offset||busy} onClick={()=>{setSelected('');setOffset(value=>Math.max(0,value-12))}}>Previous</button><span>Page {Math.floor(offset/12)+1}</span><button className="secondary" disabled={data.items.length<12||offset>=96||busy} onClick={()=>{setSelected('');setOffset(value=>value+12)}}>Next</button></div>
   </>}
  </section>
  {selected&&<section className="card" id="public-inspection-preview" aria-labelledby="public-inspection-preview-heading"><div className="section-title"><h2 ref={previewHeading} tabIndex={-1} id="public-inspection-preview-heading">Public inspection snapshot</h2><button className="text-button" disabled={busy} onClick={closePreview}>Close preview</button></div>
   {error&&<p className="error" role="alert">{friendlyError(error)} <button className="text-button" onClick={()=>{setError('');setRevision(value=>value+1)}}>Retry preview</button></p>}
   {!detail&&!error&&<p role="status">Loading image and heatmap…</p>}
   {detail&&<><div className="inspection-grid" style={{gridTemplateColumns:"repeat(auto-fit,minmax(min(100%,260px),1fr))"}}><figure style={{margin:0}}><img style={{width:'100%'}} src={preview(detail.image)} alt="Publicly shared inspection image"/><figcaption>Published image preview</figcaption></figure><figure style={{margin:0}}><img style={{width:'100%'}} src={preview(detail.heatmap)} alt="Anomaly heatmap for the published inspection"/><figcaption>Highlighted unusual areas</figcaption></figure></div>
    <p><strong>{detail.measurement.category} · {resultLabel(detail.measurement.verdict)}</strong> · Score {score(detail.measurement.score)} · Threshold {score(detail.measurement.threshold)}</p><p className="caption">{detail.measurement.model_id} · {detail.measurement.localization}<br/>A higher score means a larger difference from normal examples. It is not an accuracy percentage or the chance of a defect.</p>
    <div className="button-row"><button className="secondary" disabled={busy} onClick={()=>remove(false)}>Withdraw own publication</button>{staff&&<button className="secondary" disabled={busy} onClick={()=>remove(true)}>Staff: hide publication</button>}</div>
    <p className="caption">To remove a demo publication, use the browser that published it. Staff can remove their own publications using the same approved account. If access is lost, contact the workspace administrator with this public item number: {detail.id}. Staff can hide unsuitable publications. Hidden copies are kept privately for review and are no longer shown publicly.</p>
   </>}
  </section>}
 </>;
}
