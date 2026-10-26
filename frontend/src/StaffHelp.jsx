import React from 'react';

export default function StaffHelp({health,showcase=false}){
 const online=health?.mode==='cloud_session_workspace';
 return <div className="overview-grid"><section className="card about">
  <h2>Using DefectRAG</h2><p>Check product photos, record Staff decisions and keep track of problems that need fixing. The app helps with screening; workplace quality rules still decide whether a product is accepted.</p>
  <h3>1. Start an inspection</h3><p>Choose Image inspection for one photo, or Batch inspection for up to 20 photos. Select the matching product, add clear photos and choose Run inspection or Inspect batch. Batch photos do not need to be inspected first.</p>
  <h3>2. Check the result</h3><p>Looks normal means no unusual appearance was flagged. Unusual appearance or Needs a closer look means a Staff check is recommended. Compare the original photo with the highlighted areas. A high score means a larger difference from normal examples, not a percentage chance of a defect.</p>
  <h3>3. Keep work private or share it</h3><p>Personal Workspace is private to the signed-in account. Check that changes are saved online before closing the app or switching devices. Choose Share with team to create a separate Team copy. The public gallery is a different choice: anyone can see a published copy.</p>
  <h3>4. Review shared work</h3><p>Open Inspection history, select Team Workspace, then choose Review. Save the Staff review and decision. For a confirmed defect needing follow-up, save Reviewed and Reject, then choose Create or view corrective actions.</p>
  <h3>5. Track a corrective action</h3><p>Choose Corrective Actions in the sidebar. Under Create and assign a case, choose a Team inspection. Assignment fields can be drafted before its review is ready; the message beside Create corrective action explains what is still needed. Use Open photo and Staff review to check the evidence. Create a case only after a saved Reviewed and Reject decision and explicit defect confirmation. Keep an appropriate Accept or Hold decision unchanged. Choose the person responsible, supervisor and due date, describe the work and confirm the defect. Open Details to see progress and history. Only the person responsible, supervisor or a Developer can make changes after the account security check. Saving a deadline does not send email by itself; reminders require administrator activation.</p>
  <h3>Sign-in help</h3><p>New Staff create an account, confirm the email, sign in and request access. A Developer must approve it. Approved Staff use an authenticator app for the extra six-digit security code. Password reset does not remove this check. Contact the workspace administrator if the authenticator is lost.</p>
 </section><section className="card about">
  <h2>Saving and privacy</h2>
  <p>{showcase?'This version shows saved examples only. It does not check new photos or provide a live assistant.':online?'The online app saves approved account work privately online. Without sign-in, demo results belong to this browser session and may disappear when the app restarts.':'Without sign-in, work stays on this computer. With approved sign-in and a security code, Personal work can also be saved online. Check saved changes to see whether anything is still waiting.'}</p>
  <p>To use private work on another device, sign in with the same account and complete its security check there. Sharing with the team is always separate. Personal notes and later conversations are not added to a Team copy automatically.</p>
  <h3>If changes were made in two places</h3><p>The app keeps both copies for review. Compare saved changes before choosing which copy to use. Do not assume that a change waiting on this computer has already reached the online account.</p>
  <h3>Understanding the assistant</h3><p>Ask about the saved result, highlighted areas or supporting information. The assistant reads saved measurements and references; it does not examine the photo itself. Open supporting references and check important answers. The app does not provide factory repair instructions or replace workplace procedures.</p>
  <h3>If something is not working</h3><p>Read the message beside the action. It explains whether to add a photo, finish sign-in, enter a security code, wait for approval, or retry a connection. Free online service limits can cause delays. Mark as seen only records that an alert was noticed; it does not approve the product.</p>
  <details className="workflow-details"><summary>Technical background and references</summary>
   <p>Visual screening compares DINOv2 or DINOv3 image features with normal reference features. Encoder weights remain frozen. Category calibration sets the operating threshold. The system does not classify named defects.</p>
   <p>The Evidence Assistant uses retrieval-augmented generation (RAG). BGE text embeddings retrieve reference passages; LangChain and LangGraph support retrieval, routing and evidence checks. Qwen generates supported explanations. This is vision-assisted text RAG, not image retrieval or a vision-language assistant.</p>
   <p>Application: React + Vite, FastAPI, SQLite for local storage, and Supabase for account security and private/shared online records. {online?'Online generation uses Qwen3 4B on ZeroGPU.':'Local generation uses the configured Ollama model, commonly Qwen 2.5 3B.'} Corrective Action delivery can use n8n; a saved case is separate from an email being sent.</p>
   <p>References describe the components, not proof that every component or cited research method is implemented in full.</p>
   {[
    ['DINOv2 visual features','https://github.com/facebookresearch/dinov2'],
    ['DINOv3 visual features','https://github.com/facebookresearch/dinov3'],
    ['Qwen3 text generation','https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507'],
    ['VisA example image dataset','https://github.com/amazon-science/spot-diff'],
    ['BGE text embeddings','https://huggingface.co/BAAI/bge-small-en-v1.5'],
    ['Dinomaly reference documentation','https://anomalib.readthedocs.io/en/lib-v2.6.2/markdown/guides/reference/models/image/dinomaly.html']
   ].map(([label,href])=><a className="source-link" key={label} href={href} target="_blank" rel="noreferrer">{label}</a>)}
   <p>VisA sample images: Zou et al., ECCV 2022, CC BY 4.0. Model and library licenses remain listed in the project documentation.</p>
  </details>
 </section></div>;
}
