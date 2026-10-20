# Developer email activation — controlled preflight, 20 October 2026

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
