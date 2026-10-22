# Developer email activation — controlled preflight, 20 October 2026

## Latest checkpoint

22 October provider verification: Resend POST /emails HTTP200, response ID
01a16225-6de2-7542-97dc-3b5bffaa5c75 and Delivered status independently observed.
Exact-event idempotency key matches; Preview has Pending/manual MFA/production
workspace link and masked applicant. One message in current 15-day Sending list.
No new send/configuration change. Inbox placement awaits user confirmation;
off-laptop scheduling and actual replay/failure retry remain untested. Details:
results/email-single-send-live-20261022/provider-verification.json.

22 October: single-event attempt after the approved clock fix PASSED provider
acceptance and durable acknowledgment: HTTP200 claimed1/accepted1/retried0/
leaseLost0; selected event sent/attempts1/not claimable, applicantPending/noStaff,
all four unrelated events unchanged. Delivery immediately disabled again and
independently verified503notifications_disabled. Authorization is consumed; no
further send/retry/scheduling permitted. Resend raw response/delivery status and
mailbox receipt still await provider login/user confirmation. See
results/email-single-send-live-20261022/ and latest DEVELOPMENT_PROGRESS.md.
The dated approval/instruction history below is not permission to resend.

ONE SEND NOW APPROVED by user for exact QA event below, with unconditional
immediate return to delivery0 after outcome/error. Follow ONLY the current
docs/SINGLE_QA_EMAIL_ATTEMPT.md, including one credentialed invocation and no
retries. No connected Supabase management API exists here; owner performs the
Dashboard secret switches and enters saved worker bearer privately. Agent has
not performed any activation or send. Before/after SELECT file:
deployment/email_single_qa_verification.sql. No second live dispatch is authorized
for duplicate testing; sent exclusion and Resend log evidence only. Provider
acceptance != inbox receipt. Keep pending account unapproved and n8n/cron off.

Pending QA metadata PASSED (user-returned SQL, 21 October): event
3d25e7b3-04c4-43c8-a49e-e473be3bcbdc; one confirmed account, Pending request,
no membership, worker grants pass, exactly one current queued unattempted event
to an active verified Developer. Sanitized evidence is in
results/email-pending-qa-verification-20261021.json. No send authorized yet.

REQUEST NEXT explicit approval for ONLY that UUID, setting QA_EVENT_ID and
delivery1 with sandbox1/transportresend preserved, ONE authenticated hyper-worker
POST and returning delivery0 afterward. Email recipient remains the configured
Resend-owner Developer, not the pending applicant. Do not approve the applicant,
send unrelated notifications, configure cron or enable n8n. User enters credentials
privately; do not request the worker bearer/provider key in chat. Ambiguous first
call requires evidence review, no automatic repeated sends or outbox resets.

21 October: user reports a NEW user-controlled account Pending and unapproved.
Use deployment/email_pending_qa_verification.sql, one read-only SELECT scoped
to that new email. Expected matching_auth_accounts1/email_confirmedtrue,
request_statuspending/staff_memberships0/worker_permissions_oktrue,
eligible_event_count1 and qa_event_id populated. Read event_checks on mismatch;
do not mutate records to fix it. Metadata verification still pending user result.
No need to execute the separate QA deletion/cleanup proposal; it is superseded.
Next gate remains exact event/recipient/configuration/send approval. Retain
delivery0 until that approval; sandbox1 with exact QA UUID prevents claiming
unrelated outbox rows. Provider account-owner recipient match must remain intact.

DIAGNOSIS RECEIVED: user-supplied live SELECT shows worker_permissions_ok=true,
one active verified Developer and no pending requests. The known QA applicant
is approved; its requested event a75e25fa-c41b-4529-8c3b-44dbe93d9683 is superseded,
not current-version and attempts0. Its exact name matched; status/version caused
the zero selection. Never revive/send that stale event or revoke an approved
account for an email test. Request approval for a fresh user-controlled pending
QA request, leaving existing permissions unchanged and delivery disabled. Native
confirmation mail for a new controlled signup is separate from Developer email
delivery activation, which still requires the exact-event approval below.

