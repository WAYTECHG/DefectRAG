// Display wording only. Stored values, permission checks and API contracts do not change.
export const resultLabel=value=>({Good:'Looks normal',Anomalous:'Unusual appearance',Uncertain:'Needs a closer look'})[value]||value;
export const environmentLabel=(health,showcase=false)=>showcase?'SAVED EXAMPLES':!health?'CONNECTING…':health.mode==='cloud_session_workspace'?'ONLINE APP':'THIS COMPUTER';
export const answerLabel=(mode,saved=false)=>mode==='llm'?(saved?'SAVED ANSWER':'ANSWER WITH REFERENCES'):mode==='measurement_only'?'INSPECTION RESULT':mode==='retrieval_only'?'REFERENCE INFORMATION':'NO SUPPORTED ANSWER';
export const deliveryLabel=value=>({queued:'Waiting to send',sending:'Sending',delivered:'Accepted by email service',sent:'Accepted by email service',retry:'Waiting to retry',dead:'Needs administrator help',ambiguous:'Delivery unconfirmed',superseded:'Replaced by a newer update',suppressed:'Not sent'})[value]||value;
export const eventLabel=value=>({requested:'Staff access request',approved:'Access approved',rejected:'Access not approved',revoked:'Access removed',created:'New case',updated:'Case update',reminder:'Due-date reminder',overdue:'Overdue case'})[value]||value;

// Technical service errors are translated at the display boundary, never used to
// decide authorization, retry, success, or whether an operation was saved.
export function friendlyError(value,fallback='This action could not be completed. Try again. If the problem continues, contact the workspace administrator.'){
 const message=String(value?.message||value||'');
 if(!message)return fallback;
 if(/invalid login credentials/i.test(message))return 'The email or password was not accepted. Check both and try again.';
 if(/email not confirmed/i.test(message))return 'Confirm the email using the link in the signup email, then sign in again.';
 if(/(?:invalid|expired|incorrect).*(?:totp|otp|authenticator|verification code)|(?:totp|otp).*(?:invalid|expired)/i.test(message))return 'That security code was not accepted. Enter the latest six-digit code from the authenticator app.';
 if(/rate.?limit|too many requests|too many.*attempts/i.test(message))return 'Too many attempts were made. Wait a few minutes before trying again.';
 if(/reassign revoked owner|active owner and supervisor|active verified supervisor required/i.test(message))return 'Choose currently approved Staff for the person responsible and supervisor, then try again.';
 if(/latest reviewed reject|recorded human review required/i.test(message))return 'Open the shared inspection and save its latest Staff review as Reviewed and Reject before creating a case.';
 if(/explicit human defect confirmation required/i.test(message))return 'Confirm that the Staff review found a defect needing follow-up before creating the case.';
 if(/active team inspection required/i.test(message))return 'Choose a shared Team inspection that has not been archived.';
 if(/invalid case transition/i.test(message))return 'That case status change is not allowed. Refresh the case and choose an available status.';
 if(/audit note.*required/i.test(message))return 'Add a short note explaining what changed or was fixed before saving.';
 if(/invalid due date|due date must be within/i.test(message))return 'Choose a future due date within the next year.';
 if(/duplicate key|unique constraint/i.test(message))return 'A matching item may already exist. Refresh the list and check before trying again.';
 if(/exceeded.*(?:ZeroGPU|GPU).*(?:limit|quota)|(?:ZeroGPU|GPU).*(?:quota|limit).*exceed/i.test(message))return 'The free inspection service has reached its usage limit. Try again later. Signing in to Hugging Face may provide a separate allowance; Staff sign-in does not change this limit.';
 if(/pending.*approval|staff access.*pending/i.test(message))return 'Staff access has not been approved yet. Check its status in Staff workspace.';
 if(/revoked/i.test(message))return 'Access to this workspace has been removed. Contact the workspace administrator.';
 if(/expired.*(?:session|jwt)|(?:session|jwt).*expired|refresh token/i.test(message))return 'The sign-in has expired. Open Staff workspace and sign in again.';
 if(/(?:approved staff|approved account).*(?:TOTP|MFA)|complete MFA|verified TOTP|authenticator verification|AAL2/i.test(message))return 'Use an approved Staff account and enter the security code in Staff workspace before continuing.';
 if(/assigned editor|assigned owner|owner.*supervisor.*developer/i.test(message))return 'Only the person assigned to this case, its supervisor or a Developer can change it.';
 if(/case changed|version conflict|optimistic|stale.*version|concurrent/i.test(message))return 'This record changed elsewhere. Refresh it and check the latest details before saving again. The attempted update has not been confirmed.';
 if(/row.level security|permission denied|not authorized|unauthorized|insufficient.*privilege|RLS|42501|PGRST301/i.test(message))return 'This account cannot complete that action. Check approval and the security code in Staff workspace. If access is still denied, contact the workspace administrator.';
 if(/failed to fetch|networkerror|network request|fetch failed|connection.*(?:failed|refused)|timed? ?out|ECONN/i.test(message))return 'The connection was interrupted. Check the internet connection and try again. Any new changes may still be waiting to save.';
 if(/supabase|postgres|sqlite|RPC|PGRST|traceback|stack trace|HTTP \d{3}|service.role|JWT|backend|schema cache|constraint|relation .*does not exist/i.test(message))return fallback;
 return message;
}
