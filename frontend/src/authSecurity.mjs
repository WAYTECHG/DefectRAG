// Supabase remains the only MFA/session authority. No local code validates OTPs.
export function authWorkflowEnabled(){return globalThis.window?.DEFECTRAG_PUBLIC_CONFIG?.authWorkflowEnabled===true}
export async function authStatus(client){
 const {data,error}=await client.rpc('defectrag_auth_status');if(error)throw error;
 if(!data||typeof data.approved!=='boolean'||typeof data.authorized!=='boolean'||typeof data.aal2!=='boolean')throw new Error('Account security status is unavailable.');
 return data;
}
export async function requireStaff(client){
 const status=await authStatus(client);
 if(!status.approved||status.revoked)throw new Error('Staff access is pending, rejected or revoked. Demo Mode remains available after signing out.');
 if(!status.authorized||(status.mfa_required&&!status.aal2))throw new Error('Complete authenticator verification in Staff workspace.');
 return status;
}
export async function registerAccount(client,{email,password,displayName,redirectTo}){
 if(password.length<12||!displayName.trim()||displayName.trim().length>80)throw new Error('Use a display name and a password of at least 12 characters.');
 const {data,error}=await client.auth.signUp({email,password,options:{emailRedirectTo:redirectTo}});
 if(error)throw error;
 // No identity/role metadata or allowlist write. A verified session is needed
 // for the separate access-request RPC; email confirmation may return no session.
 if(data.session)await submitAccessRequest(client,displayName);
 return {confirmationRequired:!data.session};
}
export async function submitAccessRequest(client,displayName){
 const {data,error}=await client.rpc('defectrag_request_access',{p_display_name:displayName.trim()});if(error)throw error;return data;
}
export async function enrollTotp(client){
 const {data,error}=await client.auth.mfa.enroll({factorType:'totp',friendlyName:'DefectRAG authenticator'});if(error)throw error;return data;
}
export async function verifyTotp(client,factorId,code){
 if(!/^\d{6}$/.test(code))throw new Error('Enter the six-digit authenticator code.');
 const {data:challenge,error}=await client.auth.mfa.challenge({factorId});if(error)throw error;
 const verified=await client.auth.mfa.verify({factorId,challengeId:challenge.id,code});if(verified.error)throw verified.error;
 return verified.data;
}
export async function decideAccess(client,row,action){
 if(!['approve','reject','revoke'].includes(action))throw new Error('Invalid account action.');
 const {data,error}=await client.rpc('defectrag_decide_access',{p_user_id:row.user_id,p_action:action,p_version:row.version});if(error)throw error;return data;
}
export async function privateTeamImages(client,row){
 const urls=[];
 try{
  for(const path of [row.image_path,row.heatmap_path]){
   const {data,error}=await client.storage.from('team-inspections').download(path);if(error)throw error;
   urls.push(URL.createObjectURL(data));
  }
  return urls;
 }catch(error){urls.forEach(value=>URL.revokeObjectURL(value));throw error}
}
