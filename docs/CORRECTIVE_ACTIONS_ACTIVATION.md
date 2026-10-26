# Current Corrective Action status — 26 October 2026

**Local integration and disposable lifecycle are verified. Production automation remains OFF.**
The owner chose local operation while hosting signup issues are unresolved; no paid host is required to run the application or inspect the completed n8n demonstration.

The revised owner/supervisor/Developer restrictions apply to Corrective Actions only. Existing Personal inspection/synchronization, explicit Team sharing and ordinary authorized Team collaboration remain preserved. Native security checks and the one-event sink delivery/lifecycle evidence are recorded in [CA_N8N_COMPLETION_20261025.md](CA_N8N_COMPLETION_20261025.md).

Use [LOCAL_OPERATION_20261026.md](LOCAL_OPERATION_20261026.md) for current startup and the boundary between manual local tests and inactive real notifications. No migrations, approval changes, delivery activation or spent-event replay is needed for ordinary local use. Previous pending/absent statements below are historical.

## Historical activation record
# Corrective actions: production readiness, updated 25 October 2026

NEW INACTIVE milestone25October: single-event sink-only pull bridge is prepared
and offline tested. See CA_SINGLE_EVENT_QA_BRIDGE.md for the exact review-only SQL,
baseline guard/rollback, native Developer approval, local sender/sink and separate
QA endpoint. It changes ONE existing effect-gate condition if later approved;
no production SQL/source/flags/secrets changed now.16focused new tests, actual
isolated SQL contracts and9postflight booleans pass. Native live QA remains pending.
Refresh backup before a new approved production SQL extension; do not rerun old
migrations. Existing deployed corrective-actions remains disabled.

LATEST25October: owner-approved dedicated corrective-actions Edge function is
now deployed DISABLED. Exact reviewed source compared before/after deployment;
one anonymous POST{} gives503/automation_disabled; native dashboard corroborates
one invocation/boot. CA flag absent defaults OFF; no SQL, secrets or existing
function changed. See CA_DISABLED_DEPLOYMENT_20261025.md. Positive single-event
live callbacks/real delivery and reliable hosting remain unverified; no activation
authorized. Older statements that this dedicated function is absent are historical.

Latest25October: native live case/MFA/assignment/privacy tests remain completed
within their saved24October scope. Local n8n Header Auth/schema tests and actual
native GUI simulated callback/SMTP success, duplicate suppression and receipt-loss
quarantine now PASS. Original authenticated draft retained; separate practice
workflow unpublished; temporary simulator stopped. No real cloud callback or CA
email, hosting activation or production deployment followed from these tests.
Read docs/CA_LIVE_BRIDGE_NEXT_GATE.md for the exact initially disabled Edge
deployment approval gate and outstanding single-event/local connectivity design.
Production CA automation remains OFF; Developer cloud emails remain unchanged.
The older status paragraphs below are historical, not instructions to repeat work.

Latest: owner CONFIRMED the additional Staff B approval. Audited membership drift
is reconciled; Native Stage2 passes within the limitations recorded below. No
agent approval/reversal or existing permission edit. Local hands-on n8n Stage3
starts with owner creating a separate blank workflow; no import, execution,
credential setup, callback deployment or production automation activation yet.
The earlier pending-confirmation status below is historical.

Earlier24October: native case creation/lifecycle/owner/supervisor/Developer tests
PASS against real Supabase, including former-assignee/unassigned/pending/AAL1
denial, cross-owner private row/image isolation and unchanged ordinary Team
collaboration. Final QA case Closed/version9/history9/events9, total attempts0,
effects0, automation FALSE. Original inspection/note/Gallery counts excluding
QA and existing security definitions/settings match baseline. One independently
audited Developer approval changed Staff3->4/pending2->1 at16:41MYT; owner
confirmation is pending. Do not claim membership preservation or revert it.
See final-live-check.json, final-comparison.json and access-audit-reconciliation.json
under results/corrective-actions-live-20261024/. Pending AAL2, live account
revocation and positive live service-role callback/delivery were not exercised.
Local n8n editor opened only; existing workflow untouched. Hands-on inactive import
is next after reconciliation; production automation and callback remain OFF.

Earlier status: OWNER manually installed the reviewed migration. SELECT-only
production postflight and all twelve preservation comparisons PASS; corrective-
action automation remains FALSE. Native Developer AAL2 reads/worker isolation and
anonymous denial also PASS. Existing Staff owner/supervisor/unassigned boundaries,
case lifecycle and pending/AAL1 tests are IN PROGRESS, not yet verified live.
See results/corrective-actions-live-20261024/ and DEVELOPMENT_PROGRESS.md.
The local QA console is temporary test tooling, not a deployed Staff UI change.
Local hands-on n8n follows only after live Stage2 passes. Existing automatic
Developer emails remain active and unchanged. The earlier statuses below are
historical; do not rerun the successful migration.

