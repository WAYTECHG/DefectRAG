# Current operating status — 26 October 2026

Owner selected the **local operating edition**. See [LOCAL_OPERATION_20261026.md](LOCAL_OPERATION_20261026.md) for startup, scope and limitations.

- Developer registration notifications: existing independent cloud delivery remains active and unchanged.
- Corrective Action schema/security: installed and native-account tests completed within the recorded scope.
- Real Supabase → local n8n → no-relay SMTP sink → Supabase receipt/finalization: PASS26October; one accepted test message and zero real emails.
- Same disposable case lifecycle: Closed/version7 with audited transitions and timestamps.
- Production Corrective Action delivery and schedules: OFF. Local means a verified manual demonstration, not automatic real mail or laptop-off operation.
- Always-on hosting and Multimodal RAG: deferred by the owner. They do not block running the current local application.

Detailed evidence: [CA_N8N_COMPLETION_20261025.md](CA_N8N_COMPLETION_20261025.md).
The rollout notes below are historical; do not repeat an old migration, approval or credential step because it says pending.

## Historical development and rollout record
# Automation milestones — inactive development, 20 October 2026

Current status (24 October): automatic Developer notifications are ACTIVE and
verified independently of n8n; see DEVELOPMENT_PROGRESS.md. Corrective actions
remain inactive. Their first actual PostgreSQL contracts now pass; live Supabase
catalog audit confirms the corrective schema/Edge bridge are not yet installed.
See [corrective-action activation review](CORRECTIVE_ACTIONS_ACTIVATION.md) for
current security findings, hosting constraints and separate approval gates. The
revised draft now restricts case updates to current owner/supervisor/Developer,
all with approved Staff membership and native TOTP AAL2; production is unchanged.
The original development observations below are historical, not the current rollout.

## Audited architecture

Verified access-request RPC inserts Pending request, audit and unique recipient
outbox events. Decision RPC remains Developer/native-AAL2 protected. Existing
service-role-only claim/finish functions implement leases, eight attempts,
exponential backoff and sent/dead/superseded status. No automatic approval.
Existing Edge worker sends a minimal authenticated n8n webhook; inactive n8n
template validates, sends SMTP, checks acceptance and acknowledges. It has no
durable external-side dedup ledger. Reusing that SMTP path cannot promise exactly
one message after a crash between SMTP acceptance and outbox acknowledgment.

Auth Gmail SMTP confirmation/recovery is user-verified working. Its dashboard
credentials were NOT inspected or changed. It does not implicitly configure an
Edge Function. Live Edge secrets, cron and provider account configuration were
not inspected: no deployment/configuration claim is made.

## Milestone 1: direct provider adapter

`staff-notifications/worker.mjs` retains its existing disabled gate and bounded
execution. Opt-in `DEFECTRAG_NOTIFICATION_TRANSPORT=resend` uses HTTPS directly,
with no n8n URL, Docker, laptop or new dependency. Legacy transport is retained
for compatibility; do not enable both consumers of the same outbox.

New REVIEW-ONLY `deployment/supabase_direct_notifications.sql` adds two nullable
snapshot columns and a private dispatch clock, plus service-role-only RPCs.
It changes no membership, auth flags, existing RLS or Gallery schema. Claims are
globally serialized to at most one event per 30 seconds. Original uniqueness,
leases, attempts and retry statuses are reused. Request timestamp is database
supplied; proposed plain-text body masks applicant email, strips control chars,
and contains only a fixed authenticated workspace link. No image links/tokens.

Exact provider body is saved before sending. Retries reuse saved bytes and
`Idempotency-Key: defectrag/<event_id>`. After 23 hours from first preparation,
ambiguous sends are quarantined, including after manual dead-letter retry.
Do not delete that timestamp to resend. This avoids automatically replaying an
accepted email after Resend's 24-hour deduplication window. Provider acceptance
is not inbox delivery; existing `sent` status means accepted by provider, not read.
Concurrent delivery configuration/sender changes require draining/stopping the
worker and reconciling pending snapshots first. User status can change after
dispatch; workspace remains authoritative.

### Provider choice without a domain

