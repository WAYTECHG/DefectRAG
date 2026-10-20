// No SDK, network calls or secret reads on import. Provider remains opt-in.
export const WORKSPACE_URL='https://wizzas-defectrag.hf.space/#team';
const email=value=>typeof value==='string'&&value.length<=254&&/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);
export function emailConfiguration(env){
 if(!env.DEFECTRAG_RESEND_API_KEY||!email(env.DEFECTRAG_EMAIL_FROM))throw new Error('missing_email_configuration');
 const sandbox=env.DEFECTRAG_EMAIL_SANDBOX==='1';
 if(sandbox&&(!email(env.DEFECTRAG_EMAIL_QA_RECIPIENT)||env.DEFECTRAG_EMAIL_FROM!=='onboarding@resend.dev'))throw new Error('invalid_sandbox_configuration');
 if(sandbox&&!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(env.DEFECTRAG_EMAIL_QA_EVENT_ID||''))throw new Error('qa_event_required');
 if(!sandbox&&env.DEFECTRAG_EMAIL_FROM.endsWith('@resend.dev'))throw new Error('verified_sender_required');
 return {sandbox};
}
export function emailMessage(job,env){
 const {sandbox}=emailConfiguration(env);
 if(!email(job.recipient_email)||typeof job.display_name!=='string'||job.display_name.length>80)throw new Error('invalid_notification');
 if(sandbox&&(job.event_id!==env.DEFECTRAG_EMAIL_QA_EVENT_ID||job.kind!=='requested'||job.recipient_email.toLowerCase()!==env.DEFECTRAG_EMAIL_QA_RECIPIENT.toLowerCase()))throw new Error('sandbox_recipient_blocked');
 if(!['requested','approved','rejected','revoked'].includes(job.kind)||!Number.isFinite(Date.parse(job.requested_at)))throw new Error('invalid_notification');
 const name=job.display_name.replace(/[\r\n\x00-\x1f\x7f]/g,' ');
 const applicant=email(job.applicant_email)?job.applicant_email.split('@')[0].slice(0,1)+'***@'+job.applicant_email.split('@')[1]:'Verified account';
 const text=job.kind==='requested'?`Type: Staff Access Request\nApplicant: ${name}\nEmail: ${applicant}\nRequested: ${job.requested_at}\nStatus: Pending\nReview the current status in the authenticated workspace. Approval is manual and requires Developer MFA.`:
  `Type: Staff Access ${job.kind}\nAccount: ${name}\nAn email does not grant access. Sign in to view the current status. Approved Staff must complete authenticator verification.`;
 return {from:env.DEFECTRAG_EMAIL_FROM,to:[job.recipient_email],subject:'DefectRAG · Staff access '+job.kind,text:text+'\n'+WORKSPACE_URL};
}
