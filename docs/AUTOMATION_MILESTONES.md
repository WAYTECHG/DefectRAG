# Automation milestones — inactive development, 20 October 2026

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
requested-events-only and exact QA recipient in sandbox mode. Other events fail
closed and retain retry/dead status; do not enable sandbox against a mixed backlog
without reviewing it. Applicant approved/rejected/revoked templates are implemented
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

Local verification: 28 focused notification tests passed; real network, SMTP,
cloud scheduling, live SQL and inbox acceptance remain untested/unauthorized.

## Milestone 2: local Corrective Actions

Docker CLI exists, but `docker ps` reported that Docker Desktop Linux engine is
not running. No container was started or changed. Local n8n end-to-end execution
requires Docker availability and isolated test credentials/sinks. A stopped
laptop cannot execute local reminders or receive cloud webhooks. Production
automation stays disabled until approved always-on hosting exists.
