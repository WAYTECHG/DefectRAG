# One approved QA email attempt — 21 October 2026

User approved exactly ONE authenticated worker invocation for event
3d25e7b3-04c4-43c8-a49e-e473be3bcbdc and immediate delivery0 afterward regardless
of success/failure. No further invocation/retry/cron/n8n/other event or recipient
is authorized. The applicant must remain Pending, no Staff membership. No account
decision/deletion/permission change, SQL migration, new provider key or deployment.

No connected Supabase management API/provider connector is available to the agent.
The project owner must operate Dashboard settings and privately supply the saved
worker bearer. The agent cannot guarantee automatic shutdown through that UI or
claim a send until evidence is supplied. No credentials should enter chat or files.

## Before enabling: prepare both Dashboard tabs

1. Run deployment/email_single_qa_verification.sql once and privately save its
   metadata row. It is SELECT only. Before-send expected: matching_events1,
   applicant_still_pending_without_stafftrue,current_developer_request_eventtrue,
   event statusqueued/attempts0, no snapshot, delivered_atnull. If different STOP
   with delivery0, no automatic repair. Retain unrelated count/fingerprint for
   after comparison; no private payload is output.
2. In existing Supabase project, open Edge Functions > Secrets in one tab, and
   the existing hyper-worker > Test in another. Do NOT create/redeploy a function.
   Keep any notification cron/old n8n consumers inactive. If an active consumer
   exists or provider/recipient setup has changed, stop; do not risk a second run.
3. While delivery0, set DEFECTRAG_EMAIL_QA_EVENT_ID to the exact UUID above. Retain
   DEFECTRAG_EMAIL_SANDBOX=1 and DEFECTRAG_NOTIFICATION_TRANSPORT=resend. Existing
   QA_RECIPIENT must still be the verified Resend-owner Developer address and
   EMAIL_FROM=onboarding@resend.dev. Do not change provider keys, other secrets,
   Auth SMTP, HF settings, native MFA or registration. Never use the applicant as
   the Resend test-sender recipient.
4. Configure Test: POST, JSON body {}, and Authorization header with value
   Bearer followed by ONE space and your existing DEFECTRAG_NOTIFICATION_WORKER_SECRET.
   Enter it privately. It is not a Supabase anon/service-role key or Resend API key.
   Do not share screenshots showing the header. Do not send yet.

## One attempt and immediate shutdown

5. In Secrets set ONLY DEFECTRAG_NOTIFICATIONS_ENABLED=1 and save. In Test click
   Send Request EXACTLY ONCE. No retry for401,503,timeout,queued,or any other result.
6. As soon as the attempt returns OR an error/timeout occurs, immediately change
   DEFECTRAG_NOTIFICATIONS_ENABLED back to0 and SAVE, BEFORE inspecting mail,
   taking screenshots or replying. This is required even when nothing was sent.
   Never leave delivery1 while investigating. If access/connectivity fails,
   restore0 as the first action on reconnect; agent has no remote shutdown channel.
7. Privately copy ONLY response HTTP status and JSON body (not headers) after
   shutdown. Typical success:200 with claimed1/accepted1/retried0/leaseLost0.
   Actual body may include budgetLimited. Any other result requires inspection,
   not another send. retried1 means queued for a future authorized invocation,
   NOT approval to run automatically. The current call has bounded processing;
   later retries remain blocked by delivery0 and inactive schedulers.
8. Remove Authorization from the test form. A subsequent POST{} with NO header
   is a disabled-gate probe, not a send attempt: expect503 notifications_disabled.
   On401 it is not confirmed disabled; recheck0/save and investigate without a
   credentialed retry. No worker secret should be included in shared output.

## Read-only evidence after shutdown

9. Run the SAME verification SELECT again. Expected success: status sent,
   attempts1, delivered_at present, snapshot present, claimable_nowfalse;
   applicant_still_pending_without_staff and current_developer_request_event true.
   Unrelated count and metadata fingerprint must match the before row; differences
   require investigation (including concurrent activity), not assumed attribution.
   Share these two metadata rows only, never a snapshot/body or credentials.
10. In Resend Dashboard inspect the existing log for the single API request. Record
    provider HTTP result, response email ID, delivery status and, if available,
    idempotency key defectrag/3d25e7b3-04c4-43c8-a49e-e473be3bcbdc. Redact addresses
    and request headers/API keys. Confirm ONE matching email in Developer mailbox,
    correct Pending request context and https://wizzas-defectrag.hf.space/#team.
    No second API call is permitted to obtain missing evidence.

Provider body is not returned/stored by existing worker; accepted1 means it saw
2xx + nonempty provider email ID AND acknowledged the outbox. Resend's actual log
is needed for raw response/delivery evidence. sent does not prove inbox receipt.
No duplicate re-dispatch will be performed: sent exclusion, one provider result,
one received message, snapshot/key consistency and unchanged unrelated metadata
are available checks. An actual live provider replay/failure-retry test remains
UNTESTED without separate approval. Existing local idempotency tests are simulated.
This manually triggered test also does not prove laptop-off scheduling/operation.

## Stop conditions

Keep delivery0 on any uncertainty. Do not reset attempts/status/lease/snapshot,
regenerate idempotency keys, approve/reject/revoke the applicant, retry a timeout,
or rotate unrelated secrets. Inspect actual cloud records to resolve ambiguity.
No further send, automated retry, scheduler or n8n activation without approval.
