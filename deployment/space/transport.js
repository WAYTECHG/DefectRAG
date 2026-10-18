import {Client,closeClient} from './client.js';
import {cloudConfigured, cloudClient} from '../../frontend/src/cloud.js';
import {runBatch} from './batch_jobs.mjs';
let workspace;
let exportUrl='/api/export.csv';
export function sessionKey(){
  if(workspace)return workspace;
  try{workspace=localStorage.getItem('defectrag-private-workspace')}catch{}
  if(!/^[a-f0-9]{64}$/.test(workspace||'')){
    workspace=Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,'0')).join('');
    try{localStorage.setItem('defectrag-private-workspace',workspace)}catch{}
  }
  return workspace;
}
export const spaceUrl=path=>path==='/api/export.csv'?exportUrl:path;
async function credentials(){
  if(!cloudConfigured())return '';
  const client=await cloudClient();
  return (await client.auth.getSession()).data.session?.access_token||'';
}
export async function queued(endpoint,data,token=''){
  // A fresh client belongs to one job. Close it deterministically; never retain
  // an idle result-stream session across subsequent jobs or page transitions.
  const client=await Client.connect(location.origin,{record_history:false});
  try{return (await client.predict(endpoint,{...data,session:sessionKey(),token})).data[0]}
  finally{closeClient(client)}
}
const encode=file=>new Promise((resolve,reject)=>{
  const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);
  reader.onerror=()=>reject(new Error('Image could not be read'));reader.readAsDataURL(file);
});
export async function spaceFetch(path,options={}){
  const endpoint=new URL(path,location.origin).pathname;
  try{
    const token=await credentials();
    let data;
    if(options.method==='POST'&&['/api/inspect','/api/batch'].includes(endpoint)){
      const body=options.body,category=body.get('category'),batch=body.get('batch')||'';
      const files=endpoint==='/api/batch'?body.getAll('files'):[body.get('file')];
      if(!files.length||files.length>20||(endpoint==='/api/batch'&&!batch.trim()))throw new Error('Choose 1–20 images and a batch label.');
      const {records,errors}=await runBatch(files,async file=>{
          if(file.size>10*1024*1024)throw new Error('Image limit is 10 MB');
          return await queued('/inspect',{image_b64:await encode(file),filename:file.name,category,batch},token);
      });
      if(endpoint==='/api/inspect'){
        if(errors.length)throw new Error(errors[0].message);
        data=records[0];
      }else data={records,errors,batch};
    }else if(options.method==='POST'&&endpoint==='/api/assistant'){
      data=await queued('/assistant',JSON.parse(options.body),token);
    }else{
      const headers=new Headers(options.headers||{});
      headers.set('X-DefectRAG-Session',sessionKey());
      if(token)headers.set('Authorization','Bearer '+token);
      const response=await fetch(path,{...options,headers});
      if(response.headers.get('X-DefectRAG-Export'))exportUrl=response.headers.get('X-DefectRAG-Export');
      return response;
    }
    return Response.json({data});
  }catch(error){return Response.json({error:{message:error.message||'Model request failed'}},{status:503})}
}
