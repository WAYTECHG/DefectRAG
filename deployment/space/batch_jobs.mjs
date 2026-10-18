// Preserve successful results and stop scheduling GPU work after quota rejection.
export const isQuotaError=message=>/exceeded.*(?:ZeroGPU|GPU).*(?:limit|quota)|(?:ZeroGPU|GPU).*(?:quota|limit).*exceed/i.test(message);
export async function runBatch(files,inspect){
 const records=[],errors=[];
 for(let index=0;index<files.length;index++){
  const file=files[index];
  try{records.push(await inspect(file))}
  catch(error){
   const message=String(error?.message||error||'Inspection failed');
   const quota=isQuotaError(message);
   errors.push({filename:file.name,message:quota?message+' Open https://huggingface.co/spaces/Wizzas/DefectRAG while signed in to Hugging Face to use your available free account allowance, or wait for quota reset. Supabase staff login uses a separate account. No prediction was made for this image.':message});
   if(quota){
    for(const pending of files.slice(index+1))errors.push({filename:pending.name,message:'Not submitted: ZeroGPU quota was exhausted earlier in this batch. Retry only unfinished images when free quota is available.'});
    break;
   }
  }
 }
 return {records,errors};
}
