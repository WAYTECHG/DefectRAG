# Automatic Developer notifications — controlled rollout, 22 October 2026

## Current verified state — 24 October 2026

Automatic Developer-only notifications are ACTIVE and controlled verification passed.
One existing five-minute Supabase Cron job, the database gate and Edge delivery
are enabled. DEVELOPER_ONLY=1, SANDBOX=0, transport=resend; the existing sender,
recipient and credentials are retained. No local Docker/n8n/HF deployment is needed.

The fresh QA request remained Pending with no staff membership. After one
controlled failed attempt at the live outbox boundary, the real13:30UTC scheduler
invocation on23October returnedHTTP200/claimed1/accepted1. The event became
sent/attempts2 at13:30:02.889848UTC (21:30:02MYT). ResendHTTP200, matching idempotency
key, Sent/Delivered events and exactlyone new email were verified. The owner
reported the laptop fully off21:29–21:36MYT and supplied a mailbox screenshot.
Delivery falls inside that window; no independent hardware telemetry is claimed.
The13:25HTTP503/notifications_disabled was the expected closed delivery gate during
preparation, before activation; the actual13:30 delivery returnedHTTP200.

Later13:35/13:40 cron ticks succeeded without another send. A rollback-only native
RPC test proved the sent event is not claimable and its row is unchanged, without
calling the provider. Historical5 outbox metadata and staff fingerprints match;
MFA/registration remaintrue, worker authorization remains protected. No approvals,
old-event resets, extra email, permission/migration change or n8n activation.

Evidence: `results/email-automation-activation-20261023/final-verification.json`,
`live-postflight.json`, `provider-and-off-laptop.json`, replay SQL and screenshot.
Checkpoint and completion notes are in DEVELOPMENT_PROGRESS.md.

### Verification boundaries

- Retry verification used a deliberately recorded failure through the existing
  live claim/finish RPCs, followed by actual automatic cloud recovery. A real
  Resend outage/HTTP429 was not induced.
- Native sent-event exclusion and no duplicate provider messages were verified;
  the same provider idempotency key was not resent as another network request.
- The accepted message arrived in **Spam**, not the Inbox. Provider Delivered
  means the receiving mail server accepted it; inbox placement is not guaranteed.
  The intended recipient can mark it Not spam. A verified-domain sender and
  broader recipient rollout need separate review; no domain purchase was made.
- The test-domain sender still targets only the configured Resend-owner Developer.
  Applicant decision emails and n8n/Corrective Actions remain disabled/separate.
- Preserve the80-attempt UTC-day budget, eight-attempt limit,23-hour quarantine,
  first-activation backlog cutoff, immutable snapshots and manual approval/MFA.
  Do not rerun activation SQL or reset/replay this completed QA event.

### Pause if needed

Set Edge DEFECTRAG_NOTIFICATIONS_ENABLED=0, then use the reviewed
`deployment/email_automation_pause.sql` to close the database gate and deactivate
only this job. An already accepted message cannot be recalled. Retain outbox,
receipts and all account/workspace records; do not revert authentication migrations.

The remaining sections are historical installation/development records and
procedural reference; their inactive/not-yet-tested wording is superseded above.

## Historical live checkpoint: inactive installation complete

After explicit approval, all three installation files below succeeded once.
pg_cron1.6.4 and pg_net0.20.4 are installed; Vault0.3.1 retained. Exactly one
expected five-minute job is INACTIVE, database gate false, activation timestamp
null and zero claims/queued HTTP requests. Private table RLS/grants and RPC
execution boundaries verified through live metadata. Outbox/staff fingerprints
are identical before and after; MFA/registration remain enabled.

Only existing hyper-worker/staff-notifications.ts was deployed. Its persisted
source after reload exactly matches packageSHA256
0357e1db56ca942f8cdad8b86eda8a200fe43642c35d1ad4b549d2f84eafea3c.
Public POST still503notifications_disabled; diagnostic without bearer401.
No secret/configuration change, Vault entry, real email, activation or HF release.
Evidence: results/email-automation-install-20261022/.

Next disabled-mode configuration/Vault credential entry needs separate approval;
activation remains a later gate. The prepared/untested wording below describes
the development checkpoint; native object installation/ACL checks above now pass.
Actual scheduled execution and laptop-off delivery are still not verified.

## Scope and current status

The one-email QA path is verified through the real worker, outbox, Resend HTTP200,
Delivered event, matching provider idempotency key and user-confirmed receipt.
That event is sent and will never be reset for another test.

The existing sandbox deliberately accepts ONE event UUID. Simply scheduling it
would not notify the Developer about new requests. The new, inactive extension
adds a Developer-only selection mode, retaining the existing outbox, snapshots,
leases, backoff, maximum eight attempts and 23-hour ambiguity quarantine.

