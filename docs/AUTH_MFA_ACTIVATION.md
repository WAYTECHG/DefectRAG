# Staff registration, native TOTP and notification automation

Implementation milestone: 20 October 2026. **Inactive; not deployed or activated.**
The existing React design, password login, allowlist, private workspaces, public
Gallery, guest Demo, models and RAG remain the baseline. No SQL has been executed.

## What the prepared implementation does

| Component | Behavior |
| --- | --- |
| `AccountSecurity.jsx` | Existing dashboard styles; verified-email registration/request status; native authenticator QR/challenge/verification; developer approve/reject/revoke; delivery status/manual dead-letter retry. |
| `authSecurity.mjs` | Thin Supabase SDK/RPC adapter. No local OTP verification or membership writes. Enrollment secrets remain transient component state, cleared after verification/cancellation/unmount. |
| Additive SQL | Existing members remain unchanged/approved. New users get a pending request only. Versioned atomic decisions, audit, soft revocation and outbox. New switches default off. |
| Backend | When explicitly enabled, fresh Supabase-verified membership/AAL posture before protected repository/model operations; no legacy authorization cache reuse. Private images are fetched under the user JWT. |
| Private RLS/Storage | Existing owner/team policies remain; restrictive guards intersect them. Existing privileged RPCs inherit the updated membership/MFA helper checks. |
| Trusted worker | Claims durable leased events; authenticated HTTPS webhook; checks matching completion receipts; bounded retries/dead letters; no permissions or model responsibilities. |
| n8n template | Inactive authenticated Webhook → validate minimal event → send plain-text SMTP → verify provider acceptance → respond. No OTP or privileged database credentials. |

Developer access management always requires active developer membership and native
AAL2, even while mandatory MFA for ordinary workspace operations is off. Applicants
cannot select roles, approve themselves or gain team access by enrolling a factor.
Verified existing users can submit their request after sign-in; email confirmation
may initially create an Auth identity without any session. A denied/revoked request
cannot silently re-register to undo a decision. Reconsideration is an explicit
future administrative policy, not an automatic applicant bypass.

The SQL forbids self-decisions and protects the last active developer. It never
grants the developer role through an applicant approval. No verified-factor-removal
control is exposed by this new UI; unfinished enrollment can be cancelled and
retried after an interrupted setup.

## Files to review

1. `deployment/supabase_auth_mfa.sql`: the only new migration. Apply once, after
   existing Team, conversation and Personal migrations. It does not re-run or edit
   those earlier migrations, move records or touch Gallery tables/functions.
2. `deployment/supabase/functions/staff-notifications/worker.mjs` and `index.ts`.
3. `deployment/supabase/config.toml`: gateway JWT verification is off only for this
   purpose-secret-authenticated worker. Its handler independently requires the
   long dedicated bearer secret. It is not a public dispatcher.
4. `deployment/n8n/staff-notifications.json`: import inactive; configure credential
   references and verified sender before testing. No credentials are bundled.
5. `deployment/auth_public_config.example.js`: public disabled examples only;
   preserve the installed project's existing URL/publishable key.

### Database authorization matrix

| Surface | Caller / enforcement |
| --- | --- |
| Own security status | Signed-in caller only; own membership/request/MFA posture; no team data or directory. Available at AAL1 to avoid setup deadlock. |
| Submit request | Signed-in email-confirmed caller; DB registration switch on; own ID from `auth.uid()`; no role input; idempotent. |
| Access directory, decisions, audit, retries | Active developer plus AAL2 with an existing verified native TOTP factor. Version conflicts reject stale decisions. |
| Private Team/Personal tables and buckets | Active allowlist membership, original owner/scope rules, plus AAL2/current verified TOTP when DB mandatory MFA switch is on. |
| Existing archive, restore, conversation, note/review and stats RPCs | Their existing staff/developer checks now resolve through the active-membership/MFA helpers. Security-definer functions remain explicitly guarded. |
| Outbox claim/finish | Execute granted only to trusted service role; function checks validated role too. No browser table mutations or webhook credentials. |
| Configure registration/MFA switches | SQL-owner-only function, not granted to browser or service role. App cannot activate mandatory MFA. |
| Demo/public Gallery | Existing isolated guest permissions preserved; public snapshots remain opt-in. No staff MFA bypass for private-source publication/moderation. |

## Configuration (do not activate yet)

