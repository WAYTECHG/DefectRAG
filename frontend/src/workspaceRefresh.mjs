// Display guidance only. Backend JWT, MFA and RLS checks remain authoritative.
export function workspaceRefreshGate(health,access,workspace){
 if(health?.mode!=='cloud_session_workspace'&&!health?.local_sync_enabled)return null;
 if(health.auth_workflow_enabled){
  const reasons={
   checking:'Checking access before opening saved work.',
   mfa:'Open Staff workspace and enter the six-digit security code to open private work.',
   pending:'The Staff request is waiting for approval. Private and Team work will be available after approval.',
   rejected:'The Staff request was not approved. Contact the workspace administrator if help is needed.',
   revoked:'Staff access has been removed. Contact the workspace administrator.',
   denied:'This account cannot open Staff work. Check access in Staff workspace.',
   unavailable:'Account access could not be checked. Check the connection and retry, or sign in again in Staff workspace.'
  };
  if(!['guest','authorized'].includes(access.state))return {
   reason:reasons[access.state]||reasons.denied,
   action:access.state==='checking'?null:'account',retry:access.state==='unavailable',
   failed:access.state==='unavailable'
  };
 }
 if(access.state==='guest'&&workspace==='team'&&health.personal_workspace_enabled)return {
  reason:'Sign in with an approved Staff account and enter the security code to open Team work. To try the app without signing in, switch to Personal Workspace for the demo.',action:'personal'
 };
 return null;
}

export async function readRefreshSections(requests,api,current){
 const settled=await Promise.allSettled(requests.map(([,path])=>api(path)));
 if(!current())return null;
 return {
  apply(){requests.forEach(([, ,setter],i)=>{if(settled[i].status==='fulfilled')setter(settled[i].value)})},
  failures:requests.flatMap(([name],i)=>settled[i].status==='rejected'?[{name,status:settled[i].reason?.status}]:[])
 };
}
