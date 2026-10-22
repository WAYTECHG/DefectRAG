import React, { useEffect, useState, useRef, lazy, Suspense } from 'react';

import { createRoot } from 'react-dom/client';

import { LayoutDashboard, ScanLine, Layers, History, Bell, BarChart3, BookOpen, ArrowUpRight, ArrowRight, Upload, Check, Activity, ShieldCheck, X, LoaderCircle, FileText, MessageSquare, ChevronRight, CircleHelp, Download, Search, Cpu } from 'lucide-react';

import './style.css';
import './theme.css';
import InspectionViewer from './InspectionViewer.jsx';
import ArchiveDialog from './ArchiveDialog.jsx';
import BenchmarkReport from './BenchmarkReport.jsx';
import {workspaceChanged,cloudClient} from './cloud.js';
import InspectionAction from './InspectionAction.jsx';
import {inspectionReadiness,loadInspectionAccess} from './inspectionReadiness.mjs';
import {workspaceRefreshGate,readRefreshSections} from './workspaceRefresh.mjs';
import RefreshNotice from './RefreshNotice.jsx';
import LocalSyncPanel from './LocalSyncPanel.jsx';
import {configureLocalSync,localSyncEnabled,localSyncRequest} from './localSync.mjs';
import ReviewForm from './ReviewForm.jsx';
import WorkspaceShare from './WorkspaceShare.jsx';
import {activeWorkspace,configureWorkspace,personalEnabled,setWorkspace,startPolling} from './workspace.mjs';
import CommunityGallery,{PublishGalleryPanel} from './CommunityGallery.jsx';
import {createRequestScope,newBatch,continueBatch,batchView} from './workflow.mjs';
import {batchOwner,checkpointBatch,restoreBatch} from './batchCheckpoint.js';
const TeamWorkspace=lazy(()=>import('./TeamWorkspace.jsx'));

import { SHOWCASE, assetUrl, showcaseApi } from './showcase.js';




const url=assetUrl;

const labels={pcb1:'PCB 1',capsules:'Capsules',cashew:'Cashew',candle:'Candle',chewinggum:'Chewing gum',fryum:'Fryum',macaroni1:'Macaroni 1',macaroni2:'Macaroni 2',pcb2:'PCB 2',pcb3:'PCB 3',pcb4:'PCB 4',pipe_fryum:'Pipe fryum'};

const nav=[['overview','Overview',LayoutDashboard],['inspect','Image inspection',ScanLine],['batch','Batch monitoring',Layers],['history','Inspection history',History],['alerts','Review alerts',Bell],['performance','Model performance',BarChart3],['benchmark','Official benchmark',Cpu],...(!SHOWCASE?[['gallery','Community gallery',ScanLine]]:[]),['team','Staff workspace',Layers],['recovery','History recovery',History],['about','About & evidence',BookOpen]];

function pageFromLocation(fallback='overview'){
 const hash=location.hash.slice(1);
 if(/(?:^|&)(access_token|error_description|type)=/.test(hash)||new URLSearchParams(location.search).has('code'))return 'team';
 return nav.some(n=>n[0]===hash)?hash:fallback;
}

const number=(v,d=3)=>typeof v==='number'?v.toFixed(d):'—';

const percent=v=>typeof v==='number'?(v*100).toFixed(1)+'%':'—';

const date=v=>v?new Date(v).toLocaleString():'';

async function request(path,options={}) {
 if(localSyncEnabled())return localSyncRequest(url(path),options,await cloudClient(),activeWorkspace());
 return fetch(url(path),options)
}

async function api(path,options={}) {

  if(SHOWCASE) return showcaseApi(path,options);

  const response=await request(path,options);

  const body=await response.json();

  if(!response.ok) throw Object.assign(new Error(body.error?.message||'Request failed'),{status:response.status});

  return body.data;

}

 function Badge({value}) {return <span className={'badge '+value?.toLowerCase()}><i/>{value}</span>}

function Empty({children}) {return <div className="empty"><ScanLine size={30}/><p>{children}</p></div>}

 function Gallery({samples,busy,onChoose}){return <div className="gallery">{samples.map(s=><button className="sample" key={s.name} disabled={busy} onClick={()=>onChoose(s)}><img src={url(s.url)} alt={s.name.replace('_',' ')}/><div><strong>{labels[s.category]}</strong><span>{s.name.endsWith('_good')?'Normal reference sample':'Anomalous sample'} <ArrowUpRight size={14}/></span></div></button>)}</div>}

 function Filters({filter,setFilter,stats,filteredCount}){return <div className="filters"><Search size={17}/><select aria-label="Filter category" value={filter.category} onChange={e=>setFilter({...filter,category:e.target.value})}><option value="">All products</option>{Object.entries(labels).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select><select aria-label="Filter result" value={filter.verdict} onChange={e=>setFilter({...filter,verdict:e.target.value})}><option value="">All results</option>{['Good','Anomalous','Uncertain'].map(v=><option key={v}>{v}</option>)}</select><select aria-label="Filter batch" value={filter.batch} onChange={e=>setFilter({...filter,batch:e.target.value})}><option value="">All batches</option>{stats.batches.filter(b=>b.batch).map(b=><option key={b.batch}>{b.batch}</option>)}</select><button className="text-button" onClick={()=>setFilter({category:'',verdict:'',batch:''})}>Clear filters</button><span>{filteredCount} records shown</span></div>}

 function Table({rows=[],emptyMessage,hasRecords,onOpen}){return rows.length?<div className="table-wrap"><table><thead><tr><th>Inspection / time</th><th>Product</th><th>Batch</th><th>Result</th><th>Score / threshold</th><th>Inference</th><th/></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td><strong>{r.id.slice(0,8)}</strong><small>{date(r.created_at)}</small></td><td>{labels[r.category]}</td><td>{r.batch||'Individual'}</td><td><Badge value={r.verdict}/></td><td>{number(r.score)} <span className="muted">/ {number(r.threshold)}</span></td><td>{number(r.inference_ms,0)} ms</td><td><button className="icon-button" aria-label={'Open inspection '+r.id.slice(0,8)} onClick={()=>onOpen(r)}><ArrowUpRight size={18}/></button></td></tr>)}</tbody></table></div>:<Empty>{emptyMessage||(hasRecords?'No inspections match these filters. Clear the filters to see saved records.':'No inspections yet. Add an image to start your inspection log.')}</Empty>}

