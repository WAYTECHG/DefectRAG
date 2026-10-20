import {parseReview} from './workflow.mjs';
export const caseStates=['Open','Assigned','In Progress','Resolved','Closed','Cancelled'];
export function nextCaseStates(state){
 return ({Open:['Open','Assigned','Cancelled'],Assigned:['Assigned','In Progress','Cancelled'],
  'In Progress':['In Progress','Resolved','Cancelled'],Resolved:['Resolved','Closed','In Progress','Cancelled'],Closed:[],Cancelled:[]})[state]||[];
}
export function latestDefectReview(notes){
 const structured=notes.filter(n=>parseReview(n)).sort((a,b)=>String(a.created_at).localeCompare(String(b.created_at))||a.id.localeCompare(b.id));
 const latest=structured.at(-1);const review=latest&&parseReview(latest);
 return review?.status==='Reviewed'&&review.decision==='Reject'?latest:null;
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