Recommended initial QA option: Resend's test sender to the SAME email address
as the Resend account owner, which must also be the intended Developer recipient.
No custom domain is needed for this restricted test, but arbitrary Developers
and applicants cannot be emailed from the test domain. The adapter enforces
requested-events-only, exact QA recipient AND one configured outbox event ID in
sandbox mode. SQL claims only that selected event; unrelated queued rows are not
leased/sent. Review the chosen QA event before enabling. Applicant approved/rejected/revoked templates are implemented
for later verified-domain operation, not available under the no-domain sandbox.

Resend Free pricing currently lists 3,000 emails/month, 100/day; reconfirm quotas
before activation. The application limit is throughput, not a shared account daily
quota. Provider 429 is retried. Gmail SMTP via a separate Edge SMTP client would
need separate credential configuration and cannot provide provider idempotency.
Brevo free-address verification is not equivalent to domain authentication;
Gmail-owned domains cannot be authenticated by this project. No provider account
has been created or selected on the user's behalf.

Primary references checked 20 October 2026:
- https://resend.com/docs/knowledge-base/403-error-resend-dev-domain
- https://resend.com/docs/dashboard/emails/idempotency-keys
- https://resend.com/pricing
- https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC
- https://supabase.com/docs/guides/functions/schedule-functions

### Activation gates — separate approval required

1. Review additive SQL and existing schema preflight. Apply manually only after
   approval; no migration has been run by this task.
2. Choose provider/controlled Developer QA recipient; configure server secrets
   manually. Never put them in React, Git, chat or n8n.
3. Edge environment: existing SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY,
   DEFECTRAG_NOTIFICATION_WORKER_SECRET (dedicated >=32 characters),
   DEFECTRAG_NOTIFICATION_TRANSPORT=resend, DEFECTRAG_RESEND_API_KEY,
   DEFECTRAG_EMAIL_FROM=onboarding@resend.dev, DEFECTRAG_EMAIL_SANDBOX=1,
   DEFECTRAG_EMAIL_QA_RECIPIENT (provider owner + existing Developer email).
   DEFECTRAG_EMAIL_QA_EVENT_ID (one authorized QA request outbox event UUID;
   required in sandbox; do not point at an unrelated applicant).
   Keep DEFECTRAG_NOTIFICATIONS_ENABLED=0 until approved QA activation.
   Production sender later requires verified domain and SANDBOX=0.
4. Deploy only the reviewed Edge function. Configure Supabase Cron + pg_net with
   a Vault-stored worker bearer; scheduler must run in Supabase, not on the laptop.
   No cron SQL is autoexecuted or secret-bearing template committed here.
5. Authorize ONE QA request; verify outbox/provider event IDs, exactly one mailbox
   message, no membership grant, retries and authorization. Turn laptop/Docker
   off during a scheduled cloud dispatch and verify afterward. These tests are
   NOT yet performed and cannot be represented by mocked HTTP tests.
6. Rollback: disable dispatch gate/scheduler, retain outbox and snapshots; do not
   revert Auth SMTP, MFA, memberships, data or migrations. Do not reactivate
   legacy SMTP consumer for already-attempted events without reconciliation.

Local verification: 29 focused notification tests passed; real provider network,
cloud scheduling, live SQL and inbox acceptance remain untested/unauthorized.

## Milestone 2: local Corrective Actions

Initially Docker was stopped. After the user started it, an independent disposable
container tested the new template using the already-installed n8n 2.43.7 image
sha256:3db21366be1d3c77c1708963129c051948573019659e8873e0294be035ffc1b2.
The container used `--network none`, loopback SMTP sink and simulated Supabase
callbacks. Existing n8n/ollama containers, workflows, credentials and volumes
were not modified. All eight scenarios passed; zero external email/database calls.
Disposable container removed automatically; existing user-started containers left
running. See results/automation-n8n-local-20261020.json for exact scope/limitations.

The first real execution identified an invalid multi-line email expression; it
was corrected and the full acceptance matrix passed. CLI exit code alone proved
insufficient: the harness also checks actual execution errors, effects and sink
counts. Installed n8n requires import + execute-by-ID despite listing a deprecated
file option. A missing Python runner warning is unrelated to this JS-only flow.

### Case model and access boundary