function App(){

 const [page,setPage]=useState(()=>pageFromLocation());
 const [official,setOfficial]=useState(null),[archived,setArchived]=useState([]),[archiveOpen,setArchiveOpen]=useState(false),[archiveBusy,setArchiveBusy]=useState(false),[sharing,setSharing]=useState(false),[notice,setNotice]=useState('');

 const [health,setHealth]=useState(null),[stats,setStats]=useState({total:0,counts:{},batches:[]}),[samples,setSamples]=useState([]),[records,setRecords]=useState([]),[alerts,setAlerts]=useState([]),[evaluation,setEvaluation]=useState(null);

 const [error,setError]=useState(''),[busy,setBusy]=useState(false),[ragBusy,setRagBusy]=useState(false),[result,setResult]=useState(null),[messages,setMessages]=useState([]);

 const [category,setCategory]=useState('pcb1'),[batch,setBatch]=useState(''),[files,setFiles]=useState([]),[preview,setPreview]=useState(''),[filter,setFilter]=useState({category:'',verdict:'',batch:''}),[question,setQuestion]=useState(''),[heatmap,setHeatmap]=useState(true),[batchResult,setBatchResult]=useState(null);

 const context=useRef(createRequestScope()),refreshContext=useRef(createRequestScope()),refreshPoll=useRef(null);
 const singleSubmission=useRef(null),artifactRefresh=useRef(0);
 const batchIdentity=useRef(null),batchLoad=useRef(0),metadataLoaded=useRef(false),batchSelection=useRef(null);
 const [signedIn,setSignedIn]=useState(false);
 const [workspace,setWorkspaceState]=useState('personal'),[workspaceStatus,setWorkspaceStatus]=useState(null),[sync,setSync]=useState({state:'refreshing'});
 function clearWorkspace(){refreshContext.current.invalidate();setRecords([]);setAlerts([]);setArchived([]);setStats({total:0,counts:{},batches:[]});setWorkspaceStatus(null);setSectionErrors(previous=>previous.filter(name=>['Connection','Samples','Performance','Benchmark'].includes(name)))}
 function changeWorkspace(value){
  const keepDraft=workspace==='team'&&value==='personal'&&!busy&&!ragBusy&&!recordLoading;
  setWorkspace(value);setWorkspaceState(value);clearWorkspace();resetInspection();
  if(!keepDraft)setFiles([]);
  setFilter({category:'',verdict:'',batch:''});
 }
 function switchToPersonalWorkspace(){if(busy||ragBusy||recordLoading)return;changeWorkspace('personal')}
 function openTeamRecord(row){if(health?.personal_workspace_enabled)changeWorkspace('team');openRecord({...row.payload,id:row.id,storage:'supabase',workspace:'team'})}
 const [batchJob,setBatchJob]=useState(null),[batchWarning,setBatchWarning]=useState('');
 const [sectionErrors,setSectionErrors]=useState([]),[review,setReview]=useState(null),[recordLoading,setRecordLoading]=useState(false);
 const [inspectionAccess,setInspectionAccess]=useState({state:'checking'}),[workspaceBlock,setWorkspaceBlock]=useState(null);
 const [localSyncStatus,setLocalSyncStatus]=useState(null);
 function currentReadiness(multiple=false,retry=false){
  return inspectionReadiness({health,workspace,access:inspectionAccess,files,categoryValid:Boolean(labels[category]),batch,multiple,retry,busy,ragBusy,recordLoading,offline:sync.state==='offline',connectionFailed:sectionErrors.includes('Connection')});
 }
 const go=p=>{setPage(p);location.hash=p;setError('')};
 function resetInspection(){
  context.current.invalidate();setBusy(false);setRagBusy(false);setRecordLoading(false);
  setResult(null);setMessages([]);setReview(null);setQuestion('');
  return context.current.capture();
 }
 async function refresh(full=false){
  refreshContext.current.invalidate();const current=refreshContext.current.capture();
  let settings=health;
  // Resolve the public routing configuration before any private request.
  // On first load activeWorkspace otherwise defaults to the legacy Team route.
  if(full||!settings){
   const metadata=[['Connection','/api/health',value=>{settings=value;setHealth(value)}],['Samples','/api/samples',setSamples],['Performance','/api/evaluation',setEvaluation],['Benchmark','/api/benchmark/official',setOfficial]];
   const read=await readRefreshSections(metadata,api,current);if(!read)return false;
   read.apply();
   const failed=read.failures.map(row=>row.name);
   setSectionErrors(previous=>[...previous.filter(name=>!metadata.some(row=>row[0]===name)),...failed]);
   metadataLoaded.current=!failed.length;
   if(failed.includes('Connection'))throw new Error('The inspection service could not be reached.');
   const changed=Boolean(settings.personal_workspace_enabled)!==personalEnabled();
   configureLocalSync(settings.local_sync_enabled);
   configureWorkspace(settings.personal_workspace_enabled);setWorkspaceState(activeWorkspace());
   if(changed){clearWorkspace();setSectionErrors(failed);return false}
  }
  let access={state:'not_required'};
  if(!SHOWCASE&&(settings?.mode==='cloud_session_workspace'||settings?.local_sync_enabled)&&settings.auth_workflow_enabled){
   try{access=await loadInspectionAccess(await cloudClient())}catch{access={state:'unavailable'}}
   if(!current())return false;
  }
  setInspectionAccess(access);
  const block=SHOWCASE?null:workspaceRefreshGate(settings,access,activeWorkspace());
  setWorkspaceBlock(block);
  if(block){
   clearWorkspace();resetInspection();setLocalSyncStatus(null);
   return {state:'blocked',reason:block.reason};
  }
  if(settings?.local_sync_enabled&&access.state==='authorized'&&activeWorkspace()==='personal'){
   try{const value=await api('/api/local-sync/run',{method:'POST'});if(!current())return false;setLocalSyncStatus(value)}
   catch{if(!current())return false;setLocalSyncStatus({state:'unavailable',message:'Cloud synchronization could not be confirmed. Local records remain saved.'})}
  }
  const requests=[['Overview','/api/stats',setStats],['History','/api/inspections?limit=500',setRecords],['Alerts','/api/alerts',setAlerts],['Recovery','/api/archives',setArchived]];
  if(!SHOWCASE&&(settings?.mode==='cloud_session_workspace'||settings?.local_sync_enabled))requests.push(['Workspace','/api/workspace',setWorkspaceStatus]);
  if(page==='inspect'&&result&&!SHOWCASE&&!busy&&!ragBusy){
   requests.push(['Selected conversation','/api/inspections/'+result.id+'/messages',setMessages],['Selected review','/api/inspections/'+result.id+'/reviews',value=>setReview(value.at(-1)||null)]);
   if(Date.now()-artifactRefresh.current>8*60*1000)requests.push(['Selected images','/api/inspections/'+result.id,value=>{artifactRefresh.current=Date.now();setResult(value)}]);
  }
  const read=await readRefreshSections(requests,api,current);if(!read)return false;
  if(read.failures.some(row=>[401,403].includes(row.status))){
   // Permission may have changed since the posture check. Never retain private
   // records or silently retry under an anonymous identity after a denial.
   clearWorkspace();resetInspection();setInspectionAccess({state:'denied'});setLocalSyncStatus(null);
   const denied={reason:'Workspace access was denied or the session expired. Open Staff workspace to check sign-in and authenticator verification.',action:'account'};
   setWorkspaceBlock(denied);return {state:'blocked',reason:denied.reason};
  }
  read.apply();
  setSectionErrors(previous=>[...previous.filter(name=>!requests.some(row=>row[0]===name)),...read.failures.map(row=>row.name)]);
  if(read.failures.length||!metadataLoaded.current)throw new Error('Some workspace data could not synchronize.');
 }
 function retryRefresh(){metadataLoaded.current=false;refreshPoll.current?.refresh()}
 async function resolveLocalConflict(inspection_id,choice){
  const current=refreshContext.current.capture();
  const value=await api('/api/local-sync/resolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inspection_id,choice})});
  if(current()){setLocalSyncStatus(value);retryRefresh()}
 }
 async function importLocalHistory(ids){
  const current=refreshContext.current.capture();
  const result=await api('/api/local-sync/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids,confirmation:'IMPORT_PRIVATE'})});
  if(current()){setLocalSyncStatus(result.status);retryRefresh()}
 }
 async function downloadLocalBackup(id){
  const current=refreshContext.current.capture();
  try{const backup=await api('/api/local-sync/backups/'+id);if(!current())return;
   const href=URL.createObjectURL(new Blob([JSON.stringify(backup,null,2)],{type:'application/json'}));
   const link=document.createElement('a');link.href=href;link.download='defectrag-private-recovery-'+id+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(href),1000);
  }catch{if(current())setError('Recovery backup could not be downloaded. Verify account access and retry.')}
 }
 async function loadBatch(){
  if(SHOWCASE)return;
  const generation=++batchLoad.current,current=context.current.capture();
  try{
   const owner=await batchOwner();const job=await restoreBatch(owner);
   if(generation!==batchLoad.current)return;
   batchIdentity.current=owner;setSignedIn(owner.startsWith('staff:'));setBatchJob(job);setBatchResult(job?batchView(job):null);
   if(job&&current()&&location.hash==='#batch'){setCategory(job.category);setBatch(job.batch)}
  }catch{if(generation===batchLoad.current)setBatchWarning('Browser batch recovery is unavailable. Keep this page open to retain pending files.')}
 }
 useEffect(()=>{const poll=startPolling(()=>refresh(!metadataLoaded.current),{onState:setSync});refreshPoll.current=poll;return()=>{poll.stop();refreshContext.current.invalidate();if(refreshPoll.current===poll)refreshPoll.current=null}},[page,workspace,health?.mode,health?.personal_workspace_enabled,health?.auth_workflow_enabled,health?.local_sync_enabled,result?.id,busy,ragBusy]);
 useEffect(()=>{if(health?.personal_workspace_enabled)loadBatch()},[health?.personal_workspace_enabled]);
 useEffect(()=>{
  loadBatch();
  const navigate=()=>setPage(current=>pageFromLocation(current));
  const update=async event=>{
   if(event.type==='defectrag-auth-change'&&event.detail.event!=='TOKEN_REFRESHED'){
    refreshContext.current.invalidate();setInspectionAccess({state:'checking'});setWorkspaceBlock(null);setLocalSyncStatus(null);
    const previous=batchIdentity.current,next=event.detail.userId?'staff:'+event.detail.userId:'browser';
    if(previous?.replace(/:personal$/,'')!==next){
     clearWorkspace();setWorkspace('personal');setWorkspaceState('personal');
     context.current.invalidate();setBusy(false);setRagBusy(false);setRecordLoading(false);
     if(next==='browser'||previous?.startsWith('staff:'))resetInspection();
     setSignedIn(next.startsWith('staff:'));setFiles([]);setBatchJob(null);setBatchResult(null);batchIdentity.current=next;loadBatch();
    }
   }
   refreshPoll.current?.refresh();
  };

  window.addEventListener('hashchange',navigate);window.addEventListener('defectrag-auth-change',update);
  return()=>{context.current.invalidate();refreshContext.current.invalidate();batchLoad.current++;window.removeEventListener('hashchange',navigate);window.removeEventListener('defectrag-auth-change',update)};
 },[]);
 useEffect(()=>{if(!files[0]){setPreview('');return}const local=URL.createObjectURL(files[0]);setPreview(local);return()=>URL.revokeObjectURL(local)},[files]);
 const filtered=records.filter(r=>(!filter.category||r.category===filter.category)&&(!filter.verdict||r.verdict===filter.verdict)&&(!filter.batch||r.batch===filter.batch));
 async function openRecord(r){
  const current=resetInspection();setCategory(r.category);setBatch(r.batch||'');setFiles([]);setRecordLoading(true);go('inspect');
  try{
   const [record,history,reviews]=await Promise.all([api('/api/inspections/'+r.id),api('/api/inspections/'+r.id+'/messages'),SHOWCASE?[]:api('/api/inspections/'+r.id+'/reviews')]);
   if(!current())return;
   setResult(record);setMessages(history);setReview(reviews.at(-1)||null);setCategory(record.category);setBatch(record.batch||'');
  }catch(e){if(current())setError(e.message)}finally{if(current())setRecordLoading(false)}
 }
 async function sampleFile(sample){
  if(busy)return;
  if(SHOWCASE){const saved=records.find(r=>r.id===sample.record_id);if(saved)await openRecord(saved);else setError('Saved example not found.');return}
  const current=resetInspection();
  try{const response=await fetch(url(sample.url));if(!response.ok)throw new Error('Sample unavailable');const blob=await response.blob();if(!current())return;setFiles([new File([blob],sample.name+'.jpg',{type:'image/jpeg'})]);setCategory(sample.category);go('inspect')}catch(e){if(current())setError(e.message)}
 }
 async function inspect(multiple=false,retry=false){
  if(busy)return;
  const readiness=currentReadiness(multiple,retry);
  if(readiness.disabled){setError(readiness.reason);return}
  if(multiple&&batchJob&&batchSelection.current===files&&batchJob.category===category&&batchJob.batch===batch.trim()){
   if(batchJob.items.every(item=>item.status==='completed')){setNotice('This batch is already complete. Select new images or a new batch label to start another batch.');return}
   retry=true;
  }
  if(!retry){
   if(!files.length){setError('Choose an image first.');return}
   if(multiple&&!batch.trim()){setError('Add a batch label so these inspections can be filtered together.');return}
   if(files.some(f=>f.size>10*1024*1024)){setError('Each image must be no larger than 10 MB.');return}
   if(files.reduce((total,f)=>total+f.size,0)>20*1024*1024){setError('Keep each batch upload under 20 MB.');return}
   if(files.length>20){setError('Inspect up to 20 files per batch.');return}
  }
  const current=resetInspection();setBusy(true);setError('');
  const send=async(file,product,label,requestId='')=>{const body=new FormData();body.append('category',product);body.append('batch',label);body.append('file',file);if(requestId)body.append('request_id',requestId);return api('/api/inspect',{method:'POST',body})};
  try{
   if(multiple){
    batchLoad.current++;
    const owner=await batchOwner();batchIdentity.current=owner;
    const job=retry?batchJob:newBatch(files,category,batch.trim());if(!retry)batchSelection.current=files;
    if(!job)throw new Error('No unfinished batch is available.');
    if(!current())return;
    setCategory(job.category);setBatch(job.batch);
    const save=async updated=>{
     try{await checkpointBatch(owner,updated)}catch{if(current())setBatchWarning('Progress is retained in this tab, but browser recovery could not be saved.')}
     if(current()){setBatchJob(updated);setBatchResult(batchView(updated))}
    };
    await save(job);await continueBatch(job,send,save,()=>current()&&batchIdentity.current===owner);
   }else{
    const previous=singleSubmission.current;
    if(!previous||previous.file!==files[0]||previous.category!==category||previous.batch!==batch)singleSubmission.current={file:files[0],category,batch,id:newBatch([files[0]],category,batch).items[0].id};
    const data=await send(files[0],category,batch,singleSubmission.current.id);if(current())setResult(data)
   }
   await refresh();
  }catch(e){if(current())setError(e.message)}finally{if(current())setBusy(false)}
 }
 async function ask(text=question){
  if(!result||ragBusy||text.trim().length<3)return;
  const current=context.current.capture(),identifier=result.id;
  setRagBusy(true);setError('');setQuestion('');
  try{const answer=await api('/api/assistant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inspection_id:identifier,question:text})});if(current())setMessages(old=>[...old,{role:'user',question:text},{role:'assistant',...answer}])}catch(e){if(current()){setError(e.message);setQuestion(text)}}finally{if(current())setRagBusy(false)}
 }
 async function exportHistory(all=false){
  try{
   const query=new URLSearchParams(all?{}:Object.fromEntries(Object.entries(filter).filter(([,value])=>value)));
   const response=await request('/api/export.csv'+(query.size?'?'+query:''));
   if(!response.ok)throw new Error('Export could not be downloaded. Refresh the workspace and try again.');
   const blob=await response.blob(),link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=all?'defectrag-all.csv':'defectrag-filtered.csv';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  }catch(e){setError(e.message)}
 }
 const heading={gallery:['PUBLIC DEMO','Explore shared inspections.','Explicitly published results from demo visitors; private staff history stays private.'],benchmark:['BENCHMARK LAB','Follow the evidence.','Official dataset splits, fixed settings, and results you can reproduce.'],team:['CONNECTED QUALITY','Better decisions, together.','Share saved inspections and review progress with approved colleagues.'],recovery:health?.personal_workspace_enabled&&workspace==='personal'?['PERSONAL RECOVERY','Recover private inspections.','Restore this account’s archived inspections, conversations and review alerts.']:['DEVELOPER WORKSPACE','Nothing important gets lost.','Restore archived local inspections, conversations and review alerts.'],overview:['INSPECTION WORKSPACE','A clearer view of quality.','Inspect products, review anomaly evidence, and keep every decision traceable.'],inspect:['VISUAL INSPECTION','From image to evidence.','Explore supported VisA products and calibrated model evidence.'],batch:['OPERATIONS','Every batch, in view.','Run a group of images and track results in one place.'],history:['INSPECTION LOG','Traceable inspection history.','Review saved measurements, localization and linked conversations.'],alerts:['REVIEW QUEUE','Give uncertainty a second look.','Anomalous and uncertain inspections create a workspace review alert.'],performance:['MODEL VALIDATION','Measured, not assumed.','Held-out performance, operating thresholds and practical limits.'],about:['SYSTEM & SOURCES','Evidence behind the answer.','Understand the model, workflow and source boundaries.']}[page]||['','',''];


 return <div className="app"><aside className="sidebar"><a className="brand" href="#overview" onClick={()=>go('overview')}><span className="brand-mark"><img src="./logo.svg" alt=""/></span><div>DefectRAG<span>INSPECTION INTELLIGENCE</span></div></a><div className="workspace-label">WORKSPACE</div><nav>{nav.map(([id,label,Icon])=><button key={id} className={page===id?'active':''} aria-current={page===id?'page':undefined} onClick={()=>go(id)}><Icon size={18}/>{label}{id==='alerts'&&alerts.some(a=>!a.acknowledged)&&<span className="nav-count">{alerts.filter(a=>!a.acknowledged).length}</span>}</button>)}</nav><div className="sidebar-bottom"><div className="local-card"><span className={'status-dot '+(!health||['offline','stale'].includes(sync.state)?'offline':'')}/><strong>{SHOWCASE?'Saved example showcase':health?(sync.state==='offline'?'Workspace offline':sync.state==='stale'?'Workspace data stale':'Workspace online'):'Connecting to workspace'}</strong><p>{SHOWCASE?'Read-only public showcase':(signedIn?(health?.personal_workspace_enabled?(page==='team'||workspace==='team'?'Team · shared Supabase':'Personal · private Supabase'):'Team · shared Supabase'):health?.mode==='cloud_session_workspace'?'Temporary browser workspace':'Private local workspace')}<br/>DINOv2 / DINOv3 · VisA</p></div><div className="sidebar-foot"><ShieldCheck size={15}/> Evidence before action.</div></div></aside>

 <main><div className="topbar"><span>Workspace <ChevronRight size={13}/> {nav.find(n=>n[0]===page)?.[1]}</span><div><span className="environment"><span className="status-dot"/> {SHOWCASE?'SAVED EXAMPLES':'LOCAL DEVELOPMENT'}</span><span className="avatar" role="img" aria-label="Quality control workspace" title="Quality control workspace"><ScanLine size={16} aria-hidden="true"/></span></div></div><div className="content" key={page}><RefreshNotice errors={sectionErrors} block={workspaceBlock} refreshing={sync.state==='refreshing'} onRetry={retryRefresh} onAccount={()=>go('team')} onPersonal={switchToPersonalWorkspace} showAccess={['overview','inspect','batch','history','alerts','recovery'].includes(page)}/><header className="page-heading"><div><p className="eyebrow">{heading[0]}</p><h1>{heading[1]}</h1><p>{heading[2]}</p></div>{page!=='inspect'&&<button className="primary" onClick={()=>{if(health?.personal_workspace_enabled)changeWorkspace('personal');resetInspection();setFiles([]);go('inspect')}}><ScanLine size={17}/> {SHOWCASE?'Browse examples':'New inspection'}</button>}</header>

 {!SHOWCASE&&(health?.mode==='cloud_session_workspace'||health?.local_sync_enabled)&&<section className="note" role="status"><div><strong>{page==='team'?'Team Workspace · explicitly shared staff records':signedIn&&!workspaceStatus?'Account access not verified · cloud synchronization unavailable':signedIn?(health.personal_workspace_enabled?(workspace==='personal'?'Personal Workspace · owner-only cloud history':'Team Workspace · explicitly shared staff records'):'Team Workspace · shared cloud history'):(health.local_sync_enabled?'Local Workspace · unassigned history stays on this device':'Guest Workspace · isolated temporary history')}</strong><p>{sync.state==='synced'?'Synchronized at '+new Date(sync.at).toLocaleTimeString():sync.state==='offline'?'Offline · displayed data may be stale':sync.state==='stale'?'Synchronization failed · displayed data may be stale':sync.state==='blocked'?'Workspace records paused · account action required':'Refreshing workspace…'} · Public gallery counts are separate.</p>{signedIn&&health.personal_workspace_enabled&&page!=='team'&&<label>Data source <select aria-label="Inspection data source" value={workspace} disabled={busy||ragBusy||recordLoading} onChange={e=>changeWorkspace(e.target.value)}><option value="personal">Personal Workspace</option><option value="team">Team Workspace</option></select></label>}{health.personal_workspace_enabled&&workspace==='team'&&<p>New inspections belong in Personal Workspace. Share with staff only after reviewing the result.</p>}</div></section>}

 {health?.local_sync_enabled&&workspace==='personal'&&<LocalSyncPanel key={batchIdentity.current||'browser'} status={localSyncStatus} onRetry={retryRefresh} onResolve={resolveLocalConflict} onBackup={downloadLocalBackup} onListImports={()=>api('/api/local-sync/importable')} onImport={importLocalHistory} canImport={inspectionAccess.state==='authorized'} refreshing={sync.state==='refreshing'}/>}

 {SHOWCASE&&<div className="showcase-banner" role="note"><BookOpen size={21}/><div><strong>Public showcase · saved real results</strong><p>These saved examples retain their original DINOv3 measurements. The Benchmark page compares the newer DINOv2 profile. No live model or chat runs on this static site; run the local app for new inspections.</p></div></div>}

 {notice&&<div className="success" role="status"><Check size={18}/><span>{notice}</span><button className="icon-button" aria-label="Dismiss notice" onClick={()=>setNotice('')}><X size={16}/></button></div>}
 {error&&<div role="alert" className="error"><CircleHelp size={18}/><span>{error}</span><button aria-label="Dismiss error" onClick={()=>setError('')}><X size={17}/></button></div>}

 {page==='gallery'&&!SHOWCASE&&<CommunityGallery api={api} staff={Boolean(workspaceStatus?.role)}/>}

 {page==='overview'&&<><div className="stats-grid">{[[stats.total,'Total inspections',SHOWCASE?'Previously measured examples':(health?.mode==='cloud_session_workspace'?'Saved in the selected workspace':'Saved in your local log'),ScanLine,'teal'],[stats.counts.Good||0,'Good','Below the review band',ShieldCheck,'green'],[stats.counts.Anomalous||0,'Anomalous','Appearance anomaly flagged',Activity,'orange'],[stats.counts.Uncertain||0,'Uncertain','Near the decision threshold',CircleHelp,'amber']].map(([n,t,s,Icon,color])=><section className="stat card" key={t}><div><span>{t}</span><Icon size={19} className={color}/></div><strong>{n.toLocaleString()}</strong><small>{s}</small></section>)}</div><div className="overview-grid"><section className="hero-card"><span className="pill"><Cpu size={14}/> {SHOWCASE?'SAVED REAL INFERENCE':'RUNS LOCALLY'}</span><h2>Turn a product image<br/>into a traceable inspection.</h2><p>Get an anomaly score, see where the model found differences, and explore the supporting evidence.</p><button className="primary light" onClick={()=>go('inspect')}>{SHOWCASE?'Explore saved examples':'Inspect an image'} <ArrowRight size={17}/></button><div className="scan-visual"><div className="scan-corner"/>{samples[0]&&<img src={url(samples[0].url)} alt="VisA product sample"/>}<span><span className="status-dot"/> VISUAL ANOMALY SCREENING</span></div></section><section className="card readiness"><div className="section-title"><h2>Inspection pipeline</h2><span className="subtle-tag">{Object.keys(evaluation?.categories||{}).length} evaluated categories</span></div>{[['Visual model','Frozen visual encoder + normal memory bank'],['Decision threshold','Calibrated on separate validation images'],['Evidence workflow','LangChain retrieval + LangGraph'],['Local generation','Qwen via Ollama; retrieval fallback']].map(([t,s],i)=><div className="pipeline-step" key={t}><span>{String(i+1).padStart(2,'0')}</span><div><strong>{t}</strong><p>{s}</p></div></div>)}<div className="note"><CircleHelp size={16}/> Benchmark screening. Review evidence before making a product decision.</div></section></div><section className="card"><div className="section-title"><div><h2>Recent inspections</h2><p>{SHOWCASE?'Recorded during local verification':'Latest saved measurements'}</p></div><button className="text-button" onClick={()=>go('history')}>View history <ArrowRight size={15}/></button></div><Table onOpen={openRecord} hasRecords={records.length>0} rows={records.slice(0,5)}/></section><section><div className="section-title"><div><h2>Explore with a sample</h2><p>VisA images · Zou et al., ECCV 2022 · CC BY 4.0 · resized previews</p></div></div><Gallery samples={samples} busy={busy} onChoose={sampleFile}/></section></>}

 {(page==='inspect'||page==='batch')&&<><div className="inspection-grid"><section className="card upload-card">{SHOWCASE?<><div className="section-title"><h2>Choose a saved inspection</h2><span className="subtle-tag">READ ONLY</span></div><p className="muted">These original images and results come from completed local model verification. Select any example to view its measured heatmap and recorded conversation.</p><Gallery samples={samples} busy={busy} onChoose={sampleFile}/><p className="caption">Batch monitoring below shows the same saved examples. New uploads and batch processing are available in the local app.</p></>:<><div className="section-title"><h2>{page==='batch'?'Create a batch':'Inspection input'}</h2><span className="subtle-tag">01 / INPUT</span></div><label className="field">Product category<select value={category} onChange={e=>{resetInspection();setCategory(e.target.value)}} disabled={busy}>{Object.entries(labels).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label><label className="field">Batch label <span>{page==='inspect'?'optional':'required'}</span><input placeholder="e.g. PCB-LINE-01" value={batch} maxLength={80} onChange={e=>setBatch(e.target.value)}/></label><label className="drop-zone">{preview?<img src={preview} alt="Selected upload preview"/>:<Upload size={29}/>}<strong>{files.length?`${files.length} image${files.length>1?'s':''} selected`:'Choose an image'+(page==='batch'?' group':'')}</strong><span>JPEG, PNG or WebP · up to 10 MB each</span><input aria-label="Upload inspection images" type="file" accept="image/jpeg,image/png,image/webp" multiple={page==='batch'} disabled={busy} onChange={e=>{resetInspection();setFiles(Array.from(e.target.files||[]))}}/></label><p className="caption">Use images of the selected product. Arbitrary images are outside the validated model scope.</p><InspectionAction readiness={currentReadiness(page==='batch')} busy={busy} multiple={page==='batch'} onRun={()=>inspect(page==='batch')} onSwitch={switchToPersonalWorkspace} switchDisabled={busy||ragBusy||recordLoading}/><p className="caption">{health?.personal_workspace_enabled?(signedIn?'New results save privately to Personal Workspace. Team/gallery sharing requires a separate action.':(health?.local_sync_enabled?'Local-only results are saved on this device until explicitly imported.':'Guest results are temporary and private to this browser workspace.')):'Local inference · images stay on this device'}</p></>}</section><section className="card result-card"><div className="section-title"><h2>{page==='batch'?'Batch run':'Inspection result'}</h2><span className="subtle-tag">02 / EVIDENCE</span></div>{recordLoading?<div className="empty" role="status"><LoaderCircle className="spin" size={32}/><p>Loading saved inspection and evidence…</p></div>:busy&&page!=='batch'?<div className="empty"><LoaderCircle className="spin" size={32}/><h3>Comparing with normal reference features</h3><p>The first request also loads the local encoder.</p></div>:page==='batch'?batchResult?<><div className="batch-summary"><h3>{batchResult.batch}</h3><p>{batchResult.records.length} completed · {batchResult.errors.length} unfinished</p></div>{batchResult.errors.map((e,i)=><div key={i} className={e.status&&e.status!=='failed'?'note':'error'}>{e.filename}: {e.message}</div>)}<Table onOpen={openRecord} hasRecords={records.length>0} rows={batchResult.records} emptyMessage="No batch images have completed yet."/>{batchJob&&<><p className="caption" role="status">{busy?'Processing one image at a time. Completed images are kept.':'Batch recovery uses this browser and account; pending image files are retained locally. Completed uploads are removed from the resume copy.'} {batchJob.items.filter(i=>i.status==='running').map(i=>'Inspecting '+i.filename).join('')}</p>{batchJob.items.some(i=>i.status!=='completed')&&<button className="primary" disabled={busy} onClick={()=>inspect(true,true)}>Retry failed / pending images only</button>}</>}{batchWarning&&<p className="error" role="alert">{batchWarning}</p>}</>:<Empty>{SHOWCASE?'Browse the saved batch in the table below, or select an example.':'Choose a product, label the batch and select up to 20 images.'}</Empty>:result?<>{evaluation?.categories?.[result.category]?.metrics?.image_auroc<0.6&&<div className="error">Weak measured benchmark separation for this category. Treat the verdict as an experimental result requiring human review.</div>}<div className="result-banner"><div><Badge value={result.verdict}/><h2>{result.verdict==='Good'?'Within normal appearance':result.verdict==='Anomalous'?'Appearance anomaly flagged':'A closer review is needed'}</h2><p>{labels[result.category]} · {result.id.slice(0,8)} · {number(result.inference_ms,0)} ms · {result.model_id?.startsWith('dinov2')?'DINOv2 high resolution':'Original DINOv3 profile'}</p></div><div className="button-row">{!SHOWCASE&&<WorkspaceShare key={result.id+workspace} record={result} messages={messages} url={url} api={api} enabled={health?.personal_workspace_enabled} onNotice={setNotice} onChanged={()=>openRecord(result)}/>}<a className="secondary" href={url(result.report_url||`/api/inspections/${result.id}/report`)} target="_blank" rel="noreferrer"><FileText size={16}/> Report</a></div></div><div className="image-toolbar"><span>{heatmap?'Anomaly localization overlay':'Uploaded image'}</span><button className="text-button" onClick={()=>setHeatmap(!heatmap)}>{heatmap?'Show original':'Show heatmap'}</button></div><InspectionViewer record={result} url={url} heatmap={heatmap}/><div className="score-grid"><div><small>Anomaly score</small><strong>{number(result.score,4)}</strong></div><div><small>Validated threshold</small><strong>{number(result.threshold,4)}</strong></div><div><small>Review band</small><strong>±{number(result.uncertainty_margin,4)}</strong></div></div><div className="note"><CircleHelp size={16}/> Scores are distances, not probabilities. The heatmap shows feature differences; it does not name a defect.</div></>:<Empty>Measured results and heatmaps appear here after inspection.</Empty>}</section></div>

 {page==='inspect'&&result&&!SHOWCASE&&<section className="card"><ReviewForm key={result.id+String(review?.created_at)} current={review} onSave={async value=>{const current=context.current.capture();const saved=await api('/api/inspections/'+result.id+'/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});if(current()){setReview(saved);setNotice('Human review saved separately from model measurements.')}workspaceChanged();await refresh()}}/></section>}
 {page==='inspect'&&result&&<section className="card assistant"><div className="section-title"><div><h2><MessageSquare size={19}/> Evidence Assistant</h2><p>Linked to inspection {result.id.slice(0,8)} · image measurements stay separate from documentation</p></div><span className="subtle-tag">LANGCHAIN + LANGGRAPH</span></div><div className="observation"><strong>IMAGE MEASUREMENTS</strong><span>{result.verdict} · score {number(result.score,4)} · threshold {number(result.threshold,4)} · {labels[result.category]}</span></div>{!SHOWCASE&&<div className="suggestions">{[result.verdict==='Good'?'Is this image normal?':'Is this image anomalous?','Does the score mean accuracy?','What does the heatmap show?','Explain this result and its limits.'].map(q=><button key={q} onClick={()=>ask(q)} disabled={ragBusy}>{q}<ArrowUpRight size={14}/></button>)}</div>}<div className="conversation">{messages.map((m,i)=>m.role==='user'?<div key={i} className="user-message"><strong>Inspection question</strong><p>{m.question}</p></div>:<div key={i} className="assistant-message"><div><strong>Evidence Assistant</strong><span className="subtle-tag">{m.mode==='llm'?(SHOWCASE?'RECORDED LLM \u00b7 CITED':'LOCAL LLM · CITED'):m.mode==='measurement_only'?'SAVED MEASUREMENTS':m.mode==='retrieval_only'?'RETRIEVAL ONLY':'ABSTAINED'}</span></div><p className="answer-text">{m.answer}</p>{m.error&&<p className="caption">{m.error}</p>}{m.evidence?.length>0&&<details><summary>{m.evidence.length} retrieved source passages</summary>{m.evidence.map(s=><article className="source" key={s.chunk_id}><strong>{s.chunk_id} · {s.title}</strong><p>{s.text}</p><small>{s.scope}</small>{s.url.startsWith('https://')&&<a href={s.url} target="_blank" rel="noreferrer">Open source <ArrowUpRight size={12}/></a>}</article>)}</details>}<details className="workflow-details"><summary>How this answer was built</summary><p>Inspection facts come from the saved model run. Document explanations use retrieved passages. Measurement-only answers do not call the language model.</p><small className="trace">{m.trace?.join(' → ')}</small></details></div>)}</div>{ragBusy&&<p role="status" className="generating"><LoaderCircle size={17} className="spin"/> Retrieving evidence and validating a local answer…</p>}<form className="question-form" onSubmit={e=>{e.preventDefault();ask()}}><input aria-label="Ask a follow-up question" placeholder={SHOWCASE?'Saved conversation only - run locally to ask new questions':'Ask about this inspection or the supporting evidence…'} value={question} maxLength={1200} onChange={e=>setQuestion(e.target.value)} disabled={ragBusy||SHOWCASE}/><button className="primary" disabled={SHOWCASE||ragBusy||question.trim().length<3}>Ask <ArrowRight size={16}/></button></form><p className="caption">{SHOWCASE&&'Previously recorded Qwen answers, not a live chat. Some examples have no saved conversation. '}The assistant receives the saved inspection ID, score, threshold, verdict and conversation. It does not visually inspect your image. Source quotes and IDs are checked. Citation checks do not guarantee that every generated interpretation is correct.</p></section>}

 {page==='inspect'&&result&&!SHOWCASE&&<PublishGalleryPanel key={result.id+workspace} record={result} api={api}/>}

 {page==='inspect'&&!result&&<section><div className="section-title"><div><h2>Or start with a VisA sample</h2><p>CC BY 4.0 · resized previews; predictions may differ slightly from original-resolution evaluation</p></div></div><Gallery samples={samples} busy={busy} onChoose={sampleFile}/></section>}

 {page==='batch'&&<section className="card"><div className="section-title"><h2>Batch history</h2><span className="subtle-tag">{stats.batches.filter(b=>b.batch).length} named batches</span></div><Filters filter={filter} setFilter={setFilter} stats={stats} filteredCount={filtered.length}/><Table rows={filtered} onOpen={openRecord} hasRecords={records.length>0}/></section>}</>}

 {page==='history'&&<section className="card"><div className="section-title"><h2>Saved inspections</h2><div className="button-row">{!SHOWCASE&&<button className="secondary danger" onClick={()=>setArchiveOpen(true)}>Clear history</button>}{SHOWCASE?<a className="secondary" href={url('/api/export.csv')}><Download size={15}/> Export CSV</a>:<><button className="secondary" onClick={()=>exportHistory()}><Download size={15}/> Export filtered CSV</button><button className="text-button" onClick={()=>exportHistory(true)}>Export all CSV</button></>}</div></div><Filters filter={filter} setFilter={setFilter} stats={stats} filteredCount={filtered.length}/><Table rows={filtered} onOpen={openRecord} hasRecords={records.length>0}/><p className="caption table-caption">{SHOWCASE?'Saved verification examples. CSV exports the same saved measurements.':'Showing up to the latest 500 records. The API supports pagination; CSV exports up to 10,000.'}</p></section>}

 {page==='alerts'&&<section className="card"><div className="section-title"><h2>{SHOWCASE?'Saved review alerts':'Local review queue'}</h2><span>{alerts.filter(a=>!a.acknowledged).length} awaiting acknowledgement</span></div>{alerts.length?alerts.map(a=><div className="alert-row" key={a.id}><Bell size={19}/><div><strong>{a.kind==='Anomalous'?'Anomaly flagged':'Uncertain screening result'}</strong><p>{a.inspection_id.slice(0,8)} · {date(a.created_at)}</p></div><Badge value={a.kind}/><button className="secondary" disabled={SHOWCASE||Boolean(a.acknowledged)} onClick={async()=>{try{await api('/api/alerts/'+a.id+'/acknowledge',{method:'POST'});workspaceChanged();await refresh()}catch(e){setError(e.message)}}}>{SHOWCASE?'Saved alert':a.acknowledged?<><Check size={15}/> Acknowledged</>:'Acknowledge'}</button><button className="icon-button" aria-label="View alerted inspection" onClick={()=>{const r=records.find(r=>r.id===a.inspection_id);if(r)openRecord(r);else api('/api/inspections/'+a.inspection_id).then(openRecord).catch(e=>setError(e.message))}}><ArrowUpRight size={18}/></button></div>):<Empty>No review alerts. Alerts are created by real anomalous or uncertain inspections.</Empty>}<div className="note"><CircleHelp size={16}/> Acknowledgement records that the alert was seen; it does not change the model result. External notifications are not enabled. Cloud alert lists show up to the latest 1,000 active inspections; dashboard totals use the selected workspace.</div></section>}

 {page==='benchmark'&&<BenchmarkReport report={official} labels={labels}/>}
 {page==='team'&&<Suspense fallback={<div className="empty"><LoaderCircle className="spin" size={28}/>Loading staff workspace…</div>}><TeamWorkspace onOpenInspection={!SHOWCASE&&health?.mode==='cloud_session_workspace'?openTeamRecord:undefined}/></Suspense>}
 {page==='recovery'&&<section className="card"><div className="section-title"><div><h2>Archived local inspections</h2><p>Recovery preserves the original measurement, images, conversation and alerts.</p></div><span className="subtle-tag">{archived.length} archived</span></div>{SHOWCASE?<Empty>Saved showcase records cannot be archived. Cloud developers recover staff records in Staff workspace.</Empty>:archived.length?<div className="table-wrap"><table><thead><tr><th>Inspection</th><th>Product</th><th>Result</th><th>Saved</th><th/></tr></thead><tbody>{archived.map(r=><tr key={r.id}><td>{r.id.slice(0,8)}</td><td>{labels[r.category]}</td><td><Badge value={r.verdict}/></td><td>{date(r.created_at)}</td><td><button className="secondary" onClick={async()=>{try{await api('/api/history/restore',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[r.id]})});workspaceChanged();await refresh();setNotice('Inspection restored to active history.')}catch(e){setError(e.message)}}}>Restore inspection</button></td></tr>)}</tbody></table></div>:<Empty>No archived local inspections. Clear history moves records here without deleting their files.</Empty>}<p className="caption">{health?.personal_workspace_enabled?(workspace==='personal'?'Personal recovery restores only records owned by this account.':'Team recovery is restricted to developers.'):'This recovery page controls the local single-user workspace. Cloud recovery is separately restricted to the developer role.'}</p></section>}
 {page==='performance'&&<><div className="note standalone"><ShieldCheck size={20}/><div><strong>Active model · evaluation protocol</strong><p>{evaluation?.protocol||'Evaluation results are not available.'}</p></div></div><section className="card"><div className="section-title"><div><h2>Retrospective image performance</h2><p>Binary metrics use the versioned decision threshold. The dashboard also applies a ±5% review band. Precision measures correct anomaly flags; recall measures anomaly coverage. High precision with low recall means many annotated anomalies are missed. AUROC measures ranking across thresholds, not recall at this operating point.</p>{evaluation?.decision_policy&&<p className="caption">Sensitivity policy: {evaluation.decision_policy==='macaroni-recall-v1'?'Macaroni 1/2 normal 80th percentile; other products normal 95th percentile.':'Held-out normal 95th percentile.'} Mean recall {percent(evaluation.macro_mean.recall)} · precision {percent(evaluation.macro_mean.precision)} · normal false-alarm rate {percent(evaluation.macro_mean.false_positive_rate)}. More anomalies are caught with more review alerts. Historical inspections retain their original thresholds; future rates may differ. {evaluation.decision_policy==='macaroni-recall-v1'&&'Macaroni 1/2 falsely flag 24%/28% of normal benchmark images; review workload is substantially higher.'}</p>}</div><span className="subtle-tag">REAL PREDICTIONS</span></div><div className="table-wrap"><table><thead><tr><th>Product</th><th>Images</th><th>AUROC</th><th>Avg. precision</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>{Object.entries(evaluation?.categories||{}).map(([k,c])=><tr key={k}><td><strong>{labels[k]}</strong></td><td>{c.metrics.n_images}</td>{['image_auroc','average_precision','precision','recall','f1'].map(key=><td key={key}>{number(c.metrics[key])}</td>)}</tr>)}</tbody></table></div></section><div className="performance-grid">{Object.entries(evaluation?.categories||{}).map(([k,c])=><section className="card" key={k}><div className="section-title"><h2>{labels[k]}</h2><span className="subtle-tag">{c.train_normal_count} NORMAL FIT</span></div><p className="muted">Confusion matrix · true rows / predicted columns</p><div className="matrix"><span/><small>Good</small><small>Anomalous</small><small>Good</small>{c.metrics.confusion_matrix[0].map((n,i)=><b key={i} className={i===0?'correct':''}>{n}</b>)}<small>Anomalous</small>{c.metrics.confusion_matrix[1].map((n,i)=><b key={i} className={i===1?'correct':''}>{n}</b>)}</div><dl>{[['Decision threshold',number(c.threshold,4)],[c.profile?'Pixel AUROC · 224 × 224':'Pixel AUROC · 64 × 64',number(c.metrics.pixel_auroc_224 ?? c.metrics.pixel_auroc_64)],['Pixel average precision',number(c.metrics.pixel_average_precision_224 ?? c.metrics.pixel_average_precision_64)],['Review band coverage',percent(c.metrics.uncertain_fraction)],['Median model inference',(c.metrics.latency_median_ms==null&&!evaluation?.serving_profile?.categories?.[k]?'Not profiled':number(evaluation?.serving_profile?.categories?.[k]?.core_median_ms ?? c.metrics.latency_median_ms,0)+' ms')],['Peak PyTorch GPU allocation',(c.metrics.peak_gpu_mb==null&&!evaluation?.serving_profile?.categories?.[k]?'Not profiled':number(evaluation?.serving_profile?.categories?.[k]?.peak_torch_allocated_gpu_mb ?? c.metrics.peak_gpu_mb,1)+' MB')],['Normal bank size',(c.bank_size_bytes/1024**2).toFixed(1)+' MB']].map(([name,v])=><div key={name}><dt>{name}</dt><dd>{v}</dd></div>)}</dl></section>)}</div><div className="note"><CircleHelp size={17}/><p>Frozen nearest-normal memory, not Dinomaly. Performance varies by category; inspect image and pixel metrics separately. No supervised defect-type classifier or factory acceptance claim. Core latency excludes image decoding and heatmap rendering. Historical clean serving measurements apply only to their original model profile. GPU allocation excludes other processes and driver memory.</p></div></>}

 {page==='about'&&<><div className="overview-grid"><section className="card about"><h2>DefectRAG</h2><p>An industrial anomaly inspection application combining real visual inference, persistent history and retrieval-augmented generation (RAG).</p><h3>What the model measures</h3><p>Frozen visual encoders produce spatial patch embeddings: DINOv3 in the original profile, DINOv2 at higher resolution in the optional accuracy profile. A category-specific normal memory bank returns cosine distances. Validation selects the decision threshold; no specific defect class is predicted.</p><h3>What the assistant knows</h3><p>Retrieval-augmented generation (RAG) connects inspection-linked questions to attributed documents. BGE embeddings retrieve relevant passages; LangGraph routes questions, validates evidence, calls Qwen, and checks source IDs and supporting quotes. Saved measurements remain separate from generated explanations.</p><h3>Privacy and deployment</h3><p>{SHOWCASE?'This static showcase publishes 25 saved VisA examples across 12 categories and saved evidence. It performs no live inference or chat. The separate Staff workspace can connect to Supabase for authenticated shared history. Live features are available in the separate local application.':'This build is a single-user local workspace. A separate free static showcase is included. Public live inference requires an isolated API and per-user storage.'}</p></section><section className="card about"><h2>Source library</h2>{[['DINOv2 encoder','Meta · Apache-2.0','https://github.com/facebookresearch/dinov2'],['Qwen3 text generation','Qwen Team · Apache-2.0','https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507'],['VisA dataset','Amazon Science · CC BY 4.0','https://github.com/amazon-science/spot-diff'],['DINOv3 encoder','Meta · DINOv3 license','https://github.com/facebookresearch/dinov3'],['Anomalib Dinomaly','Intel / Open Edge Platform · model documentation','https://anomalib.readthedocs.io/en/lib-v2.6.2/markdown/guides/reference/models/image/dinomaly.html'],['BGE small embeddings','BAAI · MIT','https://huggingface.co/BAAI/bge-small-en-v1.5']].map(([t,s,href])=><a className="source-link" key={t} href={href} target="_blank" rel="noreferrer"><div><strong>{t}</strong><small>{s}</small></div><ArrowUpRight size={17}/></a>)}<div className="note"><BookOpen size={17}/> Application guidance describes benchmark screening and evidence limits. Factory standard operating procedures (SOPs), acceptance limits and repair instructions are not included.</div><h3>Runtime</h3><p>FastAPI · React + Vite · SQLite<br/>PyTorch · Transformers · LangChain · LangGraph<br/>RAG · BGE retrieval · cited generation<br/>Ollama / Qwen 2.5 3B</p></section></div></>}

 <ArchiveDialog scope={health?.mode==='cloud_session_workspace'?(signedIn?(health.personal_workspace_enabled?workspace:'team'):'guest'):'local'} open={archiveOpen} onClose={()=>setArchiveOpen(false)} busy={archiveBusy} onConfirm={async()=>{setArchiveBusy(true);try{const archived=await api('/api/history/archive',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...filter,confirmation:'ARCHIVE'})});workspaceChanged();await refresh();setArchiveOpen(false);setNotice(`${archived.archived} inspections archived. Restore them in History recovery.`)}catch(e){setError(e.message)}finally{setArchiveBusy(false)}}}/>
 <footer>DefectRAG <span>{SHOWCASE?'Saved example showcase · no live inference':'Inspection & evidence workspace'}</span><span>Benchmark screening · human review where needed</span></footer></div></main></div>

}

createRoot(document.getElementById('root')).render(<App/>);