Earlier update: backup/recovery gate PASSED in the isolated Supabase-compatible
runtime, including original role grantors, critical row contents,38object files,
Vault decryption and native GoTrue TOTP with restored AAL guards. Fresh SELECT-only
production preflight confirms no case tables/functions and unchanged old security/
records/Developer notifications. See SUPABASE_PRIVATE_BACKUP.md and
results/private-recovery-complete-20261024/. Explicit owner migration approval is
still pending; nothing has been installed/activated. Live Corrective Actions
tests remain pending and must not be conflated with these recovery tests.
The earlier missing-backup statements below are historical.

Status: NOT activated; real corrective-action authorization tests remain pending.
Current execution sequence: see CORRECTIVE_ACTIONS_STAGED_ROLLOUT.md. Oracle
signup is blocked; local interactive n8n work may follow Stage2 without waiting
for cloud hosting. Unattended production automation still requires reliable
approved hosting. Stage1 is gated on verified private backup and explicit SQL
approval; the owner confirmed no verified backup yet.
Revision: owner/supervisor/Developer editing, requested 24 October. The prior
collaborative-edit migration/hash is superseded and is not approved for execution.
Automatic Developer emails are a separate completed, active milestone. Leave its
Cron, worker, Vault, provider and delivery flags unchanged.

## Verified evidence

Authenticated read-only catalog queries in project `zrzqpbcomlorfzszolrs` found:

- None of the five corrective-action tables or eight corrective-action functions
  installed. No migration was executed during this assessment.
- Required Staff/Team/review columns and referenced primary keys exist. Native
  MFA helpers match the definitions used by the implementation; MFA remains on.
- Personal policies retain owner checks and private storage retains Staff/MFA
  guards. Gallery's actual table is `defectrag_gallery_entries`: six rows, RLS on.
- Baseline counts: nine Team inspections, six Team notes, ten Personal inspections,
  three Staff memberships. Counts alone are not a full data backup.
- Functions page lists only `hyper-worker`; the corrective-action bridge is absent.
- Public HF config omits `correctiveActionsEnabled`, so its UI remains off.
- Developer notification database gate and Cron remain enabled.

Evidence: `results/corrective-actions-readiness-20261024/`. No private row payloads,
image contents, emails or credentials were exported. The initial gallery-name
probe was corrected to the actual gallery table before saving final evidence.

Actual PostgreSQL 17 contracts now PASS in a disposable cached official image,
with no network, ports, mounts, cloud credentials or external messages. Tests use
actual base/corrective SQL and current Auth helper SQL, with synthetic Auth tables
and JWT claims. Covered: ACLs, anonymous/pending/AAL1/unverified-factor/revoked denial,
pending/AAL1 RLS on existing cases, explicit confirmation, review uniqueness,
version conflicts, transitions/reopening/terminal states, audit history, hidden
lease columns, service-only claims, disabled automation, invalid/expired leases,
unsupported ticket effects, effect replay suppression and reminder deduplication.
The revised single-result postflight query also checks the stored editor guard.

All 16 focused React/worker/template tests pass, including actual JSX compilation
and rendering. The separate production React build passes all 186 release checks;
it is verified locally, not staged or deployed. Existing eight isolated
real-n8n/SMTP-sink tests were not repeated.
These results do NOT establish native Supabase login, live corrective RLS, webhook
authentication, cloud SMTP delivery or off-laptop n8n availability.

## Security decisions before migration

All active approved Staff with verified TOTP AAL2 may read active Team cases and
create a case from a qualifying human review. Updates (including state, note,
assignment and due date) are restricted to its CURRENT owner, CURRENT supervisor
or an active approved Developer with native TOTP AAL2. The unassigned case creator
has no edit exception. The definer RPC locks the case and checks stored assignments
BEFORE considering submitted assignments, preventing self-assignment bypass.
Authorized editors can reassign to active Staff; former assignees immediately
lose edit access unless they remain owner/supervisor or are Developers. The UI
shows a read-only explanation to other Staff; SQL remains authoritative.

New actual SQL tests cover positive owner/non-Developer supervisor/unassigned
Developer writes, denied unassigned creator/self-assignment, assignment transfer,
former-assignee denial, new-owner access, revoked-owner denial, Developer AAL1 /
unverified-factor denial and unchanged audit/event counts for rejected operations.
Team read access and Personal privacy are unchanged. Developers can additionally
read cases linked to archived sources; archived-source cases cannot be updated.

Creation requires an already shared Team inspection, its latest completed Reject
human review, a separate human defect confirmation, active assignees and a valid
due date. No AI score creates a case; Personal images are never auto-shared.
Human confirmation is an attestation, not independently verified diagnosis.