UPDATE: previous QA SELECT returned zero rows (user screenshot). Cause not yet
established. Updated deployment/email_qa_selection.sql is ONE read-only SELECT
that always returns a diagnostic row, independently checks RPC permissions and
shows counts plus latest20 requested-event status metadata without personal
details. Run this updated file once; do not repeat the migration or activate
delivery. Previous expected-row instructions below are historical. No event has
been selected/authorized. Resubmitting an already-pending request is idempotent
and will not create another notification. Any new QA event or data repair needs
separate review/approval; never reset sent events to obtain a test email.

DISABLED DEPLOYMENT PASSED. Actual Dashboard function slug is hyper-worker
(default name retained), not staff-notifications. It hosts the prepared logical
staff-notification component; no need to recreate/rename it or deploy a duplicate.
Live URL:https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/hyper-worker.
User screenshot shows POST{} ->503 notifications_disabled. Agent independently
confirmed the same public POST result WITHOUT Authorization or any credential.
Evidence:results/email-disabled-live-20261020.json. This verifies the live gate,
not exact remote bundle hash, provider key validity or new database RPC behavior.
No email/claim was requested. Keep delivery0 and legacy n8n notifications off.

NEXT: run deployment/email_qa_selection.sql (ONE SELECT, no mutation). It returns
only eligible controlled QA event ID/status/attempts/request status and checks
the two new direct RPCs' service-only grants in the SAME result. Expected one
queued/pending row, attempts0,worker_permissions_ok=true. If0/multiple/mismatch,
stop and inspect; no resetting sent rows or autoapproval. QA event ID is an
identifier, not a credential; no email/payload/token is returned. After reviewing
that result, seek exact approval for QA event configuration and controlled send/
scheduling; no delivery1, invocation with worker secret, cron or provider send yet.

Future cloud scheduler MUST target /functions/v1/hyper-worker. Existing CLI source
folder/config remains staff-notifications; do not blanket-deploy functions or
create a second consumer. Review any future CLI name mapping separately.

User APPROVED DISABLED DEPLOYMENT of staff-notifications. Authorized: exact
single-file bundle below, function-scoped verify_jwt=false, delivery0 and safe
disabled POST check. No secrets read/changed, outbound delivery, cron, CA/HF
deployment or new SQL is included. Dashboard steps supplied; deployment is
COMPLETE for the actual hyper-worker slug as verified above.

Single procedure: existing project -> Edge Functions -> Deploy a new function ->
Via Editor (or open existing staff-notifications only). Name staff-notifications;
replace entire index.ts with Desktop runtime/email-function-release/index.ts;
deploy. Set function-only JWT verification off per reviewed config. Preserve
notification delivery0 and all other settings. Test POST with body{}; expected
HTTP503 and {"error":"notifications_disabled"}, an intentional disabled response.
Do not add worker secrets to shared test output. User returns status/body and
public function URL only; actual provider/DB behavior is not proven by this test.

User reports `Disabled configuration saved` for the seven approved Edge secrets.
Recorded as USER-CONFIRMED, not independent secret inspection. No secret value
was provided/read. QA event ID remains deferred. Disabled deployment is now approved above.

To avoid CLI installation/multi-file paste, offline packager
deployment/supabase/build_email_function.mjs bundles the three reviewed sources
into runtime/email-function-release/index.ts. No new dependencies, secrets or
behavior changes. Four packaged-code checks passed: import-free bundle,
disabled POST503, unauthorized enabled POST401, GET405; no network calls.
Bundle SHA256:a70e89e05d66918ed00a78bfdc769c2afd761fb10e376be0e12903147cd82017.

