import {parseReview} from './workflow.mjs';
export const caseStates=['Open','Assigned','In Progress','Resolved','Closed','Cancelled'];
// UI feedback only; the database rechecks membership, MFA and stored assignments.
export function caseCanEdit(record,actorId,isDeveloper=false){
 return !!record&&typeof actorId==='string'&&actorId.length>0&&
  (record.owner_id===actorId||record.supervisor_id===actorId||isDeveloper===true);
}
export function nextCaseStates(state){
 return ({Open:['Open','Assigned','Cancelled'],Assigned:['Assigned','In Progress','Cancelled'],
  'In Progress':['In Progress','Resolved','Cancelled'],Resolved:['Resolved','Closed','In Progress','Cancelled'],Closed:[],Cancelled:[]})[state]||[];
}
function latestStructuredReview(notes){
 const structured=notes.filter(n=>parseReview(n)).sort((a,b)=>String(a.created_at).localeCompare(String(b.created_at))||a.id.localeCompare(b.id));
 return structured.at(-1);
}
export function latestDefectReview(notes){
 const latest=latestStructuredReview(notes);const review=latest&&parseReview(latest);
 return review?.status==='Reviewed'&&review.decision==='Reject'?latest:null;
}
export function caseCreationGate(inspection,notes=[],cases=[],loading=false){
 if(loading)return {ready:false,reason:'Opening the selected inspection…'};
 if(!inspection)return {ready:false,reason:'Choose a shared Team inspection to link this draft. Personal photos stay private until they are shared with the team.'};
 if(inspection.archived_at)return {ready:false,reason:'This inspection is archived. Choose an active Team inspection.'};
 const review=latestDefectReview(notes);
 if(!review){
  const latest=latestStructuredReview(notes),saved=latest&&parseReview(latest);
  return {ready:false,reason:saved?`Latest Staff review: ${saved.status} / ${saved.decision}. A case requires a human-confirmed defect with a saved Reviewed / Reject decision. Keep a valid Accept or Hold decision unchanged; choose another inspection or review the evidence when a reassessment is needed.`:'No completed defect review is saved. Open the photo and Staff review. Record Reviewed / Reject only when the evidence actually confirms a defect; accepted products do not need a corrective-action case.'};
 }
 const existing=cases.find(c=>c.review_id===review.id);
 if(existing)return {ready:false,existingCaseId:existing.id,reason:'This saved review already has a case. Open the existing case to see its assignment and progress.'};
 return {ready:true,review,reason:'The saved review is ready. Choose the person responsible, a supervisor and a deadline, then confirm the defect to create the case.'};
}
// Immediate form feedback only. Database RPCs enforce these rules independently.
export function caseDraftError({description,owner,supervisor,priority,due},people,now=Date.now()){
 if(typeof description!=='string'||description.trim().length<10||description.trim().length>2000)return 'Describe the work in 10 to 2,000 characters.';
 const active=id=>people.some(p=>p.user_id===id&&!p.revoked_at);
 if(!active(owner))return 'Choose an active Staff member as the person responsible.';
 if(!active(supervisor))return 'Choose an active Staff member as the supervisor.';
 if(!['Low','Normal','High','Critical'].includes(priority))return 'Choose a priority.';
 const date=Date.parse(due);
 if(!Number.isFinite(date))return 'Choose a due date and time.';
 if(date<=now)return 'Choose a future due date and time.';
 if(date>now+365*24*60*60*1000)return 'Choose a due date within the next year.';
 return '';
}
export function caseMetrics(cases,now=Date.now()){
 const active=cases.filter(c=>!['Closed','Cancelled'].includes(c.state));
 const durations=cases.filter(c=>['Resolved','Closed'].includes(c.state)).map(c=>Date.parse(c.resolved_at)-Date.parse(c.created_at)).filter(ms=>Number.isFinite(ms)&&ms>=0);
 return {open:active.filter(c=>c.state!=='Resolved').length,resolved:cases.filter(c=>['Resolved','Closed'].includes(c.state)).length,
  overdue:active.filter(c=>c.state!=='Resolved'&&Date.parse(c.due_at)<now).length,
  averageResolutionHours:durations.length?durations.reduce((a,b)=>a+b,0)/durations.length/3600000:null};
}
export async function caseRpc(client,name,payload){
 // Database checks live membership + native factor on every write. UI check is
 // additive feedback, never the authorization boundary.
 const {data,error}=await client.rpc(name,payload);if(error)throw error;return data;
}