No direct browser writes, browser-readable leases or general-purpose n8n database
access. RLS limits browser reads; fixed-search-path definer RPCs enforce writes.
Callbacks authorize one effect for one event with a five-minute lease. SMTP
acceptance is not inbox delivery. Reserved but unfinished effects are quarantined
for manual reconciliation rather than blindly resent. A compromised n8n purpose
secret could forge delivery receipts; it cannot edit cases or Staff approvals.
Already issued signed image URLs remain usable until expiry, as before.

## Exact migration and backup gate

### Scope confirmation from live catalog, 24 October 2026

Reviewed 19 actual production RLS/storage policies and nine actual RPC definitions,
including their authenticated EXECUTE grants. All 14 policy definitions captured
in the earlier readiness baseline are unchanged. Existing RPCs contain no case
editor/Corrective Action dependency; required MFA remains enabled.

| Existing ability for approved Staff with required MFA | Database/backend boundary retained |
| --- | --- |
| Run Personal inspections | Backend validates `defectrag_auth_status`; Staff/Developer roles, no case assignment check |
| Save/read Personal history and images | `personal_owner_insert/read`, `personal_artifact_insert/read`: current owner + Staff/MFA |
| Synchronize Personal history | `defectrag_personal_sync_apply`: Staff/MFA + owner, immutable artifacts, versions/receipts |
| Explicitly share with Team | `defectrag_share_personal`: active owned Personal record + uploaded owned Team artifacts; no automatic sharing |
| View authorized Team inspections | `staff_read`, `team_artifacts_read`: Staff/MFA; existing archived-source restriction retained |
| Team review/collaboration | `staff_notes_insert/read`, `defectrag_append_conversation`, `defectrag_acknowledge_review`: existing Staff/MFA and active-inspection checks |
| Update a Corrective Action case | ONLY this new RPC checks current case owner/supervisor/Developer, in addition to Staff/MFA |

Unassigned Staff can still review/comment on the underlying shared inspection;
that does not authorize editing the case's state, assignments, due date or case
audit history. Case reads remain permitted for authorized Staff; assignment is
not a read filter. An unassigned case creator has no special update permission.

The revised migration alters/grants/revokes only its new case tables/functions.
It does not redefine `defectrag_is_staff`, Auth helpers, Personal sync/sharing,
Team conversation/acknowledgment, existing storage policies or existing table
grants. It adds no trigger to existing inspection/review tables. Foreign keys
protect referenced records against hard deletion after cases exist; they do not
restrict the inspect/save/sync/share/review operations above. Normal recoverable
archiving retains its established rules.

Evidence: `results/corrective-actions-boundaries-20261024/`. This was SELECT-only
live catalog verification plus migration/backend source review, not another real
account inspection run or live installation of corrective policies. Production
still has zero case tables. The case editing behavior was exercised only by the
previous isolated SQL suite; post-install native-account tests remain pending.

Review the REVISED `deployment/supabase_corrective_actions.sql`.
Canonical UTF-8/LF SHA256:
`DEACD409A1E1CBC568CA04CD2FB8090ABCF6D8BAAE44A97D4CA40DEAAE9F26A6`.
Windows checkout line endings can change the byte hash; compare normalized SQL
text or this canonical hash. The earlier 906E1110 / 58647863 hashes are obsolete.
It adds five isolated tables, four SELECT policies and eight bounded functions.
It changes no existing table policy, Staff membership, Gallery record or auth flag.
Its new automation setting defaults FALSE. It adds foreign-key dependencies;
existing data is retained and referenced users/reviews cannot be casually deleted.

Before approved execution:

1. Preserve this source checkpoint and metadata evidence. Recheck the migration
   hash and absence of ALL new objects; stop on a partial installation.
2. Make a private database backup using the project's normal approved backup
   facility or a password-prompted `pg_dump` with TLS from a trusted machine.
   Keep the dump encrypted outside Git and verify it can be listed/restored into
   an isolated test database. Database dumps contain sensitive Auth/application
   data; do not paste them into chat. Database dumps do not include Storage object
   bytes: preserve those separately. Existing source/evidence is not a data backup.
3. Request separate permission to apply ONLY this migration, with automation off.
   Do not rerun Auth, Personal, Gallery or Developer notification migrations.
4. Run `deployment/corrective_actions_postflight.sql` read-only. Expect all boolean
   checks true. Separately SELECT `automation_enabled` from the new settings table:
   expect false. Preserve before/after counts and Staff metadata fingerprint.

## Hosting decision

No production n8n host has been selected or provisioned. Local Docker and a tunnel
cannot meet laptop-off availability. A free Cloud trial is temporary, not a
permanent free hosting plan. Community Edition has no software subscription for
this internal workflow, but requires a separately available always-on host.