APPROVED SCOPE: deploy ONLY staff-notifications from that single file,
retain DEFECTRAG_NOTIFICATIONS_ENABLED=0, use reviewed function-level
verify_jwt=false with the handler's dedicated bearer check, then check disabled
POST503 without providing a worker secret. No cron, QA send, provider request,
CA/HF deployment or auth/security-policy change is included. Supabase management
connector/CLI access is unavailable; Dashboard deployment is the prepared route.
After approval, create/open the exact staff-notifications function in the
existing project, paste the complete bundle into index.ts and deploy. If an
existing function contains unrelated code, stop rather than overwrite it.

User has now APPROVED DISABLED CONFIGURATION ONLY. Manual entry of seven
Supabase Edge secrets has now been confirmed saved by the user. Keep delivery0; omit QA
event ID until its authorized selection. No secret values are requested in chat.
Deployment, worker invocation, scheduling and sending remain unapproved.

User manually executed the reviewed direct-notifications migration and reported
`Success. No rows returned`. This is expected for its DDL + transaction COMMIT.
Record it as user-reported applied; DO NOT rerun. New live RPC definitions/grants
have not yet been independently probed. Existing worker claim/finish screenshot
confirmed anon=false,authenticated=false,service_role=true for both. Earlier
flags/object/privacy checks were confirmed by the user. Resend email match was
also user-confirmed. No secret, deployment, activation or email action by agent.

Next: request separate approval to deploy only staff-notifications with delivery0. QA event ID can stay
unset while disabled; determine it before an explicitly authorized send. Native
Auth SMTP/MFA, HF/React and all membership/data remain unchanged. Milestone1
is NOT complete: actual cloud/SQL negative checks, provider delivery, off-laptop
proof, retry and duplicate evidence still pending.

Status: CONDITIONAL readiness, not authorization to migrate/deploy/send.
Starting checkpoint68b7a1e, branch feature/auth-mfa-inactive. Priority2 remains
deferred until Priority1 has real cloud/mailbox evidence. No frontend redesign,
HF deployment, inference, database mutation, provider account/key creation or
notification activation was performed during this preflight.

## First action — provider compatibility only

1. Open https://resend.com and sign up/sign in on Free using the EXACT same
   mailbox as the existing active DefectRAG Developer recipient.
2. Complete Resend account/email verification. No domain purchase, DNS change,
   paid plan or test send is required for this step.
3. Confirm privately that the verified Resend account email equals the Developer
   email. An alias/different account should not be assumed compatible.
4. Reply only `Resend ready; email matches`, or report a mismatch. Do not send
   email addresses, passwords, keys, confirmation links or screenshots of secrets.

Expected: Resend dashboard accessible with that verified account; zero changes
to Supabase Auth SMTP/MFA and zero application notifications sent. Resend's
onboarding@resend.dev sender is restricted to its account owner. This is a
Developer-only QA setup, not unrestricted production email or applicant delivery.
Free currently allows3000/month and100/day; do not enable paid overages.

## Source audit and readiness findings

- Existing verified-access-request RPC inserts Pending request/audit and unique
  outbox events for active, verified-email Developers. Resubmitting the SAME
  pending account is idempotent; it does NOT create a second request/mail event.
- Approve/reject/revoke remain manual Developer/native-AAL2 functions. Email
  worker cannot enroll MFA or approve membership. Existing Auth Gmail SMTP is
  separate and must remain unchanged.
- Direct transport calls fixed api.resend.com via HTTPS, no n8n dependency.
  Exact QA recipient, requested kind and one QA event UUID are mandatory in
  sandbox. No private images, credentials or account tokens in message/link.
- Snapshot RPC persists exact provider body before send; stable event key is
  reused. Resend keeps keys24h; SQL quarantines ambiguity after23h, including
  manual dead-letter retries. Changed verified recipient also quarantines.
- Reuses row locks,5-minute leases,eight attempts,backoff and sent/dead statuses.
  Global claim clock limits one event/30s; max100s Edge invocation, claim/send/
  snapshot/finish reservation. Provider failure never grants permission.
