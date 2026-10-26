// REVIEW ONLY: separate QA function; deploying/setting secrets requires approval.
import {handleCAQA} from './worker.mjs';
Deno.serve((request:Request)=>handleCAQA(request,{env:{
 SUPABASE_URL:Deno.env.get('SUPABASE_URL'),SUPABASE_SERVICE_ROLE_KEY:Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
 DEFECTRAG_CA_QA_ENABLED:Deno.env.get('DEFECTRAG_CA_QA_ENABLED'),DEFECTRAG_CA_QA_EVENT_ID:Deno.env.get('DEFECTRAG_CA_QA_EVENT_ID'),
 DEFECTRAG_CA_QA_WORKER_SECRET:Deno.env.get('DEFECTRAG_CA_QA_WORKER_SECRET'),
 DEFECTRAG_CA_QA_CALLBACK_SECRET:Deno.env.get('DEFECTRAG_CA_QA_CALLBACK_SECRET'),
}}));