| Option | Fit | Gate |
| --- | --- | --- |
| Existing always-on host, Community Edition | Recommended if available; no new n8n subscription | Approve the exact host/HTTPS exposure; persistent state and backups |
| n8n Cloud | Least server maintenance, recurring charge after trial | Approve plan and budget; user accepts account terms privately |
| Local laptop Docker | Development only | Keep production automation off |

The current 15-minute scheduler costs 2,880 runs per 30-day month or 2,976 per
31-day month BEFORE event webhook workflows. Advertised Starter allowance is
2,500/month, so that combination does not fit. Use an approved larger allowance,
or separately design/test Supabase-triggered dispatch so idle polls do not consume
n8n executions. Hourly polling reduces runs but changes response latency; it has
NOT been silently substituted. Hosting is not resolved until a real endpoint,
storage, recovery and off-laptop availability have been verified.

For self-hosting: pin a supported patched n8n image after review; preserve an
encrypted persistent n8n data volume and database backup plus encryption key;
use HTTPS, restricted editor access, secure cookies and the correct proxy-hop
count. Current n8n docs use `N8N_WEBHOOK_URL` (older `WEBHOOK_URL` is deprecated).
Only workflow webhooks need reachability from Edge; no public database/admin key.
No additional AI Assistant/sandbox services are needed for these fixed workflows.
Do not purchase hosting, open a laptop tunnel or reuse the HF inference container.

Official references checked 24 October 2026:
- https://support.n8n.io/article/how-do-i-cancel-my-trial
- https://n8n.io/pricing/
- https://docs.n8n.io/hosting/community-edition-features/
- https://docs.n8n.io/hosting/configuration/configuration-examples/webhook-url/
- https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/keep-n8n-running/backup-and-restore.md

## Separate deployment and real integration gates

After approved SQL and hosting decisions, request approval for an initially
disabled `corrective-actions` Edge deployment and purpose secrets:

- `SUPABASE_URL`, platform `SUPABASE_SERVICE_ROLE_KEY` (server only).
- Separate >=32-character `DEFECTRAG_CA_WORKER_SECRET`,
  `DEFECTRAG_CA_CALLBACK_SECRET`, `DEFECTRAG_CA_N8N_SECRET`.
- `DEFECTRAG_CA_N8N_URL`: fixed approved HTTPS production webhook, no credentials
  in URL. `DEFECTRAG_CA_AUTOMATION_ENABLED=0` initially.
- Keep database automation false; keep UI flag false; no live emails yet.

Import INACTIVE `deployment/n8n/corrective-actions.json` and
`deployment/n8n/corrective-actions-scheduler.json`. Replace project placeholders
with this project's `corrective-actions` endpoint, not `hyper-worker`.
Inbound Header Auth: `X-DefectRAG-CA-Key` with n8n secret; callbacks: Authorization
Bearer callback secret plus `X-DefectRAG-Operation: effect`; scheduler: Bearer
worker secret. Store credentials privately in n8n. Never supply a service-role
key to n8n. Configure separately approved SMTP; current Resend test sender only
permits its owner recipient and is not arbitrary-supervisor delivery. Supabase
Auth SMTP is separate and must remain unchanged. Never activate the old Staff
notification workflow or send a duplicate Developer notification through n8n.

Real verification, each recorded as passed/failed/blocked rather than assumed:

1. Approved test fixtures only: a disposable explicitly shared QA inspection and
   human review; no production inspection reused or private image auto-shared.
2. Real Developer and approved Staff MFA: positive bounded RPCs, case lifecycle,
   assignment validation, stale-write rejection and immutable audit trail.
3. Real pending/AAL1/anonymous denial; test revocation only on a separately
   authorized disposable account, never revoke an existing working account.
4. Raw prediction/missing confirmation/latest Accept review rejected. Direct
   writes and lease/receipt reads denied. Personal cross-owner isolation retained;
   Team case reads remain collaborative; writes require CURRENT owner/supervisor/
   Developer. Verify direct RPC self-assignment bypass is denied and reassignment
   removes former-assignee editing.
5. Wrong webhook/callback secret, expired/wrong-event lease and arbitrary effect
   rejected. Validate through real Edge and Supabase, using a mail sink first.
6. Separately authorize one controlled supervisor email; verify one message,
   durable event/effect receipts, harmless replay, ambiguity quarantine, overdue
   reminders and retry behavior. No ticket/Trello activation.
7. Prove host persistence and recovery after restart, then laptop-off delivery.
   Only then request final automation/UI activation and monitor bounded QA.

## Pause / recovery

On a separately approved pause: stop ONLY the new CA scheduler/workflow, set CA
Edge gate0, CA database automation false and public corrective flag false.
Leave automatic Developer email Cron/worker untouched. Retain all cases, review
snapshots, history, events and effect ledger. Never clear completed/ambiguous
effects or directly replay the SMTP node. Restore an application version if
needed; do not drop tables or undo existing Auth/Personal/Gallery migrations.