| Location | Setting | Initial value / purpose |
| --- | --- | --- |
| Public dashboard config | `authWorkflowEnabled` | Missing/false: existing UI/auth behavior. Later true exposes setup and management UI. |
| Public dashboard config | `registrationEnabled` | Missing/false: no self-registration form. Later true after SMTP/registration review. |
| HF backend variable | `DEFECTRAG_AUTH_WORKFLOW` | Missing/0: legacy path. Later 1 enables fresh posture/proxied private images. Requires new SQL first. |
| SQL settings | `registration_enabled`, `mfa_required` | Both false after migration. Changed only in separately authorized activation. |
| Edge secret/config | `DEFECTRAG_NOTIFICATIONS_ENABLED` | Missing/0: worker sends nothing. Later 1 only after test-mail approval. |
| Edge secret | `DEFECTRAG_NOTIFICATION_WORKER_SECRET` | Dedicated random secret, at least 32 characters. Used by trusted scheduler to invoke worker. |
| Edge secret | `DEFECTRAG_N8N_WEBHOOK_URL` | Reachable production HTTPS webhook endpoint, not localhost or test URL. |
| Edge + n8n credential | `DEFECTRAG_N8N_WEBHOOK_SECRET` | Separate random secret, at least 32 characters. Native Header Auth credential name `X-DefectRAG-Webhook-Key`. |
| Edge built-in secrets | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Trusted Edge environment only. Not HF/React/n8n. This privileged key must not be copied into notification payloads. |
| n8n server credential | SMTP connection + verified sender | Provider-approved host, TLS/port, username/password and sender. Configure workflow placeholders. |

