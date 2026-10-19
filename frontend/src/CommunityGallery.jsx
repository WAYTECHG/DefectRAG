import React,{useEffect,useState} from 'react';

const preview=value=>'data:image/jpeg;base64,'+value;
const score=value=>typeof value==='number'?value.toFixed(5):'—';

export function PublishGalleryPanel({record,api}){
 const [state,setState]=useState(null),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;api(`/api/inspections/${record.id}/publication`).then(value=>{if(active)setState(value)}).catch(err=>{if(active)setError(err.message)});return()=>{active=false}},[record.id,api]);
 const publication=state?.publication;
 async function submit(){
  setBusy(true);setError('');
  try{
   if(publication?.visible){await api(`/api/gallery/${publication.id}/withdraw`,{method:'POST'});setState({...state,publication:{...publication,visible:false}})}
   else {const value=await api(`/api/inspections/${record.id}/publication`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consent})});setState({...state,publication:value});setConsent(false)}
  }catch(err){setError(err.message)}finally{setBusy(false)}
 }
 return <section className="card"><div className="section-title"><h2>Publish to community gallery</h2><span className="subtle-tag">OPTIONAL · PUBLIC</span></div>
  <p>Private inspection history stays in this workspace. Publishing creates a separate public copy of the image, heatmap, product category and model measurements.</p>
  <p className="caption">Names, filenames, batch labels, conversations, staff notes and review decisions are excluded. Preview metadata is removed, but visible text and identifying details inside the photograph remain visible. Publish only images permitted for public sharing.</p>
  {!state&&!error&&<p role="status">Checking gallery availability…</p>}
  {state?.enabled===false&&<p className="note">Public publishing is awaiting gallery storage setup. Inspection and private staff history continue working.</p>}
  {state?.enabled&&!publication&&<label className="field"><span style={{fontSize:14}}><input type="checkbox" style={{width:18,height:18,minHeight:18,padding:0,marginTop:0,marginRight:8,verticalAlign:"middle"}} checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/> Publish this image, heatmap and measured result publicly. Permission to share this image has been obtained.</span></label>}
  {publication&&!publication.visible&&<p role="status" className="note">This publication was withdrawn or moderated. It remains unavailable in the public gallery.</p>}
  {state?.enabled&&(!publication||publication.visible)&&<button className="secondary" disabled={busy||(!publication&&!consent)} onClick={submit}>{busy?'Saving…':publication?'Withdraw public copy':'Publish to demo gallery'}</button>}
  {publication?.visible&&<p className="caption">Published. Other visitors can browse this copy in Community gallery. Withdrawal keeps the private inspection. Downloaded or cached copies cannot be recalled.</p>}
  {error&&<p className="error" role="alert">{error}</p>}
 </section>;
}

export default function CommunityGallery({api,staff=false}){
 const [offset,setOffset]=useState(0),[revision,setRevision]=useState(0),[data,setData]=useState(null),[selected,setSelected]=useState(''),[detail,setDetail]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
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
   <p className="caption">Published snapshots contain real saved model outputs, not new inference or a community accuracy benchmark. The uploader selects the category. No expert acceptance or defect diagnosis is implied. VisA sample images: Zou et al., ECCV 2022 · CC BY 4.0.</p>
   {error&&<p className="error" role="alert">{error}</p>}
   {!data&&!error&&<p role="status">Loading public gallery…</p>}
   {data?.enabled===false&&<p className="note">The gallery is awaiting separate durable storage setup. Existing inspection features remain available.</p>}
   {data?.enabled&&<><div className="table-wrap"><table><thead><tr><th>Product</th><th>Model verdict</th><th>Score</th><th>Published</th><th>Preview</th></tr></thead><tbody>{data.items.map(item=><tr key={item.id}><td>{item.measurement.category}</td><td>{item.measurement.verdict}</td><td>{score(item.measurement.score)}</td><td>{new Date(item.created_at).toLocaleString()}</td><td><button className="text-button" disabled={busy} onClick={()=>{setError('');setSelected(item.id)}}>View image & heatmap</button></td></tr>)}</tbody></table></div>
    {!data.items.length&&<p className="empty">No published inspections on this page. Inspect an image, then choose Publish to demo gallery.</p>}
    <div className="button-row"><button className="secondary" disabled={!offset||busy} onClick={()=>{setSelected('');setOffset(value=>Math.max(0,value-12))}}>Previous</button><span>Page {Math.floor(offset/12)+1}</span><button className="secondary" disabled={data.items.length<12||offset>=96||busy} onClick={()=>{setSelected('');setOffset(value=>value+12)}}>Next</button></div>
   </>}
  </section>
  {selected&&<section className="card"><div className="section-title"><h2>Public inspection snapshot</h2><button className="text-button" disabled={busy} onClick={()=>setSelected('')}>Close preview</button></div>
   {!detail&&!error&&<p role="status">Loading image and heatmap…</p>}
   {detail&&<><div className="inspection-grid" style={{gridTemplateColumns:"repeat(auto-fit,minmax(min(100%,260px),1fr))"}}><figure style={{margin:0}}><img style={{width:'100%'}} src={preview(detail.image)} alt="Publicly shared inspection image"/><figcaption>Published image preview</figcaption></figure><figure style={{margin:0}}><img style={{width:'100%'}} src={preview(detail.heatmap)} alt="Anomaly heatmap for the published inspection"/><figcaption>Measured anomaly localization</figcaption></figure></div>
    <p><strong>{detail.measurement.category} · {detail.measurement.verdict}</strong> · Score {score(detail.measurement.score)} · Threshold {score(detail.measurement.threshold)}</p><p className="caption">{detail.measurement.model_id} · {detail.measurement.localization}<br/>The score is feature distance, not accuracy or defect probability.</p>
    <div className="button-row"><button className="secondary" disabled={busy} onClick={()=>remove(false)}>Withdraw own publication</button>{staff&&<button className="secondary" disabled={busy} onClick={()=>remove(true)}>Staff: hide publication</button>}</div>
    <p className="caption">Guest withdrawal requires the original browser workspace. Staff publishers can withdraw under the same approved account. For removal when access is lost, contact the application maintainer with public item ID: {detail.id}. Staff can hide inappropriate publications. Hidden snapshots are retained privately for moderation; they are no longer publicly served.</p>
   </>}
  </section>}
 </>;
}