New REVIEW-ONLY `deployment/supabase_corrective_actions.sql` creates isolated
case/history/event/effect/settings tables. Automation defaults false. No existing
table, record, staff grant, auth setting, Gallery or storage policy is changed.
All protected functions and SELECT RLS require active allowlisted Staff AND
native verified TOTP AAL2, independent of a frontend flag. Browser writes go
through bounded RPCs only; direct INSERT/UPDATE/DELETE are not granted. n8n holds
no Supabase service key and cannot modify cases, approvals or inspection records.

Case creation requires an active shared inspection, its latest completed human
Reject review by active staff, and SEPARATE explicit confirmation by current
MFA Staff. A Reject disposition alone is not a defect diagnosis. An anomaly
score/verdict is never a creation trigger. Review ID, original review text,
reviewer and confirming actor are preserved. One case per review prevents
double-click duplicates. No Personal record is automatically shared.

Cases record active owner/supervisor, priority, description, due date, optimistic
version, resolution and close dates. SQL enforces Open -> Assigned -> In Progress
-> Resolved -> Closed, explicit progress notes and cancellation. Resolved may
reopen to In Progress, clearing current resolution timestamps. Closed/Cancelled
are terminal. Reassign revoked owner/supervisor before further updates. Every
version records actor, time, state, note and assignment/due-date snapshot.

React adds one feature-gated card inside Team Workspace using existing classes;
no CSS, navigation or theme redesign. Enable public `correctiveActionsEnabled=true`
ONLY after migration/integration approval; unset/false retains current UI.
It includes creation, assignments, due dates, priorities, overdue labels, details,
linked private evidence, updates, history and delivery status. Existing protected
image access handles evidence. Auth changes clear pending case data; database
permissions remain authoritative. Lists/metrics are explicitly limited to 500
accessible cases, not a global organization KPI. Average resolution uses actual
created/resolved timestamps; no resolved cases displays no numeric value.

### Orchestration, retries and duplicates

`corrective-actions` Edge handler uses separate >=32-character dispatcher,
callback and webhook secrets, an off-by-default environment gate and DB flag.
`config.toml` disables native gateway JWT verification for this dedicated
server-to-server endpoint only; handler secret checks are mandatory. No frontend
uses these keys. Requests, response bodies and invocation duration are bounded;
one event per call, 100s maximum, 90s reserve before scheduling/claiming.

Claims use row locks, 5-minute leases, versioned unique events, eight attempts,
backoff, dead/superseded states and immutable case history. Updates/archive
supersede obsolete events. The scheduler inserts at most one 24h reminder and
one overdue escalation per case version; overdue is derived from due date,
not a replacement for lifecycle status. Archived inspections are excluded.

n8n validates the event, reserves its notification effect through a purpose-bound
callback, receives only the active supervisor's verified email and minimal case
metadata, sends SMTP, validates recipient acceptance and records a receipt.
Neither messages nor links contain private images/descriptions/auth tokens.
Only event ID + 5-minute lease capability crosses the authenticated webhook.
Callback cannot approve staff, read unrelated records or write arbitrary tables.

Effect ledger uniqueness suppresses completed duplicates. A crash after effect
reservation is AMBIGUOUS: no automatic replay, event becomes dead/manual review.
This deliberately trades delivery availability for avoiding duplicate external
side effects where SMTP has no idempotency. Staff case data remains saved.
Lost webhook receipt AFTER durable effect completion can retry and acknowledge
without another email. Provider acceptance is not proof of inbox delivery.
Trusted n8n can attest its own receipt; provider-signed receipt verification is
not implemented. A compromise of its purpose secrets can disrupt/forge delivery
status, but grants no case/staff write permission. Rotate and reconcile if leaked.

Optional Trello integration is NOT configured/implemented: SQL rejects ticket
effect callbacks and template has no ticket node, so it cannot create duplicate
tickets. Do not claim ticket synchronization tested. A later connector requires
stable case-level keys, external-ID storage and ambiguity reconciliation before
any real ticket creation. No Trello account or API token was accessed.

### Local test results and remaining tests

`deployment/n8n/test-local.mjs`: actual n8n nodes against isolated SMTP + simulated
callback authority; eight passed: confirmed send, duplicate suppression,
unconfirmed backend denial, raw prediction rejection, SMTP failure, ambiguous
effect quarantine, accepted-message/lost-receipt, retry without duplicate.
Webhook trigger/final response use fixture substitutions; production inbound
webhook authentication and real Supabase SQL are NOT exercised by this harness.

