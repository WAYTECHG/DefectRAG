import React,{useState} from 'react';
import {Copy,Check} from 'lucide-react';
import {build,diagnosticReport,recentIssues} from './diagnostics.mjs';

// Support details are copied only when the person presses the button. They hold
// the app version, page and recent error messages: never passwords, emails or photos.
function SupportBox({context}){
 const [state,setState]=useState('idle');
 async function copy(){
  try{await navigator.clipboard.writeText(diagnosticReport(context||{}));setState('copied')}catch{setState('failed')}
 }
 const count=recentIssues().length;
 return <div className="support-box">
  <h3>If something is not working</h3>
  <ul className="fix-list">
   <li><strong>“Starting” or “busy” message?</strong> Wait a minute, then press <em>Retry refresh</em>.</li>
   <li><strong>Page looks old?</strong> Reload it (Ctrl + F5 on a computer, pull down on a phone).</li>
   <li><strong>Still stuck?</strong> Copy the details below and send them to the administrator.</li>
  </ul>
  <p>Read the message beside the button first. It says what to do next. “Mark as seen” only records that an alert was noticed; it does not approve the product.</p>
  <div className="button-row"><button type="button" className="secondary" onClick={copy}>{state==='copied'?<Check size={16}/>:<Copy size={16}/>} {state==='copied'?'Details copied':'Copy details for support'}</button></div>
  {state==='failed'&&<p className="caption" role="alert">Copying is blocked in this browser. Take a screenshot of this page instead.</p>}
  <p className="caption">Version {build.version} · build {build.commit}{build.built?' · '+build.built:''} · {count} recent problem{count===1?'':'s'} recorded in this tab. No passwords, emails or photos are included.</p>
 </div>;
}

export default function StaffHelp({health,showcase=false,context}){
 const online=health?.mode==='cloud_session_workspace';
 return <div className="overview-grid"><section className="card about">
  <h2>Using DefectRAG</h2><p>The app helps you screen photos. Your workplace rules still decide what is accepted.</p>
  <h3>1. Start an inspection</h3><p>Pick <strong>Image inspection</strong> for one photo, or <strong>Batch inspection</strong> for up to 20. Choose the product, add clear photos, then press Run.</p>
  <h3>2. Check the result</h3><p><strong>Looks normal</strong> means nothing was flagged. <strong>Unusual appearance</strong> or <strong>Needs a closer look</strong> means a person should check. Compare the photo with the highlighted areas. The score is not a chance of defect.</p>
  <h3>3. Keep work private or share it</h3><p>Personal workspace is private to you. Press <strong>Share with team</strong> to give your team a copy.</p>
  <h3>4. Review shared work</h3><p>Go to Inspection history, pick Team workspace, then press Review. Save your decision. If a real defect needs fixing, choose <strong>Reviewed</strong> and <strong>Reject</strong>.</p>
  <h3>5. Track a corrective action</h3><p>Open <strong>Corrective Actions</strong>. Pick an inspection marked Ready. Choose who fixes it, a supervisor and a deadline. Tick the box and press Create. Press Details on a case to see its progress.</p>
  <h3>Sign-in help</h3><p>New Staff: create an account, confirm your email, sign in and request access. A Developer approves it. Then enter the six-digit security code from your authenticator app. Password reset does not remove this check. Lost your authenticator? Ask the administrator.</p>
 </section><section className="card about">
  <h2>Saving and privacy</h2>
  <p>{showcase?'This version shows saved examples only. It does not check new photos or provide a live assistant.':online?'The online app saves approved account work privately online. Without sign-in, demo results belong to this browser session and may disappear when the app restarts.':'Without sign-in, work stays on this computer. With approved sign-in and a security code, Personal work can also be saved online. Check saved changes to see whether anything is still waiting.'}</p>
  <p>To use private work on another device, sign in with the same account and complete its security check there. Sharing with the team is always separate. Personal notes and later conversations are not added to a Team copy automatically.</p>
  <h3>If changes were made in two places</h3><p>The app keeps both copies for review. Compare saved changes before choosing which copy to use. Do not assume that a change waiting on this computer has already reached the online account.</p>
  <h3>Understanding the assistant</h3><p>Ask about the saved result, highlighted areas or supporting information. The assistant reads saved measurements and references; it does not examine the photo itself. Open supporting references and check important answers. The app does not provide factory repair instructions or replace workplace procedures.</p>
  <SupportBox context={context}/>
  <details className="workflow-details"><summary>Technical background and references</summary>
   <p>Visual screening compares DINOv2 or DINOv3 image features with normal reference features. The DINOv2 encoder used online was lightly fine-tuned on synthetic defects made from normal images; the DINOv3 encoder stays frozen. Category calibration sets the operating threshold. The system does not classify named defects.</p>
   <p>The Evidence Assistant uses retrieval-augmented generation (RAG). BGE text embeddings retrieve reference passages; LangChain and LangGraph support retrieval, routing and evidence checks. Qwen generates supported explanations. This is vision-assisted text RAG, not image retrieval or a vision-language assistant.</p>
   <p>Application: React + Vite, FastAPI, SQLite for local storage, and Supabase for account security and private/shared online records. {online?'Online generation uses Qwen 2.5 3B fine-tuned for this project (improved using Qwen) on ZeroGPU.':'Local generation uses the configured Ollama model, commonly Qwen 2.5 3B.'} Corrective Action delivery can use n8n; a saved case is separate from an email being sent.</p>
   <p>References describe the components, not proof that every component or cited research method is implemented in full.</p>
   {[
    ['DINOv2 visual features','https://github.com/facebookresearch/dinov2'],
    ['DINOv3 visual features','https://github.com/facebookresearch/dinov3'],
    ['Qwen 2.5 3B text generation (base model, fine-tuned here)','https://huggingface.co/Qwen/Qwen2.5-3B-Instruct'],
    ['VisA example image dataset','https://github.com/amazon-science/spot-diff'],
    ['BGE text embeddings','https://huggingface.co/BAAI/bge-small-en-v1.5'],
    ['Dinomaly reference documentation','https://anomalib.readthedocs.io/en/lib-v2.6.2/markdown/guides/reference/models/image/dinomaly.html']
   ].map(([label,href])=><a className="source-link" key={label} href={href} target="_blank" rel="noreferrer">{label}</a>)}
   <p>VisA sample images: Zou et al., ECCV 2022, CC BY 4.0. Model and library licenses remain listed in the project documentation.</p>
  </details>
 </section></div>;
}
