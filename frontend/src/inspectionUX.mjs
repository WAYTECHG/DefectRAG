export const normalizeBatchName=value=>String(value||'').normalize('NFKC').trim().replace(/\s+/gu,' ').toLowerCase();
export function batchNameTaken(name,rows=[]){
 const key=normalizeBatchName(name);
 return Boolean(key&&rows.some(row=>normalizeBatchName(row.batch)===key));
}
export function storageDescription(storage,local=false){
 if(local&&storage==='browser_session')return 'Saved only on this computer. To keep it in a private account across devices, sign in with approved Staff access and a security code, then use Copy older work into this account.';
 return ({supabase_personal:'Saved online in Personal Workspace. Only this account can see it. Sign in with the same account on another device to open it.',
  supabase:'A shared copy is saved in Team Workspace. Approved Staff can see it.',
  local_account:'Saved on this computer for this account. Check saved changes to confirm it has also reached the online account.',
  browser_session:'Temporary demo result for this browser session. It may disappear when the online app restarts.'})[storage]||'Saved only on this computer. It is not automatically copied into an online account.';
}

export function personalSaveAccess(state){
 if(state==='authorized')return {allowed:true,reason:''};
 return {allowed:false,reason:state==='mfa'?'Enter the security code in Staff workspace before saving to the account or sharing with the team.':
  state==='guest'?'This result stays in the demo workspace. To save privately across devices, use an approved Staff account and its security code. Creating an account alone does not give Staff access.':
  'Check account approval and enter the security code in Staff workspace before saving online or sharing with the team.'};
}
