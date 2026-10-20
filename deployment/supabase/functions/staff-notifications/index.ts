import {handleRequest} from './worker.mjs';

// Deployment is NOT performed by this source file. Configure native JWT gateway
// verification as documented; the purpose-scoped secret check always remains.
Deno.serve((request: Request) => handleRequest(request, {env: {
  SUPABASE_URL: Deno.env.get('SUPABASE_URL'),
  SUPABASE_SERVICE_ROLE_KEY: Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
  DEFECTRAG_NOTIFICATIONS_ENABLED: Deno.env.get('DEFECTRAG_NOTIFICATIONS_ENABLED'),
  DEFECTRAG_NOTIFICATION_WORKER_SECRET: Deno.env.get('DEFECTRAG_NOTIFICATION_WORKER_SECRET'),
  DEFECTRAG_N8N_WEBHOOK_URL: Deno.env.get('DEFECTRAG_N8N_WEBHOOK_URL'),
  DEFECTRAG_N8N_WEBHOOK_SECRET: Deno.env.get('DEFECTRAG_N8N_WEBHOOK_SECRET'),
  DEFECTRAG_NOTIFICATION_TRANSPORT: Deno.env.get('DEFECTRAG_NOTIFICATION_TRANSPORT'),
  DEFECTRAG_RESEND_API_KEY: Deno.env.get('DEFECTRAG_RESEND_API_KEY'),
  DEFECTRAG_EMAIL_FROM: Deno.env.get('DEFECTRAG_EMAIL_FROM'),
  DEFECTRAG_EMAIL_SANDBOX: Deno.env.get('DEFECTRAG_EMAIL_SANDBOX'),
  DEFECTRAG_EMAIL_QA_RECIPIENT: Deno.env.get('DEFECTRAG_EMAIL_QA_RECIPIENT'),
}}));