- Preflight found two housekeeping UPDATEs applied to all outbox rows even
  with a selected QA event. The UNAPPLIED migration now scopes both to p_event
  when configured. This prevents unrelated queued/dead/superseded status changes
  during the controlled test. Normal unfiltered operation is preserved.
- SQL changes remain limited to nullable outbox columns, private clock and
  service-role-only definer RPCs. No auth flags, staff grants, storage/Gallery
  policy, existing inspections or triggers are changed by this migration.
- Worker gateway JWT is intentionally disabled ONLY for the server function;
  dedicated >=32-character bearer validation is mandatory. React must never
  receive that bearer, provider key or service-role key.
- `sent` means provider acceptance, not inbox delivery/read. Provider response
  ID is not persisted in the outbox; correlate its UUID idempotency header with
  Resend dashboard request/response logs. Preserve sanitized QA evidence there.

Live schema/default grants/extensions, existing cloud worker/scheduler, provider
identity and server secret configuration are NOT verified yet. Local SQL/RLS
execution remains pending; source review and mocked tests do not prove it.
Supabase Edge flags/secrets are independent of same-named HF variables.

## Read-only database preflight — after account compatibility

Run deployment/email_activation_preflight.sql in the EXISTING Supabase project's
SQL Editor. It contains SELECTs only and performs no claim/send/reset/approval.
Return only metadata/counts, not full tables, applicants, payloads, keys or cron
commands. Expected:

- registration_enabled=true and mfa_required=true; otherwise stop, do not change.
- Existing outbox and original claim/finish functions present.
- Outbox RLS enabled, no anon/authenticated direct reads or updates.
- Claim/finish execute:service_role true,anon/authenticated false. Developer
  status RPC is authenticated but internally requires Developer native AAL2.
- New clock/functions/snapshot columns absent before first application. If any
  already exist, stop and compare deployed definitions; never rerun blindly.
- Review eligible QA event count. Zero is not permission to reset/recreate rows;
  more than one requires explicitly selecting one event/recipient privately.

Also inspect Edge Function names and scheduled job names/active states in the
dashboard without displaying secrets. Identify any existing staff notification
consumer/n8n workflow; prevent concurrent legacy delivery. Obtain/verify a
recoverable private database backup before approving SQL; never commit backups.
Do not assume Free project backups are available or that a UI screenshot is a
backup. The migration is transactional but not idempotent and takes table locks;
apply only when no delivery job is active and after compatibility review.

## Separate approval gates — none granted by this document

1. **Migration:** review the exact updated supabase_direct_notifications.sql and
   preflight/backup evidence; request approval for that exact file. Apply once
   manually or through an explicitly approved connection, never original auth SQL.
2. **Disabled configuration:** request approval to set NEW Supabase Edge secrets
   listed below and DEFECTRAG_NOTIFICATIONS_ENABLED=0. Do not alter Auth SMTP,
   HF settings, existing service-role keys, staff permissions or unrelated secrets.
3. **Disabled deployment:** request approval to deploy ONLY staff-notifications
   with index.ts,worker.mjs,direct-email.mjs and its reviewed verify_jwt=false
   configuration. Do not deploy corrective-actions or the React/HF application.
4. **Disabled checks:** validate deployment logs/module imports and disabled POST
   response503 notifications_disabled. Verify anon/authenticated claim/snapshot
   RPC denial and service-role grant metadata. Never invoke claim RPC as a
   read-only test: it leases/mutates outbox rows. Confirm selected QA event and
   no provider sends; disabled code cannot prove provider key validity.
5. **Controlled delivery:** request approval for exact QA event/recipient, one
   intentional notification, dispatch timing and gate change to1. An existing
   pending QA event can be used ONLY with explicit approval; do not reset sent
   rows or approve the applicant. A genuinely new request needs a separately
   authorized, user-controlled test account and email confirmation.
