// Who is signed in: shown at the top of every page so nobody works under the wrong account.
// Reads the local session only (no network call) plus the staff display name when allowed.
export const roleLabel=role=>role==='developer'?'Developer':role==='staff'?'Staff':'';

export function accountSummary(account){
 if(!account?.user)return {signedIn:false,name:'',role:'',text:'Not signed in'};
 const name=(account.staff?.display_name||'').trim()||account.user.email||'your account';
 const role=roleLabel(account.staff?.role);
 return {signedIn:true,name,role,email:account.user.email||'',text:'Signed in as '+name+(role?' · '+role:'')};
}

export async function loadAccount(client){
 const {data,error}=await client.auth.getSession();
 const user=data?.session?.user;
 if(error||!user)return null;
 let staff=null;
 try{
  const result=await client.from('staff_members').select('display_name,role').eq('user_id',user.id).maybeSingle();
  if(!result.error)staff=result.data||null;
 }catch{staff=null}
 return {user:{id:user.id,email:user.email||''},staff};
}