Supabase Auth also needs external-user custom SMTP, permitted Site URL/redirect
origins (including the actual HF app origin), native TOTP enabled and appropriate
signup/rate-limit/CAPTCHA policy. Supabase default Auth email is not an external
applicant service: it is restricted to Supabase project organization team addresses
and currently two messages/hour. Application staff membership is unrelated to that
organization list. No current project SMTP or MFA settings have been inspected.
Confirmation links and resets use Supabase, not n8n. TOTP uses an authenticator,
not email. See [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp)
and [native TOTP](https://supabase.com/docs/guides/auth/auth-mfa/totp).

### Laptop / local n8n offline

Access requests, decisions and outbox inserts commit together in Supabase. A failed
notification never reverses approval or grants access. Login does not contact n8n.
An always-available Supabase scheduled worker can retry while the laptop is off;
it cannot reach a local n8n instance on a powered-off laptop. Events stay queued,
then become dead-letter after eight delivery attempts. The developer can retry
dead-letter events from the UI when the endpoint returns.

For unattended delivery, n8n must run on an approved always-on host with a reachable
authenticated HTTPS webhook. No free hosted n8n availability or paid service is
assumed. An approved laptop tunnel can provide temporary reachability while on;
it is not always-on delivery and should expose only the webhook, not the admin UI.
An n8n outage does not affect staff authorization or ordinary login. A Supabase
Auth SMTP outage can still delay email confirmation/reset, independently of n8n.

After separate deployment approval, schedule the Edge worker using Supabase
Cron/pg_net and Vault. Store the worker endpoint and its dedicated invocation secret
in Vault; the schedule sends POST with `Authorization: Bearer <worker secret>`.
Do not invoke it from React or put secrets literally in checked-in SQL. Confirm
Cron/Edge availability and free-plan quotas before scheduling. No scheduler is
installed or activated by this milestone.

Outbox jobs lease for five minutes, retry with 30-second exponential backoff capped
at one hour, and stop after eight attempts. Decisions supersede older queued jobs.
Concurrent claims use `FOR UPDATE SKIP LOCKED`; unique event keys prevent duplicate
decision events. Stable IDs accompany retries. Delivery is **at least once**:
SMTP may accept a message before an acknowledgment is lost, causing a duplicate
on retry. A message already in flight may arrive after a later decision/revocation.
The authenticated portal is always authoritative. Sent means SMTP accepted the
recipient, not verified inbox delivery. A provider with idempotent send support is
an optional future improvement. No exactly-once guarantee is made.

## Safe activation sequence (requires new approval)

1. Preserve a database backup and developer recovery access to the Supabase
   Dashboard. Review migration diff, current policies/grants and local test report.
   Do not run previous workspace SQL again.
2. Manually apply **only** the reviewed new migration after approval. Both switches
   remain false; no staff permissions or accounts are changed automatically.
3. Approve/deploy compatible code with backend workflow enabled and public
   `authWorkflowEnabled:true`, but registration false, notifications off and DB MFA
   false. Verify existing workspaces, Gallery and isolated anonymous Demo.
4. Existing developer signs in, enrolls a native authenticator, verifies a real code
   and tests AAL2 access management in a second session. Store the authenticator's
   backup securely outside the project; DefectRAG does not generate recovery codes.
   Keep a separate authorized Supabase administrator recovery path. Inform/enroll
   existing staff before any enforcement. TOTP setup does not grant membership.
5. After separate enforcement permission and successful developer tests, the SQL
   owner can call `select public.defectrag_configure_auth(false,true);`. This refuses
   activation without a verified TOTP factor on an active developer. Verify a
   still-working developer session and direct RLS/Storage/backend denial at AAL1.
6. With explicit external-signup/mail permission and SMTP verified, the owner can
   enable DB registration (`defectrag_configure_auth(true,true)`), enable the public
   registration flag and appropriate Supabase Auth signup configuration. Test a
   dedicated applicant: confirmation → pending denial → developer approval → TOTP
   → protected access. Use a second developer/non-staff account where authorized.
7. After separate Edge/n8n deployment and real-mail permission, configure private
   credentials, import the workflow inactive, test a mail sink, activate delivery
   and schedule the trusted worker. Verify retries and sanitized logs.
8. Test revocation with a still-valid AAL2 JWT; direct REST, RPC, private Storage,
   queued inference/RAG, images/reports and exports must reject new operations.
   Record live passes separately from mocked software tests.

### Lockout / rollback / recovery

- Lost authenticator: verify identity through the independently controlled
  Supabase-admin process. The administrator resets only the affected native MFA
  factor using Supabase's supported administration tools. The account then enrolls
  and verifies a replacement. No automatic email/n8n MFA reset is implemented.
- If enforcement creates a verified operational lockout, an authorized database
  owner can call `defectrag_configure_auth(false,false)` as an explicitly approved
  emergency rollback. Keep registration/delivery disabled, record the incident and
  re-enroll before restoring enforcement. Browser/developer RPCs cannot call this.
- Soft-revoked rows and all inspection records remain. Self-service registration
  cannot restore a revoked membership. Administrative reinstatement needs a
  separately approved policy; deleting data is unnecessary.
- Do not roll back by merely disabling the frontend/backend flags while DB MFA is
  active. That hides enrollment and may reintroduce stale preflight behavior. Keep
  compatible code, stop notification scheduling if needed, and use the authorized
  owner-controlled switch. Do not undo old migrations or overwrite a database.

## Revocation and remaining verification limits

New enabled-backend operations fetch fresh Supabase authorization. Database helper
checks apply to ongoing RLS/RPC access even with a still-valid JWT. Operations
already authorized and running may finish or fail on the next database operation;
this does not cancel an in-flight GPU job. Current verified-factor existence is
checked in addition to JWT AAL2 so factor removal is not a session bypass.

The enabled app no longer mints new private signed image URLs in normal UI/backend
paths. Previously issued application links can last **10 minutes (backend) or
15 minutes (Staff page)**. They remain bearer capabilities until expiry. Copies
already downloaded or displayed in browser memory cannot be recalled. Supabase
Storage also allows authorized users to issue signed links directly; RLS does not
retroactively invalidate such links. Revocation cannot promise recovery of data
already disclosed to an authorized user.

Local reports are `results/auth-mfa-boundary-tests.xml` (55),
`results/auth-regression-tests.xml` (56), `results/auth-gallery-tests.xml` (22,
including 19 repeat Gallery regressions), `results/auth-frontend-tests.xml` (49)
and `results/auth-rag-regression-tests.xml` (9 existing assistant-behavior checks).
There are 123 distinct Python cases and 49 frontend cases; repeated Gallery
checks are counted only once in the Python total. The compact summary and exact
review-migration LF hash are in `results/auth-mfa-milestone.json`.
Local/static/cloud builds are isolated under `runtime/auth-build/`; their CSS
matches the existing `index-Bn4HF2vD.css`. Existing builds are preserved.

Software tests use mocked Supabase MFA/posture responses and fake SMTP/n8n; they do
not prove live TOTP, SQL/RLS correctness or email delivery. The migration is not
executed by tests. Deno/Edge runtime and n8n import/execution need deployment-stage
verification. A real regular-staff and non-staff account is still needed for full
live negative/role tests. No production readiness claim is made before these gates.

## Repeating local software checks when code changes

Use the existing complete Python environment, not the incomplete source `.venv`.
In this checkout that interpreter is
`development-support/zerogpu-phase1/.venv/Scripts/python.exe`. No packages were
installed. The following commands use fixtures, not native models or cloud calls:

```powershell
$env:DEFECTRAG_FACTORY_ONLY='1'
$env:USE_TF='0'
& .\development-support\zerogpu-phase1\.venv\Scripts\python.exe -m pytest tests/test_auth_mfa.py tests/test_space_security.py tests/test_personal_workspace.py tests/test_auth_gallery.py tests/test_gallery.py tests/test_application.py tests/test_workflow_fixes.py tests/test_history_archive.py tests/test_inspection_answers.py -q
Push-Location frontend
npm test
Pop-Location
```

Windows in-process API tests need local socketpair access. Under the restricted
sandbox they stalled in asyncio socketpair setup; unrestricted fixture-only runs
passed after that diagnostic. Do not change application networking to work around
the test sandbox. The initial missing dependency and oversized test-parameter ID
issues were corrected by reusing the complete environment and bounded test IDs.