6. **Cloud scheduling:** separately approve Vault/pg_cron/pg_net configuration
   using a dedicated worker bearer stored in Vault, never literal in cron text.
   Choose a controlled future dispatch so user can shut down laptop/Docker first.
   One off-laptop QA send can satisfy BOTH initial mailbox and independence
   checks; do not resend a sent event to obtain a second demonstration.
7. **Evidence/duplicate/retry:** correlate event UUID, attempts/sent timestamp,
   provider idempotency header/response ID, provider delivery result, received
   subject/body/masked applicant/timestamp/Pending/fixed #team link. User confirms
   laptop-off interval and mailbox arrival; agent verifies cloud timestamps after
   reconnect. No claim of physical power state without user attestation.
   After explicit test authorization, invoke again:claimed0 and no second
   provider acceptance/message expected. Do not clear snapshots or `sent` state.
   Actual provider-failure/lease-loss retry proof requires a SEPARATELY approved
   safe QA fault scenario; mocked tests are not that evidence. Never break live
   Auth SMTP, change RLS or inject failures for other staff to demonstrate retry.
8. Record actual outcomes/checkpoint; only after Priority1 passes start Priority2
   backup/migration/security testing. Keep CA automation and Trello off.

## Secure provider key and server configuration — after gate2 approval

1. In Resend Dashboard -> API Keys, create dedicated `DefectRAG Developer QA`
   with Sending access, not Full access. If onboarding sender cannot be used
   with the offered scope, stop and report; do not broaden privileges blindly.
2. Store its one-time value privately in a password manager. Do not paste it
   into chat, README, React config.js, HF settings, n8n, SQL or terminal history.
3. In the EXISTING Supabase project -> Edge Functions -> Secrets, manually enter
   approved values below. Account owner/QA recipient and event ID are private
   configuration, not frontend settings. Do not send screenshots showing values.

| Name | Initial value / source |
|---|---|
| DEFECTRAG_NOTIFICATIONS_ENABLED | 0 |
| DEFECTRAG_NOTIFICATION_TRANSPORT | resend |
| DEFECTRAG_RESEND_API_KEY | dedicated Sending-access key |
| DEFECTRAG_EMAIL_FROM | onboarding@resend.dev |
| DEFECTRAG_EMAIL_SANDBOX | 1 |
| DEFECTRAG_EMAIL_QA_RECIPIENT | Resend-owner email == active verified Developer email |
| DEFECTRAG_EMAIL_QA_EVENT_ID | ONE reviewed authorized QA event UUID, canonical DB spelling |
| DEFECTRAG_NOTIFICATION_WORKER_SECRET | new cryptographically random dedicated bearer, at least32 characters |

Supabase supplies SUPABASE_URL and legacy SUPABASE_SERVICE_ROLE_KEY server-side;
verify availability without exposing/replacing them. Provider key and worker
bearer are DIFFERENT secrets. Store the worker bearer privately for later Vault
setup. Existing DEFECTRAG_N8N_* values are not required for direct transport and
must not be copied into this workflow. Keep old n8n staff notifications inactive.

## Stop/rollback

On migration failure:transaction rollback, inspect error; no blind retry.
On deployment/import/configuration failure:keep delivery0; fix/review or restore
previous function, not database data. After activation, separately authorize
delivery0 and stopping its scheduler. Retain outbox/snapshots/clock for recovery.
Do not drop columns/tables, disable MFA, revert Auth SMTP, re-enable n8n SMTP,
clear idempotency state or revoke existing accounts as a rollback.

Primary references checked20October2026:
- https://resend.com/docs/knowledge-base/403-error-resend-dev-domain
- https://resend.com/docs/dashboard/api-keys/introduction
- https://resend.com/docs/api-reference/api-keys/create-api-key
- https://resend.com/docs/dashboard/emails/idempotency-keys
- https://resend.com/pricing
- https://supabase.com/docs/guides/functions/secrets
- https://supabase.com/docs/guides/functions/schedule-functions
