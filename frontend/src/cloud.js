import {practiceActive,practiceClient,practiceStaff} from './practice.mjs';
let clientPromise;
export function cloudConfig() {
  const publicConfig = window.DEFECTRAG_PUBLIC_CONFIG || {};
  return {url:import.meta.env.VITE_SUPABASE_URL || publicConfig.supabaseUrl || '',
    key:import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || publicConfig.supabasePublishableKey || ''};
}
export function cloudConfigured() {
  if(practiceActive())return true;
  const {url,key}=cloudConfig();
  let publicKey=key.startsWith('sb_publishable_');
  if(!publicKey){try{const claim=JSON.parse(atob(key.split('.')[1].replaceAll('-','+').replaceAll('_','/')));publicKey=claim.role==='anon'}catch{publicKey=false}}
  return /^https:\/\//.test(url) && publicKey;
}
export async function cloudClient() {
  // Guided practice never reaches Supabase; it uses the in-memory lesson store.
  if(practiceActive())return practiceClient();
  if(!cloudConfigured())throw new Error('Team workspace is not connected. Complete the Supabase setup first.');
  clientPromise ||= import('@supabase/supabase-js').then(({createClient})=>{
    const {url,key}=cloudConfig();const client=createClient(url,key);
    client.auth.onAuthStateChange((event,session)=>{
      if(['SIGNED_IN','SIGNED_OUT','TOKEN_REFRESHED','MFA_CHALLENGE_VERIFIED','USER_UPDATED'].includes(event))
        setTimeout(()=>window.dispatchEvent(new CustomEvent('defectrag-auth-change',{detail:{event,userId:session?.user?.id||null}})),0);
    });
    return client;
  });
  return clientPromise;
}
export async function currentStaff() {
  if(practiceActive())return practiceStaff();
  const client=await cloudClient();
  const {data:{user},error}=await client.auth.getUser();
  if(error||!user)throw new Error('Sign in to the team workspace before sharing.');
  if(window.DEFECTRAG_PUBLIC_CONFIG?.authWorkflowEnabled===true){
    const {requireStaff}=await import('./authSecurity.mjs');
    await requireStaff(client);
  }
  const {data,error:staffError}=await client.from('staff_members').select('*').eq('user_id',user.id).single();
  if(staffError||!data)throw new Error('Your account is not on the staff allowlist. Ask the workspace developer to add it.');
  return {client,user,staff:data};
}
export async function shareInspection(record,messages,url) {
  const {client,user}=await currentStaff();
  const {data:existing,error:lookupError}=await client.from('shared_inspections').select('id').eq('id',record.id).maybeSingle();
  if(lookupError)throw lookupError;
  if(existing)return {alreadyShared:true};
  const paths=[];
  for(const [kind,source] of [['image',record.image_url],['heatmap',record.heatmap_url]]){
    const response=await fetch(url(source));if(!response.ok)throw new Error('Could not read the saved inspection image.');
    const blob=await response.blob();
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))).map(b=>b.toString(16).padStart(2,'0')).join('');
    const path=`${user.id}/${record.id}/${kind}-${hash}.jpg`;
    const {error}=await client.storage.from('team-inspections').upload(path,blob,{contentType:blob.type||'image/jpeg',upsert:false});
    if(error&&!(String(error.statusCode)==='409'||(['Duplicate','ResourceAlreadyExists','KeyAlreadyExists'].includes(error.code))||(/already exists/i.test(error.message||'')&&String(error.statusCode)==='400')))throw error;
    paths.push(path);
  }
  const {image_url,heatmap_url,report_url,owner_id,...payload}=record;
  const {error}=await client.from('shared_inspections').insert({id:record.id,owner_id:user.id,payload,conversation:messages,image_path:paths[0],heatmap_path:paths[1]});
  if(error)throw error;
  workspaceChanged();
  return {alreadyShared:false};
}

export function workspaceChanged(){
 window.dispatchEvent(new Event('defectrag-workspace-change'));
 try{localStorage.setItem('defectrag-workspace-event',String(Date.now())+Math.random())}catch{}
}
if(typeof window!=='undefined'&&typeof window.addEventListener==='function')window.addEventListener('storage',event=>{
 if(event.key==='defectrag-workspace-event')window.dispatchEvent(new Event('defectrag-workspace-change'));
});
