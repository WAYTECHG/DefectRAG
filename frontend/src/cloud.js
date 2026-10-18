let clientPromise;
export function cloudConfig() {
  const publicConfig = window.DEFECTRAG_PUBLIC_CONFIG || {};
  return {url:import.meta.env.VITE_SUPABASE_URL || publicConfig.supabaseUrl || '',
    key:import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || publicConfig.supabasePublishableKey || ''};
}
export function cloudConfigured() {
  const {url,key}=cloudConfig();
  let publicKey=key.startsWith('sb_publishable_');
  if(!publicKey){try{const claim=JSON.parse(atob(key.split('.')[1].replaceAll('-','+').replaceAll('_','/')));publicKey=claim.role==='anon'}catch{publicKey=false}}
  return /^https:\/\//.test(url) && publicKey;
}
export async function cloudClient() {
  if(!cloudConfigured())throw new Error('Team workspace is not connected. Complete the Supabase setup first.');
  clientPromise ||= import('@supabase/supabase-js').then(({createClient})=>{
    const {url,key}=cloudConfig();return createClient(url,key);
  });
  return clientPromise;
}
export async function currentStaff() {
  const client=await cloudClient();
  const {data:{user},error}=await client.auth.getUser();
  if(error||!user)throw new Error('Sign in to the team workspace before sharing.');
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
    if(error&&String(error.statusCode)!=='409')throw error;
    paths.push(path);
  }
  const {image_url,heatmap_url,...payload}=record;
  const {error}=await client.from('shared_inspections').insert({id:record.id,owner_id:user.id,payload,conversation:messages,image_path:paths[0],heatmap_path:paths[1]});
  if(error)throw error;
  return {alreadyShared:false};
}