Architecture: Supabase Cron → private database enqueue function → pg_net →
existing hyper-worker → restricted claim RPC → immutable outbox snapshot → Resend.
No laptop, local Docker, n8n, React rebuild or Hugging Face deployment is involved.
Availability depends on the Supabase project and provider remaining operational.

This remains restricted test-sender use: only the configured Resend account-owner
Developer mailbox can receive requests. It is not general applicant mail delivery.
Additional recipients/applicant decision messages require a verified sender domain
and a separately reviewed rollout. No domain purchase or paid service is proposed.

## Live preflight (SELECT only)

`deployment/email_automation_preflight.sql` returned:

- Vault 0.3.1 installed; pg_cron and pg_net absent.
- Auth registration and mandatory MFA remain true; clock WHERE fix present.
- One active, verified Developer.
- Existing outbox: one requested/sent, two requested/superseded, two approved/queued.
- New automation objects absent; no source migration/activation has been applied.

Evidence: `results/email-automation-readiness-20261022/live-preflight.json`.
The two queued applicant messages will NOT be claimed in Developer-only mode.
The first activation timestamp excludes all older backlog without altering it.

## Reviewable inactive installation (approval required)

Apply the following in order ONLY after explicit production approval:

1. `deployment/supabase_developer_notification_extensions.sql` enables the
   supported pg_cron and pg_net extensions. No jobs, sends, drops or reinstall.
2. `deployment/supabase_developer_notifications.sql` adds an RLS-protected private
   settings/budget table, initially disabled, and a service-role-only claim RPC.
   It does not replace the proven direct claim/snapshot/finish RPCs or change
   existing staff, Auth, storage, personal/team/Gallery permissions or records.
3. `deployment/supabase_developer_notification_schedule.sql` adds a private request
   ID log and owner-only scheduler helper. It creates exactly one five-minute job,
   explicitly inactive in the same transaction. A conflicting job causes STOP.
4. Deploy ONLY the tested `runtime/email-developer-release/index.ts` to the
   existing `hyper-worker` / `staff-notifications.ts`, with delivery still0.
   Do not recreate the function, reset JWT configuration, touch Auth SMTP or
   deploy the frontend. Retain the previous verified diagnostic bundle for
   code rollback. Verify persisted full-source SHA256 after dashboard reload.

Current package hash:
`0357e1db56ca942f8cdad8b86eda8a200fe43642c35d1ad4b549d2f84eafea3c`.
Regenerate with `node deployment/supabase/build_email_function.mjs --developer`
if source changes; never deploy a package with mismatching source hashes.

Do not execute the original auth/direct-email migrations again.
Extensions create background capabilities, but this installation does not itself
send mail. The new SECURITY DEFINER functions use an empty search_path and explicit
schema names; browser roles cannot execute them or read their private tables.
The scheduler helper is additionally denied to service_role; cron's postgres owner
executes it. Privileged Supabase operators remain trusted administrators.

## Configuration and private credential step (later approval)

Keep existing provider key, worker bearer, QA recipient, sender, Supabase service
key, Auth SMTP and all Hugging Face settings. No credentials enter React or Git.

| Edge setting | New Developer-only value |
|---|---|
| DEFECTRAG_NOTIFICATIONS_ENABLED | 0 until separate activation |
| DEFECTRAG_NOTIFICATION_TRANSPORT | resend (retain) |
| DEFECTRAG_EMAIL_DEVELOPER_ONLY | 1 |
| DEFECTRAG_EMAIL_SANDBOX | 0 |
| DEFECTRAG_EMAIL_QA_RECIPIENT | retain the verified account-owner Developer |
| DEFECTRAG_EMAIL_FROM | onboarding@resend.dev (retain) |
| DEFECTRAG_EMAIL_QA_EVENT_ID | retain; unused for automatic selection |

Although SANDBOX becomes0, DEVELOPER_ONLY=1 keeps the strict sender/recipient and
requested-event restrictions. It does not enable unrestricted production sending.
Both flags must agree; incompatible or malformed modes fail before any claim.

Owner privately stores the SAME existing worker bearer in Supabase Vault under
`defectrag_notification_worker_bearer`. Enter and save it directly in the dashboard;
never paste it in chat, shared SQL, cron commands, terminal history or screenshots.
This is a server-to-server copy of the existing dedicated credential, not an Auth
password, Resend key or service-role key. Do not rotate unrelated credentials.
Vault setup needs its own explicit production confirmation/user private entry.

While delivery0, the no-network diagnostic can confirm ready_for_developer_only
true with boolean-only output. The historical QA UUID may still be used in its
diagnostic header; it cannot dispatch. That diagnostic does not prove live SQL or
provider delivery. Ordinary public POST must still return503notifications_disabled.

