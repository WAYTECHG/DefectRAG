// Display guidance only. Backend JWT, MFA and RLS checks remain authoritative.
export function workspaceRefreshGate(health,access,workspace){
 if(health?.mode!=='cloud_session_workspace'&&!health?.local_sync_enabled)return null;
 if(health.auth_workflow_enabled){
  const reasons={
   checking:'Checking account permissions before loading workspace records.',
   mfa:'Verify the authenticator in Staff workspace to load private workspace records.',
   pending:'Staff access is pending approval. Private workspace records are unavailable until approval.',
   rejected:'Staff access was rejected. Private workspace records are unavailable.',
   revoked:'Staff access was revoked. Protected workspace records are unavailable.',
   denied:'This account does not have permission to access protected workspace records.',
   unavailable:'Account permissions could not be checked. Reconnect and retry, or open Staff workspace to sign in again.'
  };
  if(!['guest','authorized'].includes(access.state))return {
   reason:reasons[access.state]||reasons.denied,
   action:access.state==='checking'?null:'account',retry:access.state==='unavailable',
   failed:access.state==='unavailable'
  };
 }
 if(access.state==='guest'&&workspace==='team'&&health.personal_workspace_enabled)return {
  reason:'Team Workspace requires approved staff sign-in and authenticator verification. Personal Workspace provides an isolated guest demo.',action:'personal'
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