Frontend tests cover source security contracts, state/metric logic, guarded
worker requests/failures and real JSX rendering. SQL source assertions are NOT
database authorization tests. `deployment/tests/corrective_actions_local.sql`
prepares rollback-only synthetic local tests for pending/AAL1/anonymous/revoked
denial, Staff-AAL2 creation, explicit confirmation, transitions, stale versions,
history, restricted event capabilities, effect dedup and reminder dedup. It has
NOT been executed: no local Supabase/Postgres environment was available and no
database image/dependency was downloaded. Native real-user MFA and production
case lifecycle/reminder tests remain pending after approval. Read-only metadata
preflight is deployment/automation_preflight.sql (also not run remotely).

### Configuration and later activation sequence

1. Review both new additive SQL files + read-only preflight. Approve schema
   execution separately; never rerun the existing Auth migration.
2. Run isolated local Postgres tests before production SQL approval. Verify
   real pending/anonymous/AAL1/revoked RPC/RLS/storage denial and approved AAL2
   access with authorized accounts. Do not reuse private production records as
   test fixtures. Preserve Personal/Gallery regression checks.
3. Approve a compatible frontend release separately; build manifest now binds
   new worker, template and SQL test dependencies. Current working local/static
   app builds are preserved. Public feature flag remains absent/off.
4. Edge server-only config: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
   DEFECTRAG_CA_WORKER_SECRET, DEFECTRAG_CA_CALLBACK_SECRET,
   DEFECTRAG_CA_N8N_SECRET, DEFECTRAG_CA_N8N_URL (HTTPS production webhook),
   DEFECTRAG_CA_AUTOMATION_ENABLED=0 initially. DB automation_enabled=false.
5. Import inactive `corrective-actions.json`; configure fixed project callback
   URL in both HTTP nodes. n8n inbound HeaderAuth name X-DefectRAG-CA-Key, value
   CA_N8N_SECRET. Callback HeaderAuth name Authorization, value Bearer followed
   by CA_CALLBACK_SECRET. Configure verified SMTP sender/credential separately.
   No DB key, browser key, service role or production secrets in workflow JSON.
6. Import inactive `corrective-actions-scheduler.json`. Dispatcher HeaderAuth:
   Authorization: Bearer CA_WORKER_SECRET. It polls every 15 minutes and requests
   one durable event. Configure the same fixed project endpoint. This scheduler
   has not been activated or tested against cloud services.
7. Only after approved integration QA: activate the endpoint, DB gate, n8n
   workflows and dashboard flag in that order. Never activate old staff SMTP
   notification workflow for Milestone 1. Verify human-only creation and one
   notification, due/overdue, retry, revocation, private images and recovery.
8. Rollback: public flag false, Edge gate0, DB gatefalse and stop new n8n
   workflows/schedule. Retain cases/history/outbox/effects, existing auth and
   inspection data. Reconcile ambiguous effects manually; never clear the effect
   ledger or replay its SMTP node directly. Database backup/restore should be
   reviewed separately; there is no new destructive recovery button.

### Hosting assessment AFTER the isolated workflow test

Local Docker is sufficient for development, not reliable unattended operations.
When the laptop stops, n8n schedules stop and localhost cannot receive Supabase
webhooks. No public tunnel was opened. Pending events/cases remain in Supabase;
expired claims can resume, while ambiguous effects require human reconciliation.
Production Edge bridge requires a reachable HTTPS n8n endpoint, so the local
fixture test is not a production connectivity demonstration.

Recommendation: keep production corrective-action automation disabled. For
always-on use, self-host the free n8n Community Edition on an already-approved
always-on host with HTTPS, persistent encrypted credentials/DB, backups and
monitoring, or separately approve paid managed hosting. Community software does
not imply free always-on infrastructure; no free uptime guarantee is asserted.
No paid service/tunnel/domain purchase or cloud account was created. Milestone 1
can run independently on Supabase Cron + Edge while laptop/Docker are off.

Primary n8n references:
- https://docs.n8n.io/hosting/installation/docker/
- https://docs.n8n.io/hosting/community-edition-features/