`email_automation_status.sql` is a SELECT-only check AFTER installation. It returns
flags, grants, exact job properties, Vault secret presence only, and recent request
IDs/status codes. It never reads credential values, claims events or calls HTTP.
Inspect duplicate/legacy consumers before enabling; never run n8n against this
outbox in parallel. pg_net's internal request queue temporarily holds HTTP headers;
do not expose its schema via the Data API or grant access to untrusted SQL users.

## Separate activation and first real test

1. Obtain approval for the exact `deployment/email_automation_enable.sql`, recipient,
   recurring delivery and bounded retries, plus Edge delivery1. Do not treat the
   earlier one-event approval or general work request as approval for unreviewed SQL.
2. With Edge delivery0, apply the guarded activation transaction. It starts one
   inactive five-minute job and opens the private database gate. First activation
   sets enabled_at; later resume retains it so unsent current requests can recover.
3. Verify status/permissions, then save Edge delivery1. New eligible requests are
   delivered on a later five-minute tick. Never invoke/resend the old QA event.
4. Authorize a genuinely fresh user-controlled QA request separately, keep it
   Pending, and choose a future cloud tick. The owner can then turn the Windows
   laptop and local Docker off. After reconnect, compare cron run metadata,
   pg_net response, outbox, Resend request/idempotency/Delivered and mailbox times.
   Record the owner's off-laptop attestation; a mocked test cannot prove power state.
5. Do not approve/reject/revoke accounts as part of email testing. Notification
   delivery never grants staff privileges, bypasses MFA or changes approval state.

Every call claims at most one row at a time; existing global30-second lock and
worker100-second budget remain. At most80 leased Developer attempts per UTC day,
including retries, are allowed by the new private counter. Unstarted rows remain
queued. Daily budget resets at UTC midnight, not local midnight. This leaves
headroom against the provider's listed100/day test-account limit, but it cannot
account for unrelated use of the same Resend account or guarantee provider quotas.
Provider429/outages retain durable backoff; reaching the daily cap delays work.
No fixed one-email-per-day guarantee or exactly-once transport claim is made.

Only current Pending requests to the configured active, verified Developer are
selected. Approved/rejected/revoked applicant notifications, old backlog, other
recipients, superseded versions, sent/dead rows and non-due retries are excluded.
Revocation is rechecked before snapshot preparation. A concurrent decision after
dispatch can make an email stale; its link always opens the authoritative workspace.

## Monitoring, pause and rollback

Use cron run records plus `email_automation_status.sql`; do not query the credential-
bearing net request queue. pg_net responses have limited retention (currently six
hours by default); outbox/snapshots and request-ID records persist independently.

For a reversible pause, first save Edge delivery0, then approve/run
`email_automation_pause.sql` to close the database gate and mark only this job
inactive. No jobs, extensions, records, snapshots or audit history are deleted.
An already-running send may still finish; pause is not cancellation of accepted mail.
For code rollback, keep both gates closed/job inactive and restore the prior tested
worker. Never restore the broken clock statement or re-enable n8n automatically.

## Tests and remaining gaps

- 62 offline worker/configuration/regression tests passed, including strict
  recipient/kind filtering, no credentials in output, disabled/unauthorized gates,
  HTTP429/backoff, duplicate suppression and lost acknowledgments.
- 9 compiled-package checks passed, including Developer-mode diagnostic and
  correct filtered RPC arguments through an injected network fixture.
- Two SQL contract scripts passed in real PostgreSQL17 Alpine, using a disposable
  container with networking disabled and no published ports/project mounts. Tested
  permissions, daily accounting/reset, retry due times, backlog/kind/version/role
  exclusion, revocation, no duplicate lease/sent replay, inactive install, missing
  Vault failure, request/credential routing, throttle, guarded activation and pause.
- SQL scheduler tests use fake cron/net/Vault contracts. Actual Supabase extensions,
  cron wakeups, Vault routing, live retry and laptop-off delivery remain UNVERIFIED.
- No production migration, extension installation, Vault write, worker deployment,
  secret/flag change or email has occurred in this development milestone.
- New official postgres:17-alpine image was approved/downloaded for tests (no
  existing database image was cached). Only the created test containers were
  removed. Existing n8n/Ollama containers and volumes were not modified.

Primary documentation checked22October2026:
- https://supabase.com/docs/guides/functions/schedule-functions
- https://supabase.com/docs/guides/cron/install
- https://supabase.com/docs/guides/database/extensions/pg_net
- https://resend.com/docs/knowledge-base/403-error-resend-dev-domain
- https://resend.com/docs/dashboard/emails/idempotency-keys
