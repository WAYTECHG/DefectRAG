# Disabled email configuration saved by user; deployment approval pending — 20 October 2026

User reports Disabled configuration saved. Seven Edge secret entries recorded
as USER-CONFIRMED; agent did not read/enter values or independently verify them.
Delivery remains intended0, transportresend, sandbox1; QA event ID deferred.
No worker deployment, invocation, provider send or cron approval yet.

Prepared one paste-ready Dashboard function package to avoid installing CLI or
copying three files separately. New deployment/supabase/build_email_function.mjs
uses existing esbuild, bundles exactly reviewed index/worker/direct-email and
hashes inputs/config. No dependencies installed or implementation behavior
changed. Four real bundled-code offline checks passed: no local imports,
disabled POST503, enabled unauthorized POST401, GET405, all without network.
Output runtime/email-function-release/index.ts + manifest; bundle SHA256
a70e89e05d66918ed00a78bfdc769c2afd761fb10e376be0e12903147cd82017.

NEXT: request separate approval for ONLY staff-notifications deployment with
delivery0 and function-level verify_jwt=false/dedicated handler bearer intact.
Use one-file Dashboard route (no connected Supabase management API/installed CLI).
After approved deployment, public POST without secret should return503 disabled;
if401 gateway or other result, investigate without enabling delivery. Native Auth
SMTP/MFA/roles/React/HF/Gallery/models/RAG untouched. No tests repeated except
the four new packaging checks; no SQL or GitHub changes. Sending, cloud scheduling
and Priority2 remain pending. See docs/DEVELOPER_EMAIL_ACTIVATION.md latest.

---

# Disabled email configuration approved; manual secret entry pending — 20 October 2026

User approved disabled configuration. Authorized scope: dedicated Resend Sending
key + required Supabase Edge secrets with DEFECTRAG_NOTIFICATIONS_ENABLED=0.
User must enter secret values privately; agent has not read/generated/entered
them. Seven entries in one batch; QA event ID intentionally deferred while off.
Do not overwrite platform SUPABASE_* keys or Auth Gmail SMTP configuration.
Existing implementation/source tests unchanged; no repeated model/test jobs.

WAIT FOR: user reports disabled configuration saved. Then request separate
approval to deploy ONLY staff-notifications with delivery0 and verify disabled
behavior. No function deployment, provider API call, invocation, scheduler,
staff decision, sending, HF/GitHub or SQL change performed/authorized at this step.

---

# Notification migration manually applied by user; email activation pending — 20 October 2026

User reports execution of reviewed deployment/supabase_direct_notifications.sql:
Success. No rows returned. Expected for transactional DDL ending COMMIT; record
as USER-REPORTED APPLIED. DO NOT rerun the migration or original Auth SQL.
Existing worker privilege screenshot independently shows anon/authenticated false
and service_role true for original claim/finish functions. User confirmed earlier
flags true, absent new objects before execution and private outbox checks. Resend
verified account email matches Developer recipient by user confirmation.

No new direct RPC/schema definition/grant or service configuration independently
verified live yet. No agent SQL execution, secret change, Edge/HF deployment,
email, approval/revocation, native MFA/SMTP change or GitHub push. No source-code
changes since3f94d18; tests retained, not unnecessarily repeated.

NEXT APPROVAL: disabled server configuration only, keeping notifications0;
then separate approval for staff-notifications deployment. User enters provider
key/dedicated worker bearer privately in Supabase Edge Secrets, never chat/HF/
React/n8n. QA event selection remains pending and may be omitted while disabled.
After disabled deployment, batch live permission/configuration checks. Actual
mailbox, retry/dedup and laptop-off acceptance remain NOT VERIFIED. Priority2
remains deferred. See docs/DEVELOPER_EMAIL_ACTIVATION.md latest checkpoint.

---

# Developer email activation preflight; production still OFF — 20 October 2026

Continues68b7a1e on feature/auth-mfa-inactive. Read AUTOMATION_MILESTONES,
direct-email/worker/entrypoint, current outbox/request/finish RPCs and proposed
migration. User confirmed: Resend account ready, verified email matches existing
Developer recipient. No address or secret received; no provider key created/read.

Current official Resend docs confirm test sender restriction to account owner,
24h provider idempotency and Free100/day/3000-month limits. Prepared secure manual
key/configuration guide docs/DEVELOPER_EMAIL_ACTIVATION.md with SEPARATE approval
gates for migration, secrets with delivery0, disabled function deployment, QA
activation and Vault/cloud scheduling. Supabase Edge secrets are independent of
HF variables. Gmail Auth SMTP, mandatory MFA and manual approvals preserved.

Audit found QA-filtered claims still did global housekeeping. Scoped BOTH updates
in UNAPPLIED deployment/supabase_direct_notifications.sql to selected p_event;
no unrelated notification status maintenance during QA. Updated migration LF
SHA256:53952cc212e67ca03773a791d18b55f5a74233de96b843c087a26bb610180ce5. This exact updated version requires review; NOT executed.
Prepared LOCAL rollback-only integration test deployment/tests/direct_notifications_local.sql
for role denial, selected-event isolation, rate clock, immutable snapshot, lease
checks and23h ambiguity. Local SQL environment unavailable; test NOT executed.
New deployment/email_activation_preflight.sql is SELECT-ONLY metadata/counts.

Fresh public GETs: dashboard200 (index-C51GOc1V.js), health200/statusok, all12
models configured, auth workflow/Personal/Gallery enabled; Gallery GET200.
No native login, model job, private record or cloud email test performed. Does
NOT verify live DB MFA flags, notification deployment/secrets or exact HF commit.
119 frontend regressions, cloud build/verify/stage and OFFLINE publisher guard
PASS after scoped SQL change. Existing CSS/app bundles unchanged. Prior55 backend
regressions retained, not repeated; no backend source changed. No source model,
RAG, React, Auth SMTP, staff permission, Gallery or existing record changes.

NEXT REQUIRED USER ACTION: run SELECT-only email_activation_preflight.sql in
existing Supabase SQL Editor and return metadata/counts, no secrets/PII/payloads.
Require registration_enabled=true/mfa_required=true and expected service-only
worker grants. Check absent/new schema objects before migration approval; stop
if partial/already-applied or incompatible. Obtain private recoverable backup.
Do not execute migration or set secrets until separate exact approval. Existing
pending QA request is idempotent: resubmitting does NOT create a new mail event.
Choose one explicitly authorized queued event later, never reset sent rows.

Actual mailbox, retries/dedup and laptop/Docker-off evidence remain pending.
Priority2 CA verification/hosting/Trello remains deferred until Priority1 passes.
No production SQL, deployment, secrets, permission changes, email or GitHub push.
See results/developer-email-activation-preflight-20261020.json and
results/email-activation-public-preflight-20261020.json for exact scope.

---

# Two automation milestones prepared and locally tested; NOT activated â€” 20 October 2026

Continues d7f10c2 on feature/auth-mfa-inactive. Milestone1 code checkpoint712a832
saved before independent Milestone2 development. Latest final checkpoint is the
Git HEAD containing this entry; no remote push or deployment. Source reference:
C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2.

M1: optional direct Resend cloud adapter, no n8n/laptop dependency. Reuses unique
outbox/leases/retries/status; server-only credentials, fixed #team link, masked
applicant email, database timestamp. Additive REVIEW-ONLY direct-notifications
SQL persists immutable provider payload, rate-limits claims, rechecks membership/
recipient and quarantines ambiguity after23h. Sandbox requires exact recipient
AND one approved QA outbox event ID, so unrelated requests stay untouched.
Provider24h idempotency supported; accepted is NOT verified inbox delivery.
No-domain test sender only reaches Resend account owner; applicant templates
require verified-domain operation. Provider selection/configuration still pending.

M2: inactive Corrective Actions card inside Team Workspace, existing CSS/classes.
Only active Team inspection + latest completed human Reject review + separate
explicit confirmation can create a case. New REVIEW-ONLY SQL requires current
Staff + native TOTP AAL2 on reads/RPC writes, even if frontend flag manipulated.
Cases preserve review/confirming actors, private evidence reference, owner,
supervisor, priority, due date, versioned state/audit snapshots. Progress,
resolution, reopen, close/cancel; deduplicated reminder/escalation events.
Metrics use actual timestamps from up to500 accessible cases; no fabricated data.
No automatic Personal sharing or case creation from model verdicts.

Server-only bridge + inactive n8n templates use purpose secrets, short event
capabilities and durable effect ledger; no privileged DB key in n8n/React.
Completed duplicate effects skip SMTP. Ambiguous SMTP effect becomes manual
review/dead rather than auto-replaying. Optional Trello connector NOT implemented;
ticket effects are rejected. Production automation/frontend gates remain OFF.

VERIFIED:119 frontend tests (includes29 notification and15 CA cases),55 offline
backend auth/MFA/Personal/security regressions. Real JSX renders and compiles.
After user started Docker, actual n8n2.43.7 ran in disposable --network none
container with loopback SMTP sink + simulated Supabase callbacks. Eight scenarios
passed: send, duplicate, unconfirmed denial, raw prediction rejection, SMTP
failure, ambiguity quarantine, lost completion receipt, retry without duplicate.
Zero external emails/DB calls. Existing n8n/ollama containers and volumes untouched;
disposable container auto-removed. Existing user-started containers left running.

Local/static/cloud builds PASS in runtime/automation-20261020 (working dist and
showcase preserved). Cloud verification/stage and OFFLINE publisher guard PASS,
86 files; source fingerprinta3cb620e8a1f58baa4b07112490eb205dd5546ccc227a57a0b5b5af6c0879dd8.
Cloud main:index-BBEwERpA.js; Team chunk:TeamWorkspace-BSL2byAA.js.
CSS index-Bn4HF2vD.css hash087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661
UNCHANGED. Applied auth SQL LF hash cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983
UNCHANGED. Existing non-fatal Vite config/Gradio browser and mixed-import warnings
remain. Last recorded live HF remains8df12b1010e8b3184544628bd0b64988910c7e39.

NOT VERIFIED: local PostgreSQL/RLS execution (rollback-only test script prepared,
not executed; no PostgreSQL/Supabase image installed), live Edge/cron/provider,
real mailbox/laptop-off acceptance, native CA user lifecycle/revocation/recovery,
production webhook trigger authentication/connectivity, live due/overdue schedule.
n8n local fixture substitutes manual trigger + response; backend callback authority
is simulated, not proof of deployed SQL security. No multimodal RAG/model runs.

FILES/DETAILS:docs/AUTOMATION_MILESTONES.md; results/automation-milestones-20261020.json;
results/automation-n8n-local-20261020.json. New reviewable migrations:
deployment/supabase_direct_notifications.sql and deployment/supabase_corrective_actions.sql.
Read-only metadata preflight:deployment/automation_preflight.sql. Local rollback
test:deployment/tests/corrective_actions_local.sql. n8n templates and isolated
fixture runner:deployment/n8n/corrective-actions*.json,test-local.mjs.

M2 code checkpoint2c79b10 synchronized24 source/doc/result files to Desktop,
preserving both intentional local edits and untracked data. Final release check
then detected SQL CRLF-only fingerprint drift; .sql normalization and a focused
regression were added. The rebuilt cloud assets are unchanged;119 tests and
offline publisher guard passed again. Final guarded sync carries this fix too.

RESUME: inspect Git HEAD and guarded Desktop sync receipt; do not rerun successful
model experiments, native MFA enrollment or original auth migration. First review
new SQL and execute isolated LOCAL PostgreSQL tests; then request separate
production SQL/configuration/deployment approval. Configure restricted Developer
QA provider/event, deploy Edge + Vault/Cron only after authorization, then verify
one real mailbox message with laptop/Docker off. Real CA integration requires
approved schema and authorized Staff-AAL2/privacy/recovery tests. Keep CA
automation0/DBfalse/public correctiveActionsEnabled absent until those pass.
Local n8n stops when laptop sleeps; production needs separately approved
always-on HTTPS hosting. No paid service, tunnel, secrets, permissions, existing
records, emails/invitations, model assets or GitHub changes authorized/performed.

---

# Milestone 1 direct email adapter â€” local tests only; NOT activated â€” 20 October 2026

Continues d7f10c2 on feature/auth-mfa-inactive. Audited existing request/decision
RPCs, outbox/lease/retry, Edge worker and inactive n8n SMTP template. Auth Gmail
SMTP preserved; private credentials/configuration never read. Existing live
mandatory MFA/registration and permissions unchanged. No account decision/mail.

Opt-in direct Resend adapter reuses outbox, avoids n8n/laptop, masks applicant
email and includes database request time, Pending status and fixed #team link.
New REVIEW-ONLY deployment/supabase_direct_notifications.sql adds globally
rate-limited claim and persistent provider-body snapshot. Stable idempotency key;
23h ambiguity quarantine prevents replay beyond provider's24h dedup window.
Legacy consumer retained inactive. Original applied auth SQL unchanged.

28 notification tests passed (7 direct,21 existing). No new dependencies.
Live mailbox/SQL/cron/laptop-off acceptance NOT performed; needs separate approval,
provider and server configuration. No-domain Resend test sender can notify only
the account-owner Developer address. Applicant templates implemented but require
verified domain for real recipients; sandbox blocks them. See
docs/AUTOMATION_MILESTONES.md for provider restrictions and exact activation gates.
Docker CLI present but Linux engine stopped; no Docker changes made.

NEXT: save this code checkpoint, then independent inactive Corrective Actions
development/local tests. Keep notifications disabled. Do not deploy, migrate,
configure secrets, send email or push GitHub. Current cloud UI manifest is stale
because notification test inputs changed; rebuild/verify before any later release.

---

# Team inspection UX implemented and tested locally; NOT deployed â€” 20 October 2026

Continuing7e6d92e on feature/auth-mfa-inactive. Team Run Inspection restriction is
INTENTIONAL in both React and cloud backend. Kept Personal -> private save ->
explicit Team sharing -> review. No automatic sharing or authorization changes.

New existing-style InspectionAction shows the exact requested Team explanation,
an accessible disabled-button reason, and Switch to Personal Workspace. The safe
Team-to-Personal handler changes client scope without reload and preserves exact
File objects, category and batch label; it clears results/conversations/reviews/
workspace lists and invalidates old requests. Auth changes/signout still clear
files. Reverse Personal-to-Team draft images are cleared; no upload/write/share
occurs during switching. Busy/evidence/record loading prevents the shortcut.

Readiness explains missing/invalid/oversized inputs, batch limits, processing,
connection/service/provider failure, permission checking, pending/rejected/revoked
access and native MFA. Existing native own-status RPC supplies signed-in posture;
failure/denial never becomes guest fallback. Identity changes/unmount/offline
invalidate late checks; refresh uses auth/focus/reconnect and15s polling. UI is
advisory; existing backend/RLS/MFA/scope checks remain unchanged. Guest Demo and
offline local inference retained. Byte/dimension validation stays authoritative
on the backend; GPU quota cannot be predicted before a request.

MODIFIED:frontend/src/main.jsx. NEW:frontend/src/InspectionAction.jsx,
frontend/src/inspectionReadiness.mjs,frontend/tests/inspectionReadiness.test.mjs,
docs/TEAM_INSPECTION_UX.md and results/team-inspection-ui-20261020.json.
No CSS/theme/auth/MFA/approval/SQL/n8n/model/RAG/gallery source modified.

TESTS PASSED:96 frontend (34 new focused cases),55 offline backend auth/MFA,
Personal Workspace and cloud security regressions. Real JSX render and actual
handler tests cover draft File identity/category/batch, safe scope changes,
no upload/share, private context invalidation, submit guards, native posture,
late auth responses/outages, disabled explanations and batch recovery boundaries.
Local, showcase and cloud production builds passed in runtime/team-inspection-ui.
Cloud verify/stage and OFFLINE publisher guard passed (86 selected files).
Fingerprint:7dbc25a489ae55e47e8ee804d42142eb7bcd3c19892a15bee0259df7c71006a1.
Cloud main:index-BLZHWupW.js. CSS index-Bn4HF2vD.css EXACT original hash unchanged.
Original frontend/dist and dist-static builds preserved; no new dependencies.
No live browser/native/model acceptance claim for this undeployed UI.

Local release input development-support/space/ui-dist now holds the tested pending
cloud build with existing public configuration preserved. published-hashes/remote
release receipts still describe the last live release; no HF API/publisher commit,
SQL, staff permission/secret change, email, n8n dispatch, training or GitHub push.
Last verified live HF remains8df12b1010e8b3184544628bd0b64988910c7e39; user must
approve any deployment. Keep mandatory MFA and notifications0; applicant pending.

CODE CHECKPOINT:b859d67; seven changed source/test/document/result files synchronized
to Desktop by guarded fast-forward. Desktop cloud artifact source/hash check passed;
its local config, run guide and local/static indexes retain exact protected hashes.
Final checkpoint also restores original unchanged-line formatting in main.jsx so
the final review against7e6d92e contains only23 added/5 removed UI lines there.
Verified normalized source fingerprint and runtime behavior remain unchanged.

NEXT: on explicit HF approval only, publish the verified bundle and perform the small manual draft
preservation + private inspection + separately authorized share checks described
in docs/TEAM_INSPECTION_UX.md. Do not repeat SMTP, signup/MFA enrollment, SQL or
benchmarks. Older generic authorization-sync messaging and guest SQLite lock
findings remain recorded; this change adds clear Run-button reasons only.

---

# Registration confirmed; pending-account protection verified â€” 20 October 2026

Continuing a7ddcff. Live HF remains8df12b1010e8b3184544628bd0b64988910c7e39,
RUNNING; workflow1, notifications0,12 categories and public health200 confirmed.
No new application deployment, source/UI modification, SQL, production permission,
secret change, email/invitation, account decision or model experiment in this stage.
Mandatory MFA remains enabled as previously configured by the user. The agent did
not change either database switch. No test account was approved/rejected/revoked.

USER-COMPLETED LIVE TEST: separate controlled test identity registered; Supabase
confirmation mail received and verified; confirmation returned to production
https://wizzas-defectrag.hf.space/; signed in and submitted Request Staff Access;
status Pending. Email delivery and redirect are user-observed, not inbox inspection
by the agent. User explicitly instructed that account remain pending.

INDEPENDENT BROWSER PASSES: user signed the pending account into this conversation's
browser; Access:pending, session not verified. No Team data, Developer recovery or
access-management controls. Personal and Team history disclosed no protected
records. Returning to Staff workspace reloaded Pending (request persistence).
Submitted ONE public Capsules sample through the real inspection UI: queued server
rejected with "Approved staff and required authenticator verification are needed.
Open Staff workspace." No result/report produced. Membership guard precedes GPU
compute in unchanged source; no successful inference experiment was repeated.
Then signed out only that test browser session for the Developer assurance test.

LIMITS: UI/backend denial is real, but direct pending/AAL1 JWT REST/RPC/Storage
policy probes were not performed. No credential/JWT/QR/code was requested or stored.
Password recovery success remains the user's earlier report; no fresh reset email
was sent. Pending denial also shows generic synchronization failed and CHECKING
MEMBERSHIP messaging; focused status-copy improvement recommended, not implemented.
Earlier temporary guest SQLite initialization-lock finding remains unmodified.

DEVELOPER AAL1 PASSED: user signed in with existing Developer password only. Browser
showed approved membership, session not verified, mandatory-authenticator message,
no protected Team records or Developer management/recovery. Second single public
Capsules sample was rejected by queued server before a result/report was produced.
Native authenticator challenge was available. No successful GPU inference was run.

DEVELOPER AAL2 PASSED: user completed native authenticator verification privately.
Browser showed verified session, Developer management and recovery. Native access
directory contained QA Registration as pending/applicant with approve/reject actions;
actions were INSPECTED ONLY. Five existing Team records, authenticated original/
heatmap Storage Blobs, protected backend image paths and two Personal owner records
were accessible. This demonstrates mandatory-MFA AAL1 denial -> AAL2 access without
any membership change. Delivery-status RPC showed requested event queued,0 attempts.
No notification dispatch/retry, approval/rejection/revocation or new inspection result.

CURRENT HANDOFF: #team live tab remains signed in as verified Developer. Test
identity remains pending. Do NOT approve/reject/revoke, retry delivery or change
production permissions without separate explicit confirmation. No permission for
Staff post-approval access testing has been given. Next optional native tests need
that explicit decision, additional authorized identities and/or direct RLS/Storage
test setup. Wrong-code/native lost-factor/revocation tests and fresh recovery mail
remain unperformed. Do not repeat signup, MFA enrollment, mail or model experiments.

Updated docs/REGISTRATION_ACTIVATION_20261020.md and
results/registration-activation-20261020.json distinguish user-observed email/redirect
from agent-observed pending/denial. Preserve all identities, pending/outbox/audit rows,
Personal/Team history, Gallery and models; CAPTCHA remains deferred by user choice.
Save final documentation checkpoint and guarded Desktop fast-forward. No need to
rerun unchanged software tests, rebuild frontend, redeploy or push to GitHub.

---

# Registration interface active; controlled signup test pending â€” 20 October 2026

Latest live HF commit:8df12b1010e8b3184544628bd0b64988910c7e39, RUNNING.
Parent:b9b5fd90e38f421007912f56663db26e9208bd6d. Application source remains
689554cc32880be925d14cda15e4d4972ffdaff9 on feature/auth-mfa-inactive; final
documentation checkpoint follows. Exactly ONE remote file changed:
frontend/dist/config.js. Public authWorkflowEnabled=true and registrationEnabled=true.
Backend DEFECTRAG_AUTH_WORKFLOW=1, notifications0 and every unrelated HF variable
preserved. No backend/model/React/CSS/SQL/membership/secret changes.

PREREQUISITE PASSED: user ran the requested read-only SELECT on
public.defectrag_auth_settings and returned registration_enabled=true,
mfa_required=true BEFORE the frontend flag changed. The agent did not directly
authenticate to SQL, execute a migration or change either switch. User reports
Developer native MFA verified/enforced, Gmail SMTP/reset mail working and the
recovery redirect corrected to the production HF app. Those native results are
user-reported until independently observed in a controlled test.

FRESH PASSES:62 frontend/auth/security/build tests,87 verified release files,
offline publisher guard; remote before/after comparison of149 allowlisted paths
confirms all except config unchanged. Main JS index-C51GOc1V.js and original CSS
index-Bn4HF2vD.css match exact prior/live hashes. HF RUNNING; registration and
existing sign-in forms visible together; public health/models/evaluation/samples/
Gallery200;12 model categories;3 Gallery IDs preserved; unsigned private history401.
Supabase disable_signup=false, mailer_autoconfirm=false (email confirmation on).
No model inference or benchmark repeated. Fresh guest history/stats/alerts200.

OBSERVED LIMITATION: startup log contained sqlite3.OperationalError: database is
locked in unchanged temporary guest-history initialization. Later fresh guest
requests passed; no persistent startup error observed. Not claimed fixed or
concurrency-load-tested. Preserve this finding for later focused hardening.

ABUSE: user explicitly confirmed CAPTCHA not configured and chose native Supabase
rate limits for this rollout. Retain those server limits; no production exhaustion
test or admin limit/secret changes. CAPTCHA remains a documented hardening task
requiring approved provider configuration and client-token integration across
signup/login/recovery. Do not silently enable it and break current authentication.
n8n/Edge not deployed/invoked; no agent email/invitation/account approval sent.
Requests may queue outbox events without notification delivery.

DESKTOP: started at same689554c, local config/run guide edits preserved; current
cloud release/receipts staged into isolated development-support/space/ui-dist and
validated there. Hashes of working local/static indexes and local config/run guide
unchanged. No models/datasets/secrets/records copied. Use guarded fast-forward for
the documentation/results checkpoint; never overwrite the two Desktop local edits.

MANUAL TEST PENDING: user agreed to use a separate self-controlled test email and
enter password/email steps privately. Live #team page is open. User was asked to
register, confirm email (production .hf.space hostname), sign in and submit Request
staff access, then report outcome. Expected Access:pending and protected-data denial.
Do NOT approve/reject/revoke the test account without separate explicit permission.
Actual confirmation delivery/landing, request persistence, fresh Developer AAL2
directory read and fresh recovery email remain pending; no live pass assumed.
Existing source/tests enforce verified email, no automatic staff grant, pending
denial regardless of MFA, approved Staff AAL2, Developer-only AAL2 decisions and
idempotent requests. No new registration/developer account was created by agent.

Reports:docs/REGISTRATION_ACTIVATION_20261020.md and
results/registration-activation-20261020.json. Private ignored operator receipts:
development-support/space/registration-20261020 (not for GitHub).
NEXT: incorporate the pending manual test outcome, inspect authorized pending UI/
denial and Developer AAL2 read only. Preserve existing identities/history and keep
notifications off. For a registration UI rollback restore ONLY the compatible
parent config/application; KEEP DB MFAtrue and workflow1. Never use the pre-MFA
13af0e1 rollback from the older Step5 report after enforcement. No GitHub push,
SQL migration, Multimodal RAG upgrade or permission activation is authorized here.

---

# Step 5 deployed and verified; stop before Step 6 â€” 20 October 2026

HF Space RUNNING: https://huggingface.co/spaces/Wizzas/DefectRAG
Application: https://wizzas-defectrag.hf.space/
HF release: b9b5fd90e38f421007912f56663db26e9208bd6d
Deployed source:1dfb01e8f15e26839964b58f9a7e1d1307701891,
feature/auth-mfa-inactive. Final documentation/results checkpoint follows that
application source; inspect the latest commit named "Record controlled HF rollout
and live bootstrap verification". No further application deployment is implied.

USER CONFIRMED manually executed auth migration and passing postchecks; DB
registration_enabled=false and mfa_required=false. Exact migration LF SHA256
cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983.
No migration/SQL was executed by the agent. Public authWorkflowEnabled=true,
registrationEnabled=false; HF DEFECTRAG_AUTH_WORKFLOW=1 and
DEFECTRAG_NOTIFICATIONS_ENABLED=0. All unrelated HF variables and secrets preserved.
No enrollment, MFA enforcement, registration, notification service, membership
decision, real email, GitHub push, training or multimodal upgrade activated.

FRESH VERIFIED:62 frontend tests,87-file verified build and offline release guard;
149 committed files checked against remote Git/LFS hashes; HF image build/startup;
live asset hashes including index-C51GOc1V.js, TeamWorkspace-DVtFB4ub.js,
authSecurity-C13nsxqA.js; identical original index-Bn4HF2vD.css. Public health,
models/evaluation/samples/Gallery HTTP200;12 categories;3 Gallery entries preserved;
unsigned private history and anonymous auth-status RPC401. Old container served
old assets briefly during startup; final served hashes match the new release.

User signed in to existing Developer account: approved non-AAL2 access retained;
5 active Team records,2 Personal records, private originals/heatmaps, old Team
notes/review and Personal alerts accessible. Authenticated Blob image downloads
and fresh backend private image paths both work.3 existing Team archives visible
in Developer recovery; Personal recovery empty. No private record mutations.
Account Security and Set up authenticator visible. Real new guest Capsules DINOv2
CUDA inference801.65ms, score0.2054974884 vs threshold0.1439922601; actual heatmap,
image/report200; foreign guest isolated. Real cited Qwen3-4B answer2532.49ms,
matching source quotes,2 saved conversation turns. Only temporary guest history
created; no new durable inspections or public publications. No experiment repeated.

Desktop and Work source started at the same1dfb01e. Latest verified cloud release
staged to Desktop's isolated development-support/space/ui-dist and checked there.
Original Desktop public/local config, run guide and local/static build indexes
retain exact hashes. Old release config backed up privately. No datasets, models,
secrets or inspection records copied. Guarded Git fast-forward is used for the
final documentation/results checkpoint; preserve both intentional Desktop edits.

Reports: docs/CONTROLLED_DEPLOYMENT_20261020.md and
results/controlled-deployment-20261020.json. Detailed private baseline/rollback,
logs, guest result and release receipts:development-support/space/step5-20261020;
never upload this ignored folder to GitHub. Rollback target13af0e1cb002386ade5849739f4bd28c5736f341
saved; no rollback needed. No local jobs remain; HF app continues running.

NEXT: STOP before Step6. Manual Developer TOTP enrollment/second-session test is
documented in the deployment report; never enable mandatory MFA to troubleshoot.
Separate ordinary Staff, non-staff/pending/cross-owner accounts, native successful/
failed MFA/recovery, AAL2 approvals/revocation, fresh multi-image batch and real
Edge/n8n/SMTP integrations remain unverified live. Earlier automated tests are not
native integration passes. HF notification flag0 is verified, but external Edge
settings were not changed/inspected; no worker/workflow deployed or invoked.
ZeroGPU cold starts/quotas still apply. Current RAG is vision-assisted text RAG.
Any enforcement, registration, permissions, notifications or database-switch
activation requires a new user decision. Do not rerun SQL or benchmarks on resume.

---

# Desktop synchronized and verified; inactive release ready for approvals â€” 20 October 2026

Completed the requested corrections and guarded Desktop synchronization from
91da4df. Final CODE checkpoint2c92849, branch feature/auth-mfa-inactive; subsequent
checkpoint changes only record this evidence. Source and Desktop feature branches
are synchronized. Desktop main remains d0ff630, with history intact.

VERIFIED: notification deadline/partial/retry/duplicate tests, stale-build/config/
tamper/Gradio-lock guards, offline publisher/preflight checks and temporary Git
preservation/conflict tests.62 frontend tests passed in BOTH source and Desktop.
Five offline publisher/preflight +two synchronization tests passed. Source and
Desktop cloud builds, verification/staging of87 manifest files and offline
publisher checks passed. Desktop LOCAL build passed in runtime/auth-build/local.
Source/Desktop frontend fingerprint:
d5686550fdef9e3ad4015741429eb1da012b4624c432e84c5376dfd514f4fb73.
CSS remains index-Bn4HF2vD.css (same hash as working Desktop frontend/dist).

Desktop contains latest frontend/backend, inactive security SQL, n8n/Edge worker,
preflight, tests/results and activation/progress documentation. Original public
config and RUN_AND_DEPLOY guide passed EXACT first-sync pre/post hash checks.
They intentionally remain local Git modifications. Dataset and supabase.txt remain
untracked/untouched. No secrets/models/datasets/inspection records were copied,
read or deleted by sync. Working frontend/dist and dist-static were not replaced.
The only necessary dependency setup was2 already pinned Gradio client packages
installed OFFLINE with scripts disabled; package manifests/versions unchanged.

Reports: results/release-blocker-source.json and results/desktop-sync-verification.json;
timestamped Desktop preservation receipts under development-support/space.
No new processes/jobs remain. No SQL/preflight execution, migration, permissions/
secret modification, MFA/registration/notification activation, real email,
HF deployment, GitHub push, training or inference experiment.

NEXT REQUIRES SEPARATE APPROVAL: review actual read-only Supabase preflight results,
then manually execute exact reviewed auth migration; approve inactive HF rollout;
prove real Developer TOTP/recovery and staff/non-staff authorization; configure
native Auth SMTP/redirects and n8n hosting/Header Auth/SMTP/Edge secrets; test a
mail sink and separately activate worker/Cron/registration/MFA. Native/live
integration remains unverified. SMTP ambiguity after send-before-ack is retained
as a limitation; there is no exactly-once promise. Current RAG remains vision-assisted
text RAG, not a new Multimodal RAG implementation. Preserve all existing features.

---

# Worker/runtime and frontend release blockers corrected â€” 20 October 2026

Desktop fast-forward to a3e399e completed on feature/auth-mfa-inactive;40 tracked
code/security/doc/result files synchronized. Its main stays d0ff630. Original public
config/run guide hashes and untracked dataset/supabase.txt remain preserved. Desktop
local build passed. Missing cloud-only client dependencies were installed using
the EXISTING pinned lock via offline npm ci --ignore-scripts (only2 packages).
Cloud setup now uses Desktop's preserved frontend/public/config.js because no old
Desktop cloud-release directory existed. No installed configuration was replaced.
Follow-up source guard now also fingerprints the separate Gradio client lockfile;
source cloud build/verification/staging passed62 tests and87 allowlisted files.
Next: sync that guard refinement, finish Desktop cloud verification and receipt.

Continuing 91da4df on feature/auth-mfa-inactive. Worker now claims one event at a
time, max2/invocation, reserves52s before claiming, and enforces100s overall with
fetch/body timeouts. Unstarted work remains queued; completion failures rely on
existing durable leases. Stable event IDs and duplicate guards preserved. SMTP
crash-after-send ambiguity remains documented; no false exactly-once claim.

Frontend build receipts bind current source/tests, generated assets and public
configuration. verify -> stage -> publisher check now reject untested/stale or
modified artifacts and publish only the current manifest, excluding old disk
chunks. Publisher --check-frontend is OFFLINE ONLY and contacts no HF service.
Source cloud build/verification/staging passed:61 frontend tests,87 release files,
unchanged CSS index-Bn4HF2vD.css. Working local/static builds remain preserved.
26 focused worker/build-guard checks and5 offline publisher/preflight tests passed;
two temporary-Git synchronization tests exercise preserved config and conflict
refusal (unrestricted run needed for sandbox-blocked local Git clone).

Read-only preflight finalized with expanded function ACLs and native Auth helpers.
It was NOT executed. Reviewed auth migration hash unchanged:
cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983 (LF SHA256).
No migration, database permission/secret change, activation, real mail, model work,
HF deployment or GitHub push. Existing native/live integration gates still apply.

DESKTOP PRE-CHECK: main at d0ff630; only tracked local edits are public config and
RUN_AND_DEPLOY guide. They do not overlap synchronized changes and will be retained
byte-for-byte. Dataset/supabase.txt and ignored models/runtime remain untouched.
NEXT within this milestone: commit source, run guarded branch fast-forward to
Desktop, verify Desktop cloud/local builds and record final preservation receipt.
See docs/RELEASE_BLOCKER_FIXES_20261020.md for exact offline build/stage commands,
preservation behavior and remaining activation/configuration approvals.

---

# Final pre-activation assessment â€” 20 October 2026

Audited unchanged application checkpoint fa5e499 on feature/auth-mfa-inactive.
No migrations, live SQL/catalog queries, deployment, native MFA activation,
permissions/secrets changes, emails or model work. No completed test suites rerun.
Only assessment/runbook/progress documentation and a READ-ONLY preflight SQL file
were added/updated. Earlier 123 distinct Python /49 frontend passes are historical
local evidence, not new native Supabase/n8n integration passes.

See docs/DEPLOYMENT_READINESS_20261020.md for schema compatibility, authorization,
exact n8n/Edge configuration, implementation matrix and deployment/test/rollback
checklists. Source schema is compatible, conditional on live catalog drift review;
deployment/supabase_auth_preflight.sql was prepared but NOT executed. Existing
developer MFA/recovery must pass a fresh second-session login before enforcement.

NEW RELEASE GATE: worker.mjs claims5 jobs with sequential20s webhook/15s completion
timeouts, plus15s claim: nominal190s envelope exceeds hosted Free Edge150s limit.
Before notification activation, approve a smaller batch and whole-invocation
budget plus focused slow-response/lease tests. No worker code changed in this audit.
Notifications can stay disabled independently of staged staff integration.
Also ensure the actual publisher input development-support/space/ui-dist contains
the approved new cloud build/config; verification output runtime/auth-build/cloud
does not update that release directory. Do not run publish.py as a readiness check.

PUBLIC DEMO: existing isolated anonymous browser workspace and static showcase
implemented; no separate recruiter-tour/toggle UI found. MULTIMODAL RAG: not
implemented in this checkpoint. Existing BGE text retrieval/LangGraph plus textual
inspection context and text-only Qwen is vision-assisted text RAG. Preserve it;
genuine joint image/text retrieval/reasoning remains a separate milestone.

NEXT: review assessment and gates before requesting any separately authorized
change. Do not enable MFA/registration/notifications or execute any SQL implicitly.

---

# Inactive authentication / automation milestone â€” 20 October 2026

User approved implementation, reviewable additive SQL and local automated tests
ONLY. Work is isolated on branch feature/auth-mfa-inactive from baseline d0ff630.
Implementation checkpoint: bae2b41. Resume on this branch; inspect Git status
before any future edits. Do not sync/deploy/activate this milestone implicitly.
No migration executed, no permission/account changes, no production settings or
secrets modified, no emails/invitations, no deployment, no feature activation.
Desktop installation and existing working build outputs were not replaced.

IMPLEMENTED INACTIVE: AccountSecurity.jsx and authSecurity.mjs integrate native
Supabase signup/email confirmation, own access requests/status, native TOTP setup
and verification, unfinished-enrollment cancellation, developer approve/reject/
revoke and notification status/manual retry. Existing styles/navigation remain.
Registration never inserts staff membership; privileged decisions require AAL2.

New REVIEW-ONLY deployment/supabase_auth_mfa.sql preserves prior SQL and records.
It adds off-by-default registration/MFA switches, request/audit/outbox tables,
versioned transactional decisions, soft revocation, last-developer/self-decision
guards and restrictive private table/Storage policies. Existing privileged RPCs
inherit active-membership/MFA helper checks. Own posture remains available at
AAL1 for enrollment; pending/revoked users gain no protected data access.
The activation function is SQL-owner-only and refuses mandatory MFA without an
active developer's verified TOTP factor. No activation call was executed.

Enabled backend path performs fresh Supabase-validated posture checks, bypassing
the old 45-second membership cache. Protected images use user-JWT reads instead
of new signed links. Staff-page image blobs are released on replacement/unmount.
Gallery publication was adapted to the authenticated byte path, with explicit
owner and size checks, preserving opt-in public snapshots. Earlier app-issued
signed URLs remain valid up to10/15 minutes; downloaded data cannot be recalled.

Notification implementation: dependency-free inactive Supabase Edge worker,
purpose-secret invocation auth, separate n8n Header Auth, minimal event payloads,
leased claims, bounded retry/backoff and dead letters. Inactive n8n SMTP workflow
verifies provider acceptance before acknowledging. No OTP/approval authority or
Supabase privileged credential in n8n/React. No scheduler/resource provisioned.
Local n8n cannot send while the laptop is offline; Supabase retains events,
with manual UI retry after exhaustion. Always-on delivery needs an approved
reachable always-on n8n host. SMTP delivery is at least once, not exactly once.

LOCAL EVIDENCE: 55 backend auth/privacy tests,56 application regressions and22
Gallery checks (19 repeat existing Gallery cases +3 new authenticated-path cases)
passed. All49 frontend/UI/helper/worker tests and9 assistant-behavior regressions
passed:123 distinct Python cases total (repeated Gallery cases counted once).
Summary: results/auth-mfa-milestone.json; compact JUnit reports are alongside it.
SQL tests are
structural checks, not SQL execution or proof of live RLS. Local/static/cloud
frontend builds passed in runtime/auth-build, preserving deployed/local outputs.
CSS stays index-Bn4HF2vD.css, SHA256
087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661.
Original model/RAG implementation, old SQL, public config and styles are unchanged.
No training, inference, model download or performance experiments were repeated.

TEST ENVIRONMENT: initial source .venv lacked langchain_community; reused the
existing complete development-support/zerogpu-phase1/.venv, installing nothing.
Sandbox Windows socketpair blocked the in-process HTTP test client; diagnostic
stack confirmed that cause, and approved unrestricted fixture-only API tests
passed. A test's oversized auto-generated parameter ID was corrected before the
successful final run. Initial diagnostic artifacts remain under ignored runtime/;
only compact passing reports are release evidence. The two stalled child/launcher
processes matching this milestone's unique test marker were stopped after the
successful replacement run. No new test server/training/inference job remains.

REVIEW/NEXT: docs/AUTH_MFA_ACTIVATION.md contains full permissions/configuration,
SMTP requirements, offline delivery, activation and recovery procedure. Review
new migration before MANUAL execution. No previous migrations should be rerun.
Await separate permission for SQL, inactive-compatible deployment, real MFA/account
tests, emails, secrets, notification scheduling and mandatory enforcement. Bootstrap
the existing developer before enabling MFA, then test real regular-staff/non-staff
accounts and direct REST/RLS/Storage/Gradio/export boundaries. Deno Edge/n8n runtime,
native Supabase MFA and live policy execution remain UNVERIFIED, not live passes.

---

# MFA / n8n architecture assessment â€” 20 October 2026

User selected baseline d0ff630. Read-only application audit confirms invited-account
Supabase login and authoritative staff allowlist, but no registration, access-request,
developer approval/rejection, native MFA or n8n implementation in this checkpoint.
Do not assume another branch supplies those features.

Assessment saved in docs/AUTH_MFA_N8N_ASSESSMENT.md. Recommended: native Supabase
TOTP; developer-only transactional approval RPCs; active membership + AAL2 enforced
in backend, applicable RLS/Storage and security-definer RPCs; transactional outbox
and scheduled trusted worker calling authenticated n8n for notifications only.
Public Demo/Gallery remain accessible. Existing developer must enroll before any
mandatory enforcement. Review cached staff checks and 600-second private signed
URLs when implementing revocation; frontend-only MFA is insufficient.

No application/SQL/settings changes, installs, model runs, deployment, database
writes or emails. Only this progress entry and the assessment document changed.
Existing live evidence below remains historical; NO new MFA/approval/n8n tests
have run. n8n hosting and actual project SMTP/MFA settings are unconfirmed.

NEXT: present architecture for approval; confirm n8n hosting/SMTP. Only then prepare
inactive code, separate reviewable additive SQL and mocked security/delivery tests.
Do not execute migrations, activate auth, deploy or send real mail without explicit
approval. Real staff/non-staff test accounts remain needed for complete live tests.
Preserve all existing models, UI, RAG, records, gallery, SQL and Git checkpoints.

---

# Personal workspace LIVE; acceptance checkpoint â€” 19 October 2026

Final public Space RUNNING at13af0e1cb002386ade5849739f4bd28c5736f341 on free
zero-a10g; source code checkpoint e28f8c6. DEFECTRAG_PERSONAL_WORKSPACE=1 is
confirmed by live health. User executed reviewed SQL manually. Agent executed
no SQL, changed no policies, staff membership, secret or hardware.

VERIFIED LIVE: compatible deployment preserved React CSS/design,12 model
profiles, original3 active staff records,3 old archived records and2 gallery
entries. One new genuine PCB1 owner inspection saved privately (DINOv2 score
0.3130060434, threshold0.1414354295,747.28ms inference) with original/heatmap.
One live cited Qwen heatmap answer, private review and alert acknowledgement
persisted. Same-account second tab received updates; all evidence survived the
final Space restart and browser reload. Owner report and signed private images
loaded. Personal/team totals were1 and4, separate from public-gallery counts.

Explicit sharing created exactly one team copy, excluded private conversation/
review by default, and duplicate share returned Already shared without duplication.
Separate team note/review and the new team alert acknowledgement worked. Both
Personal and Team filtered QA archive/restore passed; each preserved the other
scope and left all pre-existing active/archived records untouched.

Gallery personal-source lifecycle passed: explicit unchecked-by-default consent,
independent guest read with matching measurements/redacted JPEGs, UI withdrawal,
404 public detail afterward, original2 entries still visible. New QA private and
team records remain active for traceability. The withdrawn QA gallery row remains
hidden and counts against lifetime publication caps; no deletion was performed.

Final live public/anonymous19/19 and owner-report/known-record guest-denial16/16
checks passed. Anonymous new tables/RPCs return permission denials, guests cannot
enter Team or access known private records/artifacts/messages/reviews, invalid
tokens do not become guests, guest CSV excludes private records.

Live testing found and fixed misleading archive/scope copy and nested component
remounts during polling. Stable Gallery/Filters/Table identities, corrected Staff
context and scoped archive wording were deployed in a frontend-only follow-up
(3 files,346848 bytes). Final frontend20/20 and local/cloud/static builds passed.
Original CSS asset index-Bn4HF2vD.css stayed identical; final JS index-DCyhJBD5.js
was verified in browser. Earlier backend51/51 focused result remains valid;
no backend changes were made for this final UI-only follow-up.
Eight final UI checks also passed, including both scoped archive wordings and
restored Team notes/review. The last dialog was cancelled without another write.

LIMITATIONS / NEXT OPTIONAL TESTS: only the approved developer-role account was
available; no real second staff, regular staff-role or authenticated non-staff
cross-owner E2E was run. No forced live outage, quota exhaustion, audit-table
actor/time inspection, opt-in conversation team copy, new guest import or owner
browser CSV download was performed. Local software/source coverage is recorded
separately; do not label these live passes. Free GPU capacity/quotas and temporary
guest history remain constraints. Pending batch files stay browser/device-local.
Signed URLs are temporary bearer capabilities; model provenance is unattested.
Some narrow-viewport automated pointer actions required keyboard fallback;
not every pointer issue was proven resolved. Manual multi-viewport checking is
still useful. The live app tab remains open; the extra test tab was closed.

See docs/MULTIUSER_LIVE_VERIFICATION.md for the complete evidence matrix and
private receipt filenames. No retraining, model/dataset changes, paid service,
GitHub push, destructive database action or active inference/training job.
DO NOT rerun SQL or completed experiments. Keep existing feature configuration.
Resume unperformed account/failure checks only with appropriate accounts and
authorization. This checkpoint supports the verified demo workflows; it is not
a complete production-security certification.

---

# Personal workspace active; owner E2E in progress â€” 19 October 2026

Compatible cloud commit49463314 is now active with
DEFECTRAG_PERSONAL_WORKSPACE=1. User initially reported activation, but the exact
variable was absent and health still false. Agent applied the requested public
variable through the existing deployment connection and restarted once; live
health confirmed true. No secrets, schema or existing records were modified.

All19 activated public/anonymous checks passed. Three existing staff records and
both gallery snapshots remain intact. One real owner PCB1 inspection saved
privately, with actual DINOv2 score0.3130, threshold0.1414,747ms inference and
heatmap. A second tab automatically received personal history and an alert.
Only the new QA-PERSONAL-20261019 test record is used for mutation tests.

OWNER E2E PASSED: Qwen cited heatmap answer, private review, personal ack1->0,
report with private signed images,16 known-record artifact/guest-denial checks,
explicit team copy3->4, duplicate share without duplication, separate team note/
review, same-account cross-tab updates, personal filtered archive1->0 and restore
with original evidence intact. Team copy stayed active during personal archive.
Original3 shared records and2 public gallery entries preserved.

Live testing found misleading archive/scope copy and polled controls remounting
on parent refresh. Minimal source fixes are ready: scoped copy, Staff context,
and stable module-level Gallery/Filters/Table identities. No CSS/design change.
NEXT: final frontend builds/tests, personal-source gallery lifecycle, deploy
these small UI fixes while retaining activation, verify reload/durable state.
No real second staff/non-staff account exists for cross-owner tests;
anonymous/invalid-token boundaries are covered but not a substitute. See
docs/MULTIUSER_LIVE_VERIFICATION.md for exact evidence and remaining gaps.

---

# Compatible multi-user build deployed; activation pending â€” 19 October 2026

User now reports successful MANUAL execution of the reviewed personal-workspace
migration and authorizes compatible deployment and E2E testing. This supersedes
the previous withheld approval below. Agent executed no SQL and changed no
schema, records, staff allowlist or secrets.

Source checkpoint7d636ac deployed incrementally to HF commit
49463314b49e9a7407b80e4a18cbe3b5a85062d1 (parent46e957e). Space RUNNING on
free zero-a10g. Changed9 application/frontend files,418365 bytes; no model assets,
static showcase files or dependencies uploaded, no file deletions. Existing
Supabase public config compared equal; personal flag remains absent/disabled.

LIVE compatibility checks18/18 passed: flag off,12 models and staff backend healthy,
exact original CSS, gallery enabled with both existing redacted JPEG snapshots,
independent guest empty private lists, all3 new personal tables denied to anon,
all5 tested personal/team RPCs denied to anon with42501 (not missing-function404),
invalid-token workspace API denial. Browser retained approved staff session and
all3 existing team records after reload. These prove legacy compatibility and
anonymous boundaries, not yet owner E2E or second-account isolation.
Receipts (private): development-support/space/personal-migration-confirmed.json,
personal-compatibility-published.json,personal-compatibility-public.json.

NEXT: finish browser staff/gallery checks; guide user to HF Settings -> Variables
and secrets -> New variable: DEFECTRAG_PERSONAL_WORKSPACE, value1 (not a secret).
Wait for user activation confirmation and verify health flag true. Then real
personal save, multi-tab history/conversation/review/ack, explicit team sharing,
scope counts, archive/restore, guest and gallery regression. Use only new labeled
QA records; preserve all existing rows. Do not claim a real second staff/non-staff
account test if no such account is available. No retraining/benchmark repeats.

---

# Independent multi-user hardening checkpoint; SQL NOT approved â€” 19 October 2026

Latest user instruction: "Not approved yet; continue independent code and tests."
Do not execute the migration, activate DEFECTRAG_PERSONAL_WORKSPACE or deploy the
multi-user upgrade. No approval request needs repeating. Current hosted behavior
is still legacy shared staff history; new owner-only privacy is not live yet.

Independent work completed after checkpoint6142375:
- Sharing controls discard late success/error callbacks after the view/account/
  scope changes, preventing an old record from reopening or showing an old notice.
- Polling preserves Offline when a pending request succeeds or fails after the
  connection drops; it cannot falsely mark that completion Synced.
- Personal-to-team image copying streams with a 10MiB bound, rejects empty/denied
  content, and sanitizes network errors. Failed transfers never reach the share
  RPC. Repeated sharing of an existing team copy does not download/upload again.
- Added software checks for full conversation preservation at the 40,000-byte
  import boundary and rejection before any upload when oversized.

Latest focused tests: backend51/51 (personal workspace, Space security, gallery),
frontend20/20, all local/cloud/static builds passed. Stylesheet remains
index-Bn4HF2vD.css. Receipt: development-support/personal-independent.xml.
These checks use software fixtures, no live SQL/authentication, GPU or retraining.
An initial test invocation selected a nonexistent test filename and collected no
tests; corrected invocation above passed. No running jobs remain at checkpoint.
Reviewed SQL hash below is unchanged. Application config, dataset, models,
evaluation results, gallery and hosted application are preserved.
Code/test checkpoint: f7e5272, synchronized to Desktop. GitHub-ready source copy
refreshed safely; no staging, push or deployment. Windows Desktop migration has
CRLF newlines and byte hash DFBF13A85CDEF3688D4854C1415DC3B732161152D1BE9EBE5A7A3A80A740B96D;
the source LF hash remains63e561bd234294286c6fc65b075ea130e9c021d60cf164ebf13d74a7c1f13ca1.
Full content equality after CRLF/LF normalization was verified. Neither SQL copy
was modified. Preserve their existing line endings during review.

---

# Multi-user upgrade implemented locally; SQL approval pending â€” 19 October 2026

User request: secure owner-only personal history, explicit authorized team
sharing, near-real-time dashboard/alerts, separate public gallery; preserve UI
and AI. Inspected checkpoint99bfb72 and the actual repository/auth flows. Found
all current signed-in saves go to shared_inspections/team-inspections; personal
cloud privacy did NOT exist. Guest history is isolated temporary SQLite; batch
files/checkpoints are browser IndexedDB. No new model work is required.

Prepared manual migration deployment/supabase_personal_workspace.sql and review
guide docs/MULTIUSER_WORKSPACE.md in checkpoint0fc4506; copied to Desktop.
Requested review/approval with async question. User subsequently replied
"Not approved yet; continue independent code and tests." No execution confirmed.
Exact migration SHA256:
63e561bd234294286c6fc65b075ea130e9c021d60cf164ebf13d74a7c1f13ca1.
DO NOT execute or alter this reviewed migration without user authorization.
Optional rollback-only policy test SQL prepared separately, not executed.

Implemented: owner-only PersonalRepository with immutable hash-named images,
verified/idempotent writes and bounded explicit guest imports; team copy via
owner-checked RPC; private conversations/reviews; separate scope statistics;
request and artifact scope binding; owner personal recovery; approved staff/developer
team permissions retained. New inference is personal-only when activated.
Frontend retains exact CSS/design; minimal storage labels/scope selector/share
conversation opt-in; correct workspace counts; serialized polling/focus/online
refresh/cross-tab mutation invalidation; stale/error/offline state; selected
reviews/messages and expiring artifact links refresh. Guest reviews import as
provenance-labeled notes, never falsely attributed authenticated decisions.
Stable single submission IDs and known duplicate HTTP400/409 handling allow retry
without duplicate saves. Public gallery state refreshes; protections preserved.

Validation: full Python117/117 passed; final privacy/session/gallery43/43 passed,
including2 additional cases (119 distinct covered across runs, not one full119
run). Frontend15/15; local/cloud/static builds passed with unchanged CSS hash
index-Bn4HF2vD.css. No retraining, dataset/model edits, new dependencies or GPU
requests. Actual new-schema RLS, second-account and hosted personal/team E2E
checks have NOT run. Software fixtures do not establish live database security.
Private receipts: development-support/multiuser-tests.xml,personal-final.xml.

Feature is gated by DEFECTRAG_PERSONAL_WORKSPACE=1; default remains legacy team
mode. Current HF production has NOT been changed for this upgrade; existing
team and gallery records remain as previously verified. Prepared source builds
are isolated. SQL, tables/policies, staff membership and service secrets unchanged.

NEXT: await user approval AND successful manual SQL execution. Then deploy
compatible source, verify legacy access, activate the variable once, and run
real owner inspection across sessions, independent guest denials, explicit team
share, note/review/ack propagation, archive/restore, duplicate/failure handling
and gallery regression. Invite a real second staff/non-staff test account only
if authorized; otherwise document that gap and use the optional rollback SQL
owner/non-staff/anon policy checks. Do not claim completion until E2E passes.
Exact source upload list now37 paths in docs/WORKFLOW_UPDATE_FILES.txt. Never
upload runtime/gallery-setup, supabase.txt, configuration secrets, datasets or models.
No new GitHub push or paid service. Preserve completed experiments and published
gallery items. Legacy pending batch checkpoints remain stored under old keys;
do not blindly replay them into Personal scope. See review guide for other limits.

---

# Community gallery activated and live-verified â€” 19 October 2026

COMPLETED: user confirmed executing the generated SQL manually and configuring
both HF settings. Live /api/gallery now enabled; existing12 models and Supabase
staff persistence remain available on Space46e957e3b0ba022ef92bd40e3a261a37a8c7b8ab.
No direct SQL, secret reading, service-role key, retraining or new GPU inference
was used by the agent during activation verification.

Verified live: existing2 public snapshots readable without login; actual JPEG
original/heatmap previews <=512px with no EXIF; public payload excludes private
IDs, account/filename/batch, conversations, notes/reviews and signed URLs.
An independent cookie-free guest workspace has empty private history; cannot
read the known existing staff QA record or publish it (both404), withdraw a
foreign publication (409), or moderate (403). Direct anon reads of all3 gallery
tables denied. Anonymous key configuration and empty/wrong gallery capability
calls denied. These requests did not alter records or keys.

Signed-in staff browser explicitly published the existing genuine PCB1 public
VisA QA sample through the unchecked-by-default consent control. A separate
guest client saw the new public snapshot and matching real saved score .31301,
threshold .14144, original and heatmap. Gallery increased2->3. Browser withdrawal
succeeded; public detail now404; original2 items remain unchanged (count2).
Staff history still shows all3 pre-existing inspections including the QA source.
No staff notes, conversations, archive state or inspection measurements modified.
The withdrawn gallery snapshot remains hidden for moderation and counts against
the configured lifetime gallery/publisher limits, as documented.

Receipts (private, ignored): development-support/gallery-activation-checks.json,
gallery-live-lifecycle.json, gallery-cloud-check.json and
 gallery-hosted-verification.png. Existing software suites104/104 and frontend11/11
remain valid; no application source change was needed after manual activation.
The additional targeted gallery suite19/19 previously passed.

No remaining activation blocker. Actual non-staff account, successful staff hide
of a visible publication and fresh hosted guest publication were not repeated;
negative authorization and local guest publishing/isolation tests cover those
boundaries partially. Free hosting/API limits, lack of proactive moderation and
CAPTCHA, guest browser identity, public-copy caching and the100/5 lifetime caps
remain documented. Guest withdrawal needs the original browser workspace.

Resume only for a new user request. Do not repeat model training or benchmarks.

---

# Opt-in community gallery implemented; hosted activation pending â€” 19 October 2026

User approved implementing the optional public demo gallery and preparing an
additive SQL migration for manual execution. No Supabase SQL was executed by the
agent. Existing staff tables, records, policies, models and calibration preserved.

Implemented separate public snapshots: explicit strict consent; server-resolved
saved measurements; fresh random public IDs; resized metadata-free original and
heatmap previews; no filename, private ID, batch, owner, conversations or reviews.
Anonymous paginated browsing, publisher withdrawal and approved staff moderation.
Hidden entries remain private; cannot auto-republish. Atomic SQL caps: 100 total
and 5 per publisher, including hidden entries. No GPU needed for publication.

Backend104/104 tests passed including a two-browser isolation/publication test;
frontend11/11 tests passed. Local/cloud/static builds passed; original stylesheet
unchanged. Browser verified unchecked consent disables Publish; checked consent
publishes an existing genuine PCB1 result; gallery shows matching measurements
and both actual image/heatmap previews. No new inference, training or downloads.
Temporary test-client sandbox loopback restriction diagnosed; final tests passed
outside sandbox. No repeated model experiment was performed.

Read docs/COMMUNITY_GALLERY.md and deployment/supabase_public_gallery.sql.
Run deployment/Prepare-Gallery.ps1 from the Desktop application to generate a
private runtime/gallery-setup/gallery-setup.sql and gallery-key.txt. User manually
runs generated SQL in the existing Supabase SQL Editor; sets HF SECRET
DEFECTRAG_GALLERY_KEY to that key, HF VARIABLE DEFECTRAG_GALLERY_ENABLED=1.
Do not send the secret in chat or commit runtime. No service-role key needed.
Cloud gallery remains disabled unless both settings exist. Never fall back to
Space SQLite for supposedly durable public snapshots.

Browser withdrawal passed: gallery became empty; private saved history preserved.
Hosted update d49c762685a1abbb7a30a5586079caca0e1ab3a2 deployed successfully.
Public API confirmed 12 models, staff persistence, gallery disabled, empty gallery,
unscoped publication rejected401 and new frontend. Hosted browser shows the correct
setup notice. Desktop synchronized, key and generated SQL prepared privately.
GitHub checkout was clean at940578e;29 allowlisted files prepared without staging
or push. Targeted final gallery19/19 passed after UUID validation tightening.
Final UI polish published as46e957e3b0ba022ef92bd40e3a261a37a8c7b8ab;
Final HF runtime verified RUNNING on46e957e3 with free zero-a10g hardware.
Source/Desktop checkpoint652889d,29 GitHub files prepared, no push.
Temporary preview PID8372 stopped; agent-created test tabs closed.
REMAINING: user manual SQL execution and two HF
settings; then hosted write tests. Do not repeat completed model experiments. After manual
SQL/settings confirmation, test real hosted anonymous publication, independent
visitor reading, authorization denial and withdrawal; new SQL is not yet verified
against the live database. Limits: free quota/bandwidth, no proactive image
moderation/CAPTCHA, browser identity not a strong anti-abuse mechanism, no recall
of downloaded/cached public copies. Guest withdrawal requires original workspace.
Dedicated key rotation changes publisher hashes; preserve it on normal upgrades.

---

# Workflow fixes complete, hosted and Desktop synchronized â€” 19 October 2026

COMPLETED: public Space RUNNING at41b9f9b1433942325cf73110476e0ae0e964a35e.
All seven requested fixes/additions are active: scoped asynchronous responses,
consistent refresh, saved-record category/batch synchronization, filtered/all CSV,
clean report metadata, failed-only batch recovery/replay, human review status,
decision/reviewer/time and clearer errors/cloud labels. Existing design/CSS retained.
Implementation626f42e; Windows update-command safeguardad1a140; build/publish
configuration safeguard8fba13d. No models, dataset, metrics or schema changed.

Final verification:85 distinct Python regression cases covered across full84/84
and final focused44/44 runs; frontend11/11 plus batch harness; all three builds.
Two genuine local DINOv2 inspections passed, along with invalid-image rejection,
reload recovery, failed-only retry and same-ID replay returning the original result.
Record count remained2. Local Reviewed/Hold decision and filtered export passed.
Hosted CPU checks10/10 passed, current UI and exact CSS confirmed, all12 models and
staff persistence available, unauthorized requests denied, unknown API now404.
Signed-in hosted review saved to the existing QA record, reopened through the new
Staffâ†’inspection link, and appeared with actor/time plus the original note in the
cleaned report. Both640Ã—488 report images loaded. No new hosted GPU request.

Publishing initially exposed a blank example Supabase config copied by Vite. This
was corrected using the preserved Desktop public settings. The Space builder now
preserves installed config byte-for-byte; publisher preflight rejects a blank staff
config. Default rebuild preservation check passed. Existing DB/RLS records untouched
apart from the explicitly labeled QA review note; no SQL executed or access expanded.

Desktop code/local build synchronized; personal config and guide hashes preserved,
untracked VisA folder untouched. Existing GitHub checkout at88d58f1 now contains
the22 prepared source/docs files, unstaged and unpushed. Exact Desktop PrepareOnly
command passed, and full staging command passed in an isolated temporary checkout.
User can run deployment/Update-GitHub.ps1, inspect staged changes, commit and push
origin HEAD. Exact file list:docs/WORKFLOW_UPDATE_FILES.txt. No duplicate archive.

Temporary local preview PID27704/session28611 stopped, test tab closed. No training,
new model download, new paid service or local background job remains from this work.
Final private receipts:development-support/workflow-local-verification.json,
workflow-cloud-verification.json, workflow-fixes-tests.xml, workflow-fixes-final.xml,
workflow-hosted-review.png. Public screenshot:docs/assets/workflow-review.png.

Limits retained: ZeroGPU quotas; pending batch files recover only in the same
browser/account/site context (not a shared cloud queue); acknowledgements still mean
seen while human review is separate; conversation model provenance not attested.
Mobile emulation, actual second/non-staff account and sustained-load tests remain
unverified. No further development is required for the seven requested changes.
Do not rerun completed training/benchmark experiments or auto-push GitHub.

---

# Workflow fixes implemented locally â€” 19 October 2026

User authorized all seven summarized workflow fixes/additions and GitHub update
commands. Implemented scoped asynchronous inspection/chat/history responses,
saved-record form synchronization, shared-data refresh/events and section errors,
filtered/all CSV, report field allowlist, readable upload errors/cloud labels,
browser IndexedDB batch recovery with failed-only retry, stable per-item request
IDs/content fingerprints, and append-only human reviews with reviewer/time/decision.
Existing CSS/layout preserved byte-for-byte. Models, data, metrics and policies
unchanged. Human reviews use existing staff_notes RLS or SQLite audit_events;
no Supabase SQL or schema modification is needed or executed.

Local genuine verification: PCB1 anomaly and normal sample succeeded, one invalid
batch image rejected. Batch restored after browser reload; retry skipped completed
image; same-ID replay returned original saved result with record count unchanged.
Human Reviewed/Hold decision survived reopening and appeared in the cleaned report.
Category/batch synchronization and filtered CSV verified. Separate QA runtime is
runtime/workflow-qa; original runtime and staff history preserved. No retraining,
new models, GPU benchmark experiment, dataset copy or dependency installation.

Tests: full Python run84/84 passed; after the stable-ID addition, final focused
application/security/workflow tests44/44 passed. 85 distinct Python cases covered
across these runs. Frontend11/11 plus existing batch harness passed. Local, cloud
and static builds compile with original CSS hash; final Team token-refresh change
requires the last rebuild before publication. Public deployment is still old
revision3b68268 at this checkpoint. Local preview PID27704 / port8786 is temporary.

GitHub update manifest and safe copy/stage script prepared:21 exact source/docs
paths, no automatic commit/push, no private config or assets. Existing GitHub
checkout is clean at88d58f1. Desktop personal config and deployment guide edits,
and untracked VisA dataset folder, must remain unchanged during synchronization.

Next: finish final builds, commit; incrementally publish existing HF Space and
verify CPU boundaries + signed-in review flow without repeating GPU requests.
Then fast-forward Desktop with configuration hashes preserved, prepare the existing
GitHub export in place, and provide the PowerShell commands. Keep browser-only
batch recovery, quota and independent-account/mobile testing limits explicit.

---

# Public application QA checkpoint â€” 19 October 2026

Exploratory review completed against hosted3b68268a582dce6ad731e5a362988eb6d1d9b99e
(RUNNING), source baseline0554152. Findings and reproduction steps are saved in
docs/PUBLIC_QA_REVIEW_20261019.md. No working app code, UI design, models, datasets,
SQL policies, old records or deployment were changed during the review.

Fresh results: genuine PCB1 anomaly score0.313006 vs threshold0.141435, heatmap and
viewer passed; relevant live Qwen heatmap answer cited sources; direct score/verdict
answers and unsupported-repair abstention passed. Guest-to-staff share, saved
conversation append, staff note, alert acknowledgement, report/images, navigation
and benchmark switching passed. Two-image capsule batch: normal completed (Good,
~0.132 vs0.144); anomalous file blocked by actual ZeroGPU quota. Do not resubmit
the completed file. Supabase login is separate from Hugging Face GPU allowance.

30/31 public boundary expectations passed (unknown route405 rather than404).
Both anonymous RPC calls correctly denied401/42501. Python suite78/79 initially;
one Windows long-temp-path SQLite failure passed in the targeted shorter-path
security rerun (9/9). All79 distinct cases successfully covered across those runs.
6 frontend tests and existing batch harness passed. No new training/downloads.

Open priorities: source-handler harness reproduced late-answer context mix-up;
main views stay stale after sharing until reload; opening PCB1 can retain Candle
in input; export ignores active filters; report table exposes signed URLs/internal
fields; misleading filtered-empty and raw image-validation errors. Detailed report
separates live findings, isolated software reproductions and source-only risks.

Two labeled QA records remain in Supabase (batches QA-20261019 and
QA-20261019-BATCH), including one QA review note and four saved conversation turns.
Existing three archived records were viewed but not restored or changed. No archive,
delete, schema change or paid service. Private receipts/screen captures are ignored
under development-support/public-qa-20261019. Do not publish private capabilities.

Remaining verification: mobile override ignored (actual1280px, reset), no actual
non-staff/second staff account test, no fresh live archive/restore round trip or
sustained load/cold restart/PDF output. Quota stops further GPU tests. No local
training/server job was started; test commands completed or were stopped.

Resume: read the QA review first. Fix request-context guards and refresh consistency
before adding features; keep existing UI. Then form/export/report corrections,
followed by separately reviewed durable batch/review schema enhancements. Do not
retrain or repeat completed benchmark experiments. No fixes deployed by this review.

---

# Targeted Macaroni update completed and hosted â€” 18 October 2026

COMPLETED: public revision3b68268a582dce6ad731e5a362988eb6d1d9b99e serves
macaroni-recall-v1. Public model/evaluation endpoints exactly match the new
manifest for all12 products; the other10 cards match previous q95 without changes.
Browser verified Macaroni1 recall0.850/precision0.780 and Macaroni2 recall0.800/
precision0.741. Visible policy warns of normal false alarms24%/28%. Proof saved
at docs/assets/macaroni-recall.png. UI design/CSS/navigation preserved.
Desktop code/local frontend synchronized throughb74bc3b; selected policy checked
with existing Desktop .env. Personal Supabase config and personal guide hashes
preserved. Restart an existing local backend to apply the new policy.
66 backend tests +6 frontend tests and both builds passed. No new inference,
training, GPU experiment, model download, paid service or database mutation.
All original assets/results/history/static showcase preserved. This is threshold
calibration with higher review load, not better AUROC or independent validation.
No local training/test/development-server job remains running from this task.
Final documentation/proof checkpoint synchronized. Existing GitHub source export
refreshed IN PLACE fromfe912bd:290 files,11.93MB, blank public config, credential
scan passed. No duplicate model archive. Private receipts record these checks.
Future model research remains optional, not automatically started. Do not repeat
completed inference or refit banks. Rollback DEFECTRAG_CALIBRATION=normal-q95-v1
(previous policy) or normal-max-v1 (original), then restart backend/Space.

---

# Macaroni-only recall improvement â€” 18 October 2026

User authorized targeted Macaroni1/2 recall improvement with minimal compute.
COMPLETED locally: separate macaroni-recall-v1 normal-q80 decision overlay,
Macaroni1 recall57% ->85%, precision77.98%, normal FPR24%; Macaroni2 recall48%
->80%, precision74.07%, normal FPR28%. Other10 category cards byte-for-value
identical to earlier q95 manifest. Overall macro recall88.83%, precision90.47%,
F1 89.57%, normal FPR11.10%. These are retrospective development-score results,
not independent validation or improved AUROC. UI and README disclose false alarms.
Encoder, banks, scores, heatmaps, official split/results, history and static
showcase unchanged. Saved-map audit: all95 q95 Macaroni false negatives had full
GT-mask nonzero support at224x224, so no evidence for wholesale foreground loss.
No new inference, GPU job, rotation bank, downloads, training or database write.
66 focused backend tests passed in13.37s;6 frontend tests and both builds passed.
New model IDs for the two categories end -q80-v1; historical records unchanged.
Default installed policy macaroni-recall-v1. Roll back to normal-q95-v1 or
normal-max-v1 via DEFECTRAG_CALIBRATION and backend restart. Do not refit assets.
Next: publish incremental policy/UI, verify hosted all12 cards and visible table,
sync Desktop with configuration hashes preserved, refresh existing small GitHub
source export in place. Do not create another model archive or repeat inference.
Details: docs/MACARONI_RECALL_UPDATE.md. Folder name remains DefectRAG-v2.

---

# Macaroni follow-up diagnostic â€” 18 October 2026

Read-only CPU check of saved real inference scores: Macaroni1/2 current q95 recall
57%/48%, normal FPR1%/7%. Fixed normal q90 diagnostic gives recall76%/66%,
precision86.36%/80.49%, normal FPR12%/16%. This diagnostic was NOT activated;
public revision3e1bf17 and normal-q95-v1 policy remain unchanged. No GPU request,
new model, training, downloads or database mutation. Review and bounded next
research design saved in docs/MACARONI_RECALL_REVIEW.md. Authors' preprocessing
code confirms rotations supported/enabled in agnostic VisA, disabled in informed;
our adaptation omits rotations. Benefit here is unproven. Next: false-negative
mask/heatmap audit, then one preregistered isolated preprocessing candidate if
approved. Do not repeat completed baseline experiments or claim independent
validation from the existing development-exposed official test set.

---

# Recall calibration deployed and verified â€” 18 October 2026

COMPLETED: Hugging Face revision3e1bf17dcff9622b61b6f662af810348c8ab109e
RUNNING. Public /api/models and /api/evaluation exactly match the new manifest
for all12 products. Browser verified new sensitivity text and full metrics table,
including PCB2 recall0.840, capsules0.820, candle0.870. Screenshot saved at
 docs/assets/recall-policy.png. No fresh GPU job was requested: this update reuses
saved real inference scores and changes only decision calibration. No database
write, retraining, dataset change or model download. 56 backend tests,6 frontend
tests and both builds passed. Static showcase and original evaluation preserved.
Desktop synchronized through9c44466 with local build and personal Supabase config/
guide hashes unchanged. Restart an existing local backend to use new calibration.
Normal-q95-v1 policy is active by default when its manifest is installed. Original
policy rollback: DEFECTRAG_CALIBRATION=normal-max-v1 and backend/Space restart.
Future work: independent validation before claiming guaranteed recall/FPR;
approved feature/model research for weak Macaroni1/2; prior staff-role/load-test
gaps remain as documented. Do not rerun completed experiments. No local training,
server or test process was left running by this task. Folder rename NOT performed;
Desktop remains DefectRAG-v2; follow docs/FOLDER_RENAME.md for coordinated changes.
GitHub export refreshed IN PLACE from9c44466:284 source/public files,11.86MB,
blank public config and credential-pattern scan passed. Receipt saved privately at
development-support/space/github-export-refreshed.json. No duplicate model archive
was created. Final documentation-only checkpoint should be synchronized; all
implementation and hosted verification work for this calibration is complete.

---

# Recall-oriented calibration milestone â€” 18 October 2026

User selected prioritizing anomaly recall with more false alarms. Audit reproduced
all 12 existing confusion matrices/precision/recall/F1 from saved genuine scores;
checked normal holdout content grouping, train/test nonoverlap and label polarity.
No inference, retraining, asset download or database mutation was needed.
New separate normal-q95-v1 manifest and guarded local/ZeroGPU adapter are ready.
Original cards, banks, encoder, evaluation, history and static showcase preserved.
Retrospective macro recall60.17% ->83.83%, precision97.59% ->93.26%, F1 68.63% ->
87.56%, normal false-positive rate2.42% ->7.43%. AUROC and image scores unchanged.
Policy chosen after viewing development diagnostics; NOT independent validation.
Macaroni1/2 remain limited (recall57%/48%). No guaranteed future recall/FPR.
56 focused calibration/highres/answer/API tests passed in9.66s,6 frontend tests
passed,local and separate cloud UI builds passed. Personal Supabase public config
copied into isolated cloud build and checked by hash (contents not logged).
Initial sandbox API tests stalled and were terminated; rerun outside sandbox
passed. No training/development server remains running from these checks.
Deployment and Desktop synchronization are pending this checkpoint; complete
those, verify public /api/models and /api/evaluation agree for all12 categories,
verify the visible performance page and record the published revision. Do not
repeat model experiments. New model IDs end -q95-v1; old records retain original
thresholds. Rollback: DEFECTRAG_CALIBRATION=normal-max-v1 and restart backend.
Details: docs/SENSITIVITY_CALIBRATION.md; audit results/recall_threshold_audit.json.
Folder rename was discussed but NOT performed. The Desktop path is still
C:\Users\User\Desktop\DefectRAG-v2. Source .venv/experiments junctions target that
path and sync_code.ps1 hardcodes it. A coordinated rename must update those and
verify the virtual environment. See docs/FOLDER_RENAME.md. Public Space unaffected.
The existing prepared GitHub export predates this calibration; do not claim it is
current until refreshed from the completed code checkpoint.

---

# Answer focus, brand and GitHub publication preparation â€” 18 October 2026

COMPLETED: code checkpoint59b61d11a008c70cc9df9d68f557ee8c6f8b6739, synced to
Desktop with rebuilt LOCAL frontend and both personal config/guide hashes intact.
Cloud b715fbf7b7d6237e9677550bda8dce02ce54ccb4 RUNNING; visible About/logo/RAG/
objective metrics heading verified. Source-only GitHub export is prepared at
C:\Users\User\Desktop\DefectRAG-v2\development-support\github-ready\DefectRAG.
Manifest275 source/public files plus export receipt,11.76MB, blank public config,
no Git history/models/datasets/private runtime/environments/build outputs. Known
credential-pattern scan passed. No GitHub repository was created or pushed.
README includes SVG hero/version badges/Mermaid diagram/actual dashboard preview.
All original model/evaluation files and static showcase backup remain preserved.
38 answer/API tests +6 frontend tests and both builds passed. No active local
development/training process was initiated. Existing local server needs restart
to load changed Python code; do not stop unrelated user processes automatically.
Further work is optional validation-based recall calibration (no test tuning),
previous role/load acceptance gaps, and a fresh live answer check when a staff
session is available. Do not repeat completed model experiments or asset downloads.

### Completion details and earlier preparation notes

LATEST: b715fbf7b7d6237e9677550bda8dce02ce54ccb4 RUNNING. Public About/new
logo, explicit RAG copy and objective evaluation heading verified in browser.
38 answer/API regressions and6 frontend tests passed; both builds passed, CSS
unchanged. Details docs/UI_AND_ANSWER_POLISH.md. No active staff session in the
new test browser; no fresh live Qwen response is claimed for this copy/assembly
update. Previous genuine RAG and Supabase acceptance remains preserved. No new
vision request, training, threshold study, model download or database change.
README and GitHub preparation scripts ready; commit then sync -SyncFrontend and
create Desktop source export. The export manifest will identify the source commit.
Existing Desktop public config and custom guide must retain their original hashes.

User requested question-focused RAG answers, objective interface text, clearer
recall/RAG/SOP explanation, new product-inspection logo and polished GitHub README.
Working from746a5bc; no models/thresholds/evaluations/database records changed.
Found unconditional measurement-prefix assembly in backend/rag.py. Heatmap and
documentation answers now omit unrelated verdict/score prefixes; score meaning
answers are direct; explicit result summaries retain trusted facts once. Existing
conversations preserved. Question-focused prompt added; source/citation guards stay.
38 focused answer/API tests passed13.48s (initial sandbox run stalled and stopped;
outside-sandbox run passed). Six frontend checks passed. Both cloud/local builds
passed; original CSS SHA remains087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661.

Cloud update published b715fbf7b7d6237e9677550bda8dce02ce54ccb4 (8 files).
Pending this checkpoint: verify updated live About/logo and one existing-record
heatmap answer, then commit/sync updated local build with personal config preserved.
No new inspection/retraining needed. Existing static showcase build is preserved.
README redesigned with original SVG banner, real version badges, Mermaid architecture,
honest benchmark/recall distinction, reproducible source setup and explicit limits.
GitHub export script allowlists tracked source, resets public config, excludes Git
history/private state/models and scans credential-like values. Optional pinned
asset downloader added; only --list executed, NO model download. Source clone path
now accepts DINOv2-only encoder assets in launcher. No GitHub repo/push authorized.
After final code commit, sync Desktop with -SyncFrontend, then run export from
Desktop to development-support/github-ready/DefectRAG. Review manifest/size/links;
do not upload entire working folder or private migration/runtime evidence.

## Previous deployment checkpoint (completed evidence retained)

CORE PHASES2â€“5 MIGRATION DEPLOYED AND VERIFIED for the available developer account.
Public: https://huggingface.co/spaces/Wizzas/DefectRAG
Cloud commit3717008401fcf9c85612ce6d4c0c77b629c39f53, RUNNING, ZeroGPU,
staff_persistence_enabled=true. Core code checkpoint53c48ce; this final documentation
checkpoint is identified by Git HEAD and the Desktop sync receipt. Do not redeploy
or repeat finished tests simply to resume. Source working tree should be clean
after checkpoint commit; Desktop retains the user's two config/guide modifications.

Verified final outcomes:
- Same original React CSS SHA256 preserved, navigation/appearance/static/local
  backups intact. Existing all12 benchmark metrics/models/calibrations unchanged.
- Existing all12 local/cloud DINOv2 parity and genuine cited Qwen tests preserved;
  no retraining or benchmark rerun. Latest13 CPU boundary checks passed.
- User manually executed reviewed SQL and signed into existing developer account.
  No agent SQL, schema/policy/account changes or service credentials used.
- Both RPCs: approved developer success and anonymous401/42501 verified. Invalid
  JWT403; missing workspace401. No existing nonstaff account available.
- Actual PCB1 a6351615259d42868b766a004f5dd303 saved to Supabase, six conversation
  turns including real contextual Qwen answer, exact note and acknowledged alert.
- Same record, conversation, note, images, acknowledgment survived browser reload,
  archive/developer restore and an actual Space deployment restart. Signed report,
  CSV and both private Supabase images200 after restart.
- Guest batch quota failure safely stopped pending submissions; old successes
  retained. User then signed into HF Wizzas (regular FREE verified) and staff in
  the embedded Space. Both unfinished Capsule images processed in successive
  one-image runs under PHASE5-STAFF-BATCH; latest run1 completed/0 failed. Separate
  staff browser session's signed export verified both durable IDs:
  88b2489b5759419a9caad724ade0ae53 (Uncertain0.20549749),
  ee823f7db3ae4a8fb687bb7b4d50896c (Good0.13208820). No duplicate model retries.
- Captured final logs: queue/session/response-started/CUDA-init/OOM counts0;
  bounded observation only. No local development or training jobs started.

Remaining limits/next work (do not mislabel these as passed):
1. Authenticated nonstaff RPC denial, ordinary-staff ownership/restore denial and
   distinct second-user collaboration need real existing accounts. User reports
   no nonstaff account. Do not create accounts or change allowlists without scope.
2. Single-click successful combined two-file batch remains unverified; both files
   actually succeeded as separate one-image submissions. Multi-file rejection and
   quota-stop behavior plus scheduler software checks passed. Do not re-infer the
   saved images just to repeat a completed individual case.
3. Free quotas/cold starts/shared capacity remain; long-duration concurrent load
   and broad reconnect campaigns were not run. No paid operation is authorized.
4. Staff-submitted answers lack verified model provenance. Acknowledgment lacks
   actor/timestamp. Existing stats/list/archive/export bounds remain documented.
5. Anonymous history is temporary. Staff records are durable. HF GPU identity and
   Supabase staff login are separate; embedded/direct app sessions can differ.

Read docs/PUBLIC_APPLICATION_GUIDE.md, ZEROGPU_PHASE4_RESULTS.md and
ZEROGPU_PHASE5_RESULTS.md. Sanitized evidence: docs/zerogpu_phase4 and
docs/zerogpu_phase5_final. Private reports/logs/capabilities/confirmation stay in
Git-ignored development-support/space; never publish that directory wholesale.
No new large ZIP/model/environment/dataset copy was created. The hosted app stays
running; no new model tasks should be initiated after this checkpoint.

---

## Superseded continuation notes (final checkpoint above takes precedence)

# Active Phase 4/5 continuation â€” 18 October 2026

LATEST: final public Space3717008401fcf9c85612ce6d4c0c77b629c39f53 RUNNING.
Core Phase4/5 developer flow VERIFIED, including actual restart preservation and
new Qwen contextual generation. Final CPU boundaries13/13 passed, staff enabled,
CSS unchanged. Post-restart signed report/CSV/images200, six saved turns and
acknowledgment persisted. See docs/ZEROGPU_PHASE4_RESULTS.md,
docs/ZEROGPU_PHASE5_RESULTS.md and docs/PUBLIC_APPLICATION_GUIDE.md.

Remaining active check: direct-browser batch0 successes hit guest quota; scheduler
submitted only first image and marked second not submitted, preserving old data.
User has now signed into both HF (Wizzas regular FREE verified) and Supabase staff
inside the hosted iframe. Browser file-chooser automation failed twice across that
iframe; no GPU work was submitted by those failed upload attempts. User is manually
uploading ONLY capsules_good.jpg/capsules_anomalous.jpg to PHASE5-STAFF-BATCH.
Await their submission confirmation, read the actual outcome, and record it.
Do not re-run passed inspection/Qwen cases. No nonstaff account exists; real
authenticated nonstaff/ordinary-staff/second-user role acceptance remains limited.

After batch outcome: capture bounded final runtime/error summary, copy sanitized
evidence, update this header, commit and sync Desktop via sync_code.ps1. Preserve
existing config/guide hashes. No additional release ZIP, model copies or retraining.
No local development/training jobs were started; hosted app remains running.

## Continuation milestone details

User explicitly confirmed successful manual SQL execution in the existing project.
Private migration-confirmed.json records that confirmation and reviewed SQL hash.
Agent did not execute SQL. Phase4 incremental deployment published as
ebbcf47cdd1f87dcd7f94219fecaf7d5bac35db4 (13 changed files); startup/live staff
acceptance still requires verification. Resume only unfinished staff/RPC/persistence
and final stability checks. Do not rerun all12 model smoke tests or benchmarks.
Source baseline5dea41f. Preserve user config/guide and existing database records.

Phase4 first live checks PASSED: both RPCs deny anonymous caller401/42501 (not
missing functions); public CPU/API/assets checks13/13 passed, unchanged CSS,
12 categories, ZeroGPU=true, missing workspace401 and invalid staff JWT403.
Cloud startup RUNNING, captured missing-session errors0. No staff login yet;
await user's sign-in at the existing #team page. Do not claim staff persistence,
RPC success or nonstaff authenticated denial before actual account tests.
Investigated official HF quota docs: guest2min/day, free account5min/day, resets
24h after first GPU use. Supabase login and HF GPU identity are separate. Prepared
small batch transport fix stops pending submissions after quota error and retains
successful results; it does not increase quota or auto-retry. Tests use fixtures,
not GPU. Keep these changes for the next consolidated deployment after staff tests.

Phase4 staff milestone: approved existing developer signed in themselves. Genuine
PCB1 inspection a6351615259d42868b766a004f5dd303, score0.3130/threshold0.1618,
Anomalous, displayed666ms, saved directly to Supabase (visible in Staff workspace).
Measurement answer and real LIVE LLM CITED heatmap answer succeeded, exercising
the conversation append RPC. Continue notes, acknowledgement, reload/report,
archive/recovery and post-deployment restart preservation on this same record.
User confirms no existing nonstaff account: authenticated nonstaff denial remains
unverified; no account is created. Avoid repeated GPU work on this passed case.
Staff milestone2 PASSED: exact note saved through existing staff_notes RLS,
acknowledgement RPC changed queue to0 pending/Acknowledged, full browser reload
retained the shared inspection, both answers (four turns), images and exact note.
Testing reversible archive/developer recovery only on the single owned fixture;
no pre-existing staff records were present or modified.
Staff milestone3 PASSED: owned fixture archived then restored through developer
recovery; exact note, four conversation turns and both private images retained.
Main dashboard history reopened the shared record. Signed CSV/report returned200,
report storage=supabase and alert acknowledged=True; both signed Supabase images200.
Exact measured score0.31300604343414307, threshold0.16181933879852295, inference
666.43ms on CUDA. Private phase4-staff-artifacts.json/report/export saved. No tokens
are copied into public evidence. Next: final consolidated phase5 deployment,
verify this same durable record after restart, one bounded real two-image staff
batch and final logs. Do not repeat the passed inspection/Qwen conversation.
Phase5 published3717008401fcf9c85612ce6d4c0c77b629c39f53, runtime RUNNING. The
same inspection, prior four conversation turns and exact note survived the real
Space deployment restart; no re-inference/recreation was needed. Checking a new
contextual question against persisted history, then one bounded batch. Existing
anonymous session history remains intentionally ephemeral; only staff data durable.

## Prior verified checkpoint (SQL gate below superseded by confirmation above)

Phases 2 and 3 VERIFIED. Phase 4 prepared but disabled; Phase 5 partially verified.
Latest user answer: **SQL not executed yet**. Do not execute SQL or perform staff
database-writing/RPC tests. User will manually execute the exact reviewed
deployment/supabase_additive_conversations.sql. No additional phase approval is
needed; successful manual SQL execution and account-based acceptance are the gate.

Current verified cloud: a31f52b64c91b7d6dab34113bc17a5bfac37ff72,
https://wizzas-defectrag.hf.space. Real DINOv2 all12 inference and real Qwen3-4B
cited RAG passed. Existing React/CSS retained, no model training or new benchmark.
Phase3 source checkpoint: 2c4c31561c6451c25487a56e818fa71faa14f8b3.
The next Git commit adds readiness/error handling, bounded staff export pagination,
cloud-specific archive wording, nine security software checks and acceptance docs.
Those readiness changes are NOT yet deployed to the cloud; do not confuse source
readiness with live staff acceptance. Avoid another rebuild before SQL is ready.

Completed evidence (do not repeat):
- Phase2: 24 real images locally +24 in cloud, all12 categories. Verdict parity
  24/24; maximum score difference0.00052985549. Original benchmark results intact.
- Phase3: real Qwen heatmap/context answers passed citation/quote checks; measurement
  answers and scope refusal passed; ten saved turns. CPU BGE subprocess fixes the
  diagnosed ZeroGPU fork interaction. No Qwen weights downloaded to this laptop.
- Browser QA: nine navigation destinations locally and in cloud; genuine Cashew
  inspection4551ace05dba4237a22a1630f7b18d34 (score0.24145314, threshold0.13224798,
  Anomalous), live cited follow-up, history archive/restore, populated image/report
  evidence and signed CSV export passed. Generic Gradio private-file routes403.
- Browser batch: one real Capsules image completed (Good, displayed score0.132,
  threshold0.197); second image rejected by anonymous ZeroGPU run quota. UI showed
  1 completed/1 failed and retained success. Not a fully passed two-image batch;
  no retry or paid quota purchase. Screenshot and limitation saved.
- Existing44 focused regressions passed at Phase3. Latest9 security software
  tests passed0.63s; these are local fixtures, not proof of live Supabase RLS.
  Latest isolated frontend production build passed; original CSS unchanged.

Private resumable evidence: development-support/space (Git-ignored). Full reports
contain workspace secrets/signed capabilities: never publish them. Sanitized
summaries and screenshots: docs/zerogpu_phase2, docs/zerogpu_phase3,
docs/zerogpu_phase5; see docs/ZEROGPU_PHASE4_READINESS.md and
docs/ZEROGPU_PHASE5_PARTIAL_RESULTS.md.

Exact resume sequence:
1. Read this checkpoint, Git status and Phase4 readiness doc. Preserve Desktop's
   existing frontend/public/config.js and deployment/RUN_AND_DEPLOY.md user edits.
2. Await explicit user confirmation that the reviewed SQL executed successfully.
   Do not apply SQL, create accounts or create migration-confirmed.json before it.
3. After confirmation, record it privately, build isolated UI with existing public
   Supabase config and publish phase4. Existing RLS/tables/storage remain intact.
4. User signs in themselves. Test both RPCs with approved staff, anonymous and a
   real existing nonstaff account; no fabricated claims from software mocks.
5. Verify durable inspections/images/conversations/acknowledgements, collaboration,
   reports, archive ownership and developer recovery. Finish remaining quota,
   refresh/restart and multi-user acceptance; only then claim Phases4/5 complete.

Future hardening: staff-submitted conversation answers lack verified model
provenance; alert acknowledgements record no actor/timestamp. Staff dashboard
statistics cover latest1000 active records; archive operates on up to500 matches.
Anonymous history is temporary and quota-limited. No fitting/training jobs running.
Owned local compatibility server on8784 was stopped; no listener remains there.
original local app/Ollama/user processes are left alone. HF hosted app stays live.
Desktop code sync uses deployment/space/sync_code.ps1 with ff-only Git and checksums
for existing config/guide. Its private receipt records the exact synced commit.
Reviewed SQL SHA256: 025ef75f224fbefda7d24b9a291b4532ec43b014d8f7659209cd8de4578beb47.

---

## Superseded chronological notes (latest checkpoint above takes precedence)

# Phases 2â€“5 authorized â€” 18 October 2026 â€” IN PROGRESS

LATEST MILESTONE: PHASE3 LIVE CLOUD RAG PASSED at a31f52b64c91b7d6dab34113bc17a5bfac37ff72.
See docs/ZEROGPU_PHASE3_RESULTS.md and sanitized docs/zerogpu_phase3/rag-summary.json.
Existing BGE CPU execution now isolated in one CPU-only child to avoid corrupting
the ZeroGPU parent/fork runtime. Real Qwen3-4B generation passed (85 tokens2.465s,
peak8601.55MB); contextual follow-up passed (90 tokens2.696s,peak8649.42MB). Same
Blackwell48GB, same weights/revision; no laptop Qwen download. Ten conversation
turns saved for real inspection527791824aea4124b9f60ec9d173b048. Measurement-only
answers and scope refusal verified. Do not repeat these successful GPU checks.
Phase3 private report development-support/space/phase3-cloud.json; verifier resumes
passed cases and creates only ONE new integration inspection after an ephemeral
rebuild if the old record is genuinely gone.

Phase4 remains pending the user's MANUAL SQL success confirmation. No database
modification/RPC call has been performed. Publisher phase>=4 refuses to enable
staff persistence without development-support/space/migration-confirmed.json,
which must only be created after explicit user confirmation. Preserve exact reviewed
SQL. Continue UI/error/transport checks and other independent development now.

LATEST CHECKPOINT: Phase2 code 60a9e49, security/sharing checkpoint b1f28af.
Desktop fast-forwarded to60a9e49 with existing public config/guide hashes preserved.
44 focused regressions and6 new security software tests passed. Evidence XML in
development-support/space. Source changes after b1f28af are active Phase3 fixes.

Phase3 cloud candidate startup loaded/packed8.65GB successfully (Qwen4B plusDINO).
Initial cloud commit d09a296 failed CUDA worker initialization before any inference,
twice. Targeted CPU embedding warmup deferral/eager attention commit cd9f54c restored
vision: real new PCB1 request47ec26ea212841c7b83c47584e6aa10c and measurement answer
passed. After first BGE retrieval, generation worker again reported No CUDA GPUs
are available. This points to CPU embedding runtime contaminating parent GPU/fork
state; exact internal probe is unconfirmed. New fix isolates BGE loading/inference
in a bounded CPU-only subprocess; same model/CLS/L2 pooling, same Qwen and vision.
That Phase3 fix is being uploaded; inspect latest publish-phase3 receipt/runtime
and resume verify_rag without repeating completed all12 cases. Full cloud RAG is
NOT yet verified. No Qwen weights were downloaded to the laptop.

User explicitly says: approved migration is for MANUAL execution only; agent must
not directly modify Supabase. Await their success confirmation before RPC tests.
Do not run migrations or create test accounts. Staff login is available when ready.
Documented hardening limits: no model provenance attestation for staff-submitted
answers; acknowledgement boolean lacks user/timestamp. Exact reviewed SQL includes
NULL checks and remains unchanged since their approval.

LATEST MILESTONE: Phase 2 local/cloud PASSED; docs/ZEROGPU_PHASE2_RESULTS.md.
Cloud commit 3784513453133497d4249a00f7daa32571a3bfef. All 24 per-environment
real integration cases saved; all verdicts match, max score difference0.00052986.
No missing-session/response-started errors in the captured post-test cloud log.
Hub1.31.0 cloud verified. Guest quota stopped after7 cases; resumed only unfinished
cases with the verified regular free HF account. No paid operations. Anonymous
history, artifacts and reports are session-isolated. Do not rerun passed cases.

Migration review update: user approved the exact reviewed SQL for manual execution
only, NOT direct database modification by the agent. Await confirmation of their
successful execution before testing RPCs with staff/anonymous/nonstaff accounts.
Record limitations: staff-submitted conversations lack model provenance attestation;
alert acknowledgements lack actor/timestamp. Do not enlarge the reviewed migration.
Phase4 repository scaffolding is not enabled in the cloud until its readiness gate.
Cloud live RAG is next. Local RAG already passed against existing records.

User explicitly approved continuous Phases 2â€“5 from 5fdff26. Earlier STOP/approval
notes below are historical. Preserve React appearance, local app/static showcase,
models/results/configuration. Do not train, pay, delete data or replace architecture.
Additive database migrations must be reviewed before execution. User can sign in
to an existing staff account when the test page is ready; do not request passwords.

Phase 2 implementation is isolated under deployment/space. All 12 existing banks
load eagerly with checksums; original highres encoder, PCA/scoring/thresholds and
heatmaps are reused. Browser session namespaces isolate anonymous history; image
and report links use expiring signed capabilities. Sequential batch transport
preserves existing result/error contracts. Fresh per-job Gradio clients close
deterministically; cloud stream lifecycle still requires verification.

Local 24-request smoke PASSED (one normal/anomalous resized public sample per
category), including real CUDA output, all heatmaps/reports, same-bank checks,
cross-session isolation, unsigned-image rejection and invalid image rejection.
Saved private report: development-support/space/phase2-local.json. Do not repeat
these successful GPU requests; verifier resumes saved cases. This is integration
evidence, not a rerun or revision of the model benchmark/AUROC.

Phase 2 cloud update is in progress. First upload failed before committing because
Windows default decoding corrupted the README emoji; explicit UTF-8 fixed it.
Hub 1.31.0 is verified published and satisfies Transformers>=1.31 and the platform
datasets<2 dependency, replacing the Phase1 Hub 2.2 cloud warning. Production local
dependencies unchanged. Check publish-phase2 receipt and Space runtime before any
next upload. Existing phase1 Space remains until a commit succeeds.

Read-only Supabase probe: public auth settings HTTP200; staff_members,
shared_inspections and staff_notes reject anonymous reads (401/42501). This is
not yet authenticated RLS verification. Existing public config URL/key reused,
no credentials printed, no database changes. User can sign in when ready.

Phase 3 provider scaffolding: inject a generator into the existing EvidenceWorkflow,
keep existing BGE CLS/L2 pooling on CPU and existing citation/measurement checks.
Qwen3-4B-Instruct-2507 candidate pinned cdbee75f17c01a7cc42f958dc650907174af0554,
8,044,982,000 weight bytes. Cloud-only loading planned; no laptop Qwen download.
Must verify actual cloud RAM/GPU/time/quality before claiming live generation.

Active local development server: isolated port 8784, exec session 28223 (PID17032).
No training/benchmark jobs. Next: cloud all12/parity and stream checks; phase2 Git
checkpoint; bounded live RAG local/cloud tests; additive persistence migration
review then authenticated staff tests. Do not stop simply because a phase finishes.

---

# Historical ZeroGPU Phase 1 â€” 18 October 2026 â€” core passed, issues recorded, STOPPED

User approved React + Gradio Server architecture and Phase 1 compatibility ONLY.
Phase 1 passed locally and on the existing empty Wizzas/DefectRAG ZeroGPU Space.
STOP here. No Phase 2, full RAG migration, Qwen download, training, Supabase
schema change or full production deployment is authorized.

Read docs/ZEROGPU_PHASE1_RESULTS.md for detailed evidence and limitations;
deployment/zerogpu_phase1/README.md for exact local resume commands. All new
implementation is isolated under deployment/zerogpu_phase1. Existing React/backend
source, CSS, dist/static showcase, models, thresholds, data and evaluations remain
unchanged. Desktop's preexisting config.js and RUN_AND_DEPLOY.md edits are preserved.

Completed: original React served by gradio.Server, nine navigation pages checked,
file upload, real @gradio/client -> scheduled DINOv2 -> saved score/heatmap -> React,
comparison/zoom, HTTP report/history/evaluation/CSV and identical production CSS.
Exactly one real local and one cloud inspection were run; no benchmark repeated.
Local score 0.3130886257; cloud 0.3130060434; both Anomalous, threshold 0.1618193388.
Cloud GPU: RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb; ZeroGPU=true.
Cloud Python 3.12.12 / Torch 2.8.0 / Gradio 6.30.0 / spaces 0.51.3 /
Transformers 5.20.1 / Hub 2.2.0. Local original production environment unchanged.
Gradio/old Transformers Hub conflict resolved only in isolated test environment.
One HF CONFIG_ERROR fixed by removing +cu128 from requirements' Torch version.
Unused preinstalled datasets/Hub dependency warning remains documented.
After successful result delivery, cloud logs show Gradio SSE missing-session 404
errors and a response-already-started exception. Immediate server condition traced
to missing pending_messages_per_session entry; reconnect/cleanup trigger remains
unconfirmed. This needs bounded lifecycle diagnosis before a production migration.

Public test: https://huggingface.co/spaces/Wizzas/DefectRAG
Cloud commit 84df9af3f59b2fe43fdb6ad14a1820c930329abc. Only public PCB1 fixture
and its bank are accepted; no private history/config, RAG, batch or cloud staff
migration published. The separate Wizzas/defectrag-inference Space is untouched.
Read-only metadata and local/cloud verification saved under
development-support/zerogpu-phase1 and docs/zerogpu_phase1. Genuine local artifacts
and isolated SQLite remain in runtime/zerogpu-phase1. No new large release ZIP.

Owned local adapter on port 8783 stopped after testing. No owned training or
inference job remains. HF minimal test remains hosted/idle and can sleep; temporary
history is not durable. All other existing user processes are left alone.

Next only after approval: diagnose SSE session cleanup; review HF iframe identity/quota and restart
tests, clean the unused cloud dependency warning, then migrate bounded vision
requests for remaining existing banks with approved parity checks. RAG and durable
Supabase persistence remain later gates. Do not repeat completed work or rerun
publish_minimal (it intentionally refuses to overwrite the existing test).

---

# Historical ZeroGPU assessment â€” 17 October 2026

User requested feasibility/architecture review ONLY before major implementation.
Assessment complete in docs/ZEROGPU_MIGRATION_ASSESSMENT.md. STOP here for approval.
No UI, application code, dependencies, models, data or cloud services changed.
No GPU runs, installations, model experiments, rewrites, new ZIPs or deployment.

Recommendation: preserve the exact React/Vite UI in one Gradio SDK Space using
documented gradio.Server mode; @gradio/client transports scheduled GPU requests,
existing CPU/FastAPI services retain reports/evaluation/history contracts. Use a
separate ZeroGPU runtime adapter for DINOv2 (DINOv3 optional), CPU BGE retrieval,
an injected in-Space Transformers generation provider, and the existing Supabase
project for durable authenticated history/artifacts/collaboration. Proposed cloud
LLM candidate is Qwen3-4B-Instruct-2507 (not downloaded or tested for this app).
Existing local Qwen2.5-3B/Ollama remains unchanged. No model retraining proposed.

Current Desktop Git HEAD 67b2378. Preserve existing user edits to
deployment/RUN_AND_DEPLOY.md and frontend/public/config.js. Unlike older notes,
Desktop public and built configs now contain a non-placeholder Supabase URL and
publishable key. Do not overwrite them with the blank source-mirror config.
No live database/schema/RLS/login was checked; account/Space entitlement unknown.

Key risks: Gradio route ordering and HF iframe quota headers; lazy CUDA loading,
worker isolation/locks and CPU-only startup computations; unauthenticated global
SQLite/history must not be exposed publicly; ephemeral disk; separate Supabase/HF
identities; missing durable backend message/alert/artifact repository; generation
JSON differences, quota/cold starts and exact dependency compatibility. No claim
of cloud performance, numerical parity, or always-free uninterrupted availability.

Next after approval: only an isolated Phase 1 test retaining the React build,
one queued existing-model job, actual account hardware/quota context and dual-auth
transport. Then scoped vision parity, one generation provider, additive Supabase
migration and full UI/persistence acceptance. Details, options, files and gates
are in the assessment. Do not rerun old experiments or start implementation now.

---

# Local folder consolidation â€” 16 October 2026

Follow-up editor fix: backend/highres.py explicitly types the optional encoder
and checks it before .device/.encode access, addressing possible-None diagnostics.
Six focused detector tests passed; report development-support/device-typing-tests.xml.
No model assets, thresholds or saved benchmark results changed. Actual VS Code
hover diagnostics were not supplied; if an underline persists, inspect its exact
message and confirm the local .venv interpreter. No experiment rerun is needed.

The subsequently supplied reportOptionalMemberAccess screenshot was for the
legacy backend/vision.py. The same explicit optional type and checked local
encoder fix is now applied there. One real CUDA DINOv3 PCB1 inspection passed
(score 0.0961143672, Anomalous); development-support/legacy-device-smoke.json.
No training, thresholds, model assets or existing results were changed.

COMPLETED AND PAUSED near 4% usage at the user's request. Both receipt files
confirm status=passed. All 228 experimental receipt files are hash-verified;
both 12-category experiments, banks/results/caches, legacy projects, interpreter
and dependencies are now inside Desktop\DefectRAG-v2. Real CUDA API inspection,
inspection-grounded assistant, pip/uvicorn launchers and private-row preservation
passed. Existing CUDA PyTorch 2.8.0+cu126 retained, no packages reinstalled.
No training/benchmark or owned preview server remains. Global Ollama is unchanged.
No more development tasks should begin until the next user instruction.
On resume, read these receipts and Git status; use the simple command below.
Do not repeat migration, feature extraction, fitting or successful benchmarks.

User requested one Desktop application folder, without duplicating large assets.
This section supersedes old interpreter paths below. Consolidation status is
authoritative in development-support/consolidation-moves.json and
consolidation-verification.json. Only status=passed confirms all final checks.

Target: C:\Users\User\Desktop\DefectRAG-v2. Existing environment moves from
Desktop\.venv-defectrag into .venv (user had already moved it out of Verified).
Activation and executable entry points are repaired offline; no package download
or CUDA replacement. Local .python-deps replaces the Codex PYTHONPATH dependency.
Both complete experiments move here into experiments; the source mirror gets
a junction to avoid duplicate storage and accidental reruns. Original VisA stays
unchanged in Downloads. Legacy Unified project (including datasets/secrets) and
remaining Verified Git history are preserved privately under
development-support/legacy-projects, excluded from Git and release packaging.

Run after successful verification:
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Port 8767
VS Code interpreter: .venv\Scripts\python.exe. No external overlay variables.
The existing base Anaconda Python and global Ollama remain system requirements.

No new large ZIP is created. Existing local-accuracy and highres-benchmark-assets
ZIPs become optional backups after both experiments and real CUDA/API checks pass.
Deleting them removes independent backups, not the consolidated on-disk assets.
Do not delete runtime, models, experiments, .venv, .python-deps or legacy datasets.
No training reruns are authorized or necessary. Old owned previews on 8766/8771
may be stopped for consolidation; do not stop unrelated Python/Ollama processes.
Resume any incomplete move by inspecting the receipt before touching directories.

---

# Completed accuracy upgrade â€” 16 October 2026

This is the latest checkpoint; older sections below are historical. Preserve
every earlier model, experiment, dataset, history and release. Previous upgrade
is still recoverable at commit 39590a6. Final Git identity and packaging/sync
status are recorded in the sibling accuracy ZIP receipts and
development-support/release_sync_receipt.json; inspect these before repeating.

Completed: AnomalyDINO-inspired frozen DINOv2 Small/14, 448px short edge with
aspect retained, unsupervised PCA foreground, image-balanced normal memory up to
32,768 vectors. Three fixed benchmark seeds 42/43/44, all 8,659 official train
normals and identical 2,162 official test images across all 12 products. This is
a custom adaptation, not exact paper reproduction or weight fine-tuning.
Prior test exposure is disclosed; no fresh untouched-test claim. Masks and test
anomaly labels never fit the bank, foreground heuristic or operating threshold.

Measured overall means (original -> candidate): image AUROC 85.38% -> 95.13%,
image AU-PR 86.47% -> 95.74%, pixel AUROC 92.96% -> 98.60%, pixel AU-PR
33.29% -> 43.04%. Macaroni 2 image AUROC 48.27% -> 83.20%. Cashew image
AUROC regresses slightly; Cashew and Pipe fryum pixel AP regress. All rows and
seeds are saved, including regressions. Official VisA reports mean AUROC and
AU-PR; supplementary mean AP is separate from YOLO bounding-box mAP@IoU.

Operational model is a separate fixed-seed normal-holdout bank installed beside
the original models in models/highres. PROFILE.json enables auto selection;
DEFECTRAG_PROFILE=legacy restores the original DINOv3 detector. Its conservative
threshold yields macro precision 97.59%, recall 60.17%, F1 68.63%. Some anomalous
images are classified Good. High AUROC is not classification accuracy. No
threshold adjustment after test exposure was performed.

Saved assets: models/encoder_dinov2 (revision/hash/license receipt),
models/highres (all 12 operational banks/cards), experiments/dinov2_highres_v1
(all completion receipts, four banks per product, split/calibration/predictions,
metrics and intermediate caches/maps). Original DINOv3 assets are unchanged.
The benchmark finished successfully; do NOT repeat completed experiments or
restart scripts.train / benchmark_official / benchmark_highres.

Verification: 46 Python tests, six frontend checks, both builds, 24 real API
inspections across all 12 products, five assistant cases including real Qwen,
CPU/CUDA checks, browser benchmark profile switch and static provenance/privacy
checks passed. Actual receipts: results/software-tests-highres.xml,
highres_application_verification.json, highres_preservation.json and
static_verification.json. See docs/ACCURACY_VERIFICATION.md for exact limits.
The 25 static examples retain their original DINOv3 measurements; the static
benchmark includes both reports and does not pretend to run live inference.

Recoverable release artifacts (unique names; never replace earlier archives):
- DefectRAG-local-accuracy.zip: application, both detector profiles, builds/docs.
- DefectRAG-static-accuracy.zip: saved-example dashboard for free static hosting.
- DefectRAG-highres-benchmark-assets.zip: all experimental banks/manifests/
  predictions/metrics. Intermediate feature caches/maps stay on this workstation.
- development-support/git/DefectRAG-accuracy.bundle: code-only Git recovery.
Private database backup: development-support/saved-runtime/
desktop-before-highres.sqlite3 (integrity OK; 9 inspections / 10 messages).
Excluded from all releases. Original 66 model/evaluation files hash-identical.

Exact next steps on resume:
1. Inspect Git status and accuracy receipts; preserve any newer user edits.
2. In the user's existing PowerShell server window, Ctrl+C and use README.md's
   exact existing-computer command on port 8767. The already-running old process
   keeps its imported code until restarted. No fitting/build/install is needed.
3. Read docs/ACCURACY_AND_METRICS.md and ACCURACY_RESULTS.md before reporting
   performance. New experiments must have new versioned outputs and frozen
   settings, with a genuinely held-out evaluation if making generalization claims.
4. Supabase remains unprovisioned. User must create their own free project;
   deployment/SUPABASE_SETUP.md contains setup and hosted validation steps.
   No public deployment exists. Static hosting serves saved examples; live AI
   needs the local/running backend. Preserve optional cloud config and secrets.

Running state: benchmark session 55802 and acceptance session 91404 completed.
Owned port 8782 preview was stopped after browser checks. User's port 8767 /
PID 10108 and shared Ollama were left alone. Earlier preview ports 8766 / 8771
may remain; these are servers, not training jobs. No fitting job remains.
Docker execution, a fresh dependency installation, 390px mobile visuals and
hosted Supabase auth/RLS/storage remain unverified. Final archive/sync results
are authoritative in receipts, not inferred from the historical text below.

---

# DefectRAG development checkpoint â€” upgrade, 16 October 2026

This section supersedes the historical checkpoints below. Preserve original
assets and earlier archives. Visible branding is DefectRAG; directory stays
DefectRAG-v2 for compatibility. No Supabase project/account was provisioned.

Completed in this upgrade:
- Official VisA split experiment across all 12 categories, seeds 42/43/44,
  all 8,659 train normals and 2,162 test images; all masks evaluation-only.
  results/official_evaluation.json contains means/SD, per-seed and pixel metrics.
  Retrospective test exposure is disclosed. Macro image AUROC 0.854 / AU-PR 0.865;
  macaroni2 remains weak (~0.483). This is frozen DINOv3 patch memory, not fine-tuning.
- Every category has a verified completion receipt, three benchmark banks and
  a separate normal-only calibration bank in experiments/official_visa_v1.
  Completed experiments are skipped; do not repeat them. Current app banks and
  original evaluations are unchanged (66 files hash-checked).
- Saved-inspection measurement answers now state verdict/score/threshold directly.
  Five real HTTP assistant cases passed, including two real Qwen explanations
  and one follow-up. Root causes abstain; negative questions avoid ambiguous yes.
- New logo/favicon, larger fonts, stronger colors, transitions/reduced-motion,
  image comparison, zoom, expanded viewer, training/benchmark pages.
- Local Clear history archives; Recovery restores records/images/conversation.
  Browser verified archive/restore of two isolated Pipe fryum test records.
- Optional Supabase allowlisted staff login/sharing/notes/private images/archive/
  developer restore prepared. No hosted sign-in, RLS or storage test is possible
  until the user creates a Supabase project. Setup screen clearly shows this.
- Import configuration, environment checker and editor/training/evidence/cloud
  guides added. Current verified environment sees all eight required imports.
- Both builds and five frontend checks passed; static snapshot has 25 measured
  examples across 12 categories and refreshed recorded assistant answers.
- Vite 6.4.4 installed; dependency installation audit reported zero vulnerabilities.

Release artifacts (unique names; earlier ZIPs preserved):
- DefectRAG-local-upgrade.zip: source + current application models/builds/guides.
- DefectRAG-static-upgrade.zip: static public dashboard, no live AI.
- DefectRAG-official-benchmark-assets.zip: all experimental banks/manifests/
  calibration/predictions/metrics, hash/CRC verified. Extract into project root
  only when absent; never overwrite newer experiments. No source dataset images.
- development-support/git/DefectRAG-upgrade.bundle: code-only Git recovery.
Packaging/sync completion is recorded in sibling *.receipt.json and
  development-support/release_sync_receipt.json. Inspect those before repeating.

Preservation:
Original VisA dataset and DefectRAG-Verified are read-only and unchanged.
Desktop runtime is preserved, never replaced with preview data. Private backup:
  development-support/saved-runtime/desktop-before-upgrade.sqlite3
(integrity OK; 9 inspections / 10 messages at backup; excluded from release).
Preview runtime/ux-review is isolated. Models/experiments remain outside Git;
ZIPs preserve them. Git history is fast-forwarded, never reset or rewritten.

Resume/use exact next steps:
1. Inspect Git status, this file and release receipts; preserve newer edits.
2. Restart the user's existing server in its own terminal with Ctrl+C, then use
   the exact README command for port 8767 and the verified interpreter/overlay.
   No fitting, dependency installation or frontend rebuild is needed.
3. User must create a free Supabase project in their own account. Follow
   deployment/SUPABASE_SETUP.md and supabase.sql. Configure only public URL/key,
   invite staff, then verify anonymous/non-staff denial, staff share/read/notes,
   developer restore and expiring private images. Do not claim cloud connected.
4. For public saved-example hosting follow deployment/RUN_AND_DEPLOY.md.
   No public deployment exists; static hosting does not run Python/Ollama.
5. Optional future experiments require a new versioned output and frozen settings;
   do not replace production banks based on already-seen test metrics.

Verification details: docs/UPGRADE_VERIFICATION.md. Docker runtime, clean venv
installation and 390px mobile visuals remain unverified; VSCode Problems UI not
inspected. No training job remains. The owned port 8780 preview is stopped during
final teardown; existing user port 8767/PID10108 and shared Ollama are left alone.
Earlier port 8766 / static 8771 previews may remain; they are not model training.

All 40 Python tests passed (one third-party deprecation warning). Archive/Git/sync status is in the receipts and
results/software-tests-upgrade.xml. Do not call setup-ready Supabase fully tested.

---

# DefectRAG v2 â€” development checkpoint

## Active upgrade â€” official protocol, assistant quality, UI and staff sharing

User authorized the official VisA-split experiment, inspection-grounded conversational answers, DefectRAG branding/logo, larger type, richer colors/interactions, recoverable history and free Supabase staff sharing. No Supabase project has been created; user confirmed they do not have a known project. Setup/schema/client are being implemented, but hosted auth/RLS/storage checks remain blocked on project creation/public config. Do not claim cloud is active.

Official benchmark is isolated in experiments/official_visa_v1; exec session 27077. It uses all official training normals and all official test images, three fixed seeds, no test-based thresholds. A fourth normal-calibrated operational bank is saved separately and does not replace current app banks. Completed per-category receipts skip repeated work. Original baselines/models/history remain preserved.

Assistant now directly answers saved measurement questions with an explicit measurement-only mode; Qwen remains responsible for cited document explanations. Archive/restore preserves records, images/conversations and writes audit events. New regression suite: 36 tests passed, results/software-tests-upgrade.xml. Live cloud verification pending a project. UI build passed; isolated UX preview is being started on localhost:8780 (runtime/ux-review), leaving the user's Desktop server on 8767 alone. Vite patched to 6.4.4; npm install audit reports zero known vulnerabilities.

Current remaining work: finish and audit official results; finish UI/browser QA and response quality capture; inspect editor import visibility; document/install Supabase setup; refresh static snapshot and final unique release ZIPs; commit/checkpoint and synchronize Desktop without stopping the user's server. Resume this active work before the older checkpoint steps below. Save and pause if remaining usage approaches 3-5% as previously requested.


## Latest checkpoint: all 12 evaluated; paused near 5% usage

All nine missing categories completed fitting/calibration/final evaluation. All 12 cards, banks, split manifests and prediction files are saved. Original three-category models and predictions remain hash-identical (`results/all12_preservation.json`). No training or evaluation process remains active.

Completed integration: backend category allowlist and safe sample routing for all 12 (including pipe_fryum); dashboard labels and category count; weak-separation warning when image AUROC < 0.6; incremental --resume fitting safeguards. `results/all_categories_acceptance.json` records 18 real API inspections for the new nine categories, saved separately under runtime/verification12. Scores matched evaluation; heatmaps and reports passed. All 29 software tests passed in results/software-tests-all12.xml.

Both dashboard builds and 3 static contract tests passed. Static snapshot now contains 25 measured examples across 12 products. Snapshot hash/privacy/report-resource checks passed. Earlier three-category browser checks are preserved in results/static_verification_three_categories.json; browser QA for the expanded build has NOT been performed.

Important measured limitations: macaroni2 image AUROC is 0.46825 (weak; do not claim reliable detection). Macaroni1/2 localization is extremely weak; capsule/PCB2 localization is also weak. See docs/ALL12_EVALUATION.md for all 12 measured rows. No final-test tuning or extra experiments were performed. Existing clean serving profile covers only the original three categories.

The new artifact is DefectRAG-v2-all12-checkpoint.zip, a recoverable development checkpoint, NOT the final accepted all12 release. Earlier released ZIPs remain three-category versions and are preserved. Recovery bundle: development-support/git/DefectRAG-v2-all12-checkpoint.bundle. Archive and sync JSON receipts record hashes/commit and whether Desktop copy finished.

Exact resume steps:
1. Read this file, Git status and results/evaluation.json (must contain 12 categories). Do NOT refit or reevaluate completed categories.
2. Verify the expanded dashboard in the browser: 12 category options, 24 local samples, 25 static examples, pipe_fryum routing, all 12 performance rows, macaroni2 warning and static report/CSV links. Existing local preview on 8766 still has the OLD Python process/category allowlist; restart only that identified v2 preview before testing the new backend. Static preview on 8771 serves the rebuilt files; reload it.
3. Refresh README, deployment guide, static Space metadata and older three-category wording to the final scope. Keep old verification results clearly historical. Update final screenshot/browser receipt. Do not repeat model experiments.
4. Create unique final all12 static/full ZIP names; the old ZIP names must not be overwritten. Commit final documentation, create a new recovery bundle, then sync Desktop with scripts.sync_release --archive NEW_FULL.zip --bundle NEW.bundle --extra-archive NEW_STATIC.zip.
5. Preserve original dataset, runtime history and all models/results. The exporter uses runtime/verification12 (new nine examples) plus original runtime (earlier seven examples); both remain saved. No dependency installation is needed: use original verified Python + workspace sibling .test-deps overlay.

Processes at pause: training session 77130 and API/tests session 38315 completed successfully. Build/test session 1643 completed. No fitting/training/test job remains running. Static preview localhost:8771, v2 preview localhost:8766 and shared Ollama localhost:11434 may remain active; no training state depends on them. A new verification database is under runtime/verification12; never replace user history with it.

User requested saving around 3-5% remaining; account reported 5% at this checkpoint. Stop after checkpoint/archive synchronization and wait for a credit reset or further instruction.

## Earlier milestone â€” free static showcase (16 October 2026)

User requested a free static public version while preserving the full local app.
Implemented a separate read-only build using **seven allowlisted, real saved VisA
inspections**: the original six acceptance images plus the latest verified RAG
follow-up inspection. Model weights, datasets and evaluation experiments were
not changed or repeated. Obsolete LLM conversations with an old knowledge
fingerprint are excluded from the public snapshot. No private uploads are exported.

- Local production build passed after UI integration; live functionality remains
  in the ordinary build. Static build uses no backend or inference service.
- Three Node tests passed: static data loading/cache, rejected upload/chat/alert
  writes, real score/cited conversation/report URL preservation.
- `results/static_verification.json`: all seven scores match saved receipts,
  snapshot hashes pass, report images exist, no local paths/secrets/model files.
- Browser QA passed: seven records, image toggle, combined PCB1+Anomalous filter
  gives two records, final recorded Qwen explanation/follow-up, report images
  and source text, batch/alerts/performance/About pages. No captured console errors.
- Vercel static configuration, Render Static Site configuration and Hugging Face
  Static Space metadata are provided. No account/public deployment was created.
- Instructions: `deployment/RUN_AND_DEPLOY.md`. Dashboard proof:
  `docs/screenshots/static-showcase.jpg`.

New release names: **DefectRAG-v2-static.zip** (public files only) and
**DefectRAG-v2-with-static.zip** (full local app + static build/source).
Adjacent JSON receipts record archive size/hash and verification. Earlier
`DefectRAG-v2.zip` and its recovery bundle stay preserved.
The new code-only recovery bundle is
`development-support/git/DefectRAG-v2-static-release.bundle`.

Resume only if a new receipt is absent: inspect Git status; preserve newer edits;
run `python -m scripts.package_showcase` if its archive is missing, then
`python -m scripts.package_release --name DefectRAG-v2-with-static.zip` if missing.
After committing code and creating the new bundle, synchronize using:
`python -m scripts.sync_release --archive DefectRAG-v2-with-static.zip
--bundle DefectRAG-v2-static-release.bundle --extra-archive DefectRAG-v2-static.zip`.
Never overwrite an existing differing ZIP or restart completed model experiments.

Latest remaining scope: public account deployment is user-run using the documented
commands. The static site deliberately has no live image upload or chat. Full
browser inference/RAG conversion remains a separate future project. Existing
Docker/mobile/fresh-environment verification caveats below still apply.

Processes: a static preview was started on localhost:8771 (plain Python file
server; safe to stop/restart, no training state). The original local preview may
remain on localhost:8766 and shared Ollama on localhost:11434. No training,
benchmark or dependency-installation job was started in this milestone.
Usage checks reported 26%, 21%, then 15% five-hour allowance remaining. If usage reaches
3â€“5%, stop new work after updating this file and a recoverable Git checkpoint.

---

Updated **16 October 2026**, Asia/Kuala_Lumpur. User-authorized continuation completed
the remaining implementation and local verification. No fitting, dataset download
or expensive experiment was repeated.

## Deliverables and authoritative completion records

- Source and assets: `C:\Users\User\Desktop\DefectRAG-v2`.
- Final release: `C:\Users\User\Desktop\DefectRAG-v2.zip`.
- ZIP verification/checksum: adjacent `DefectRAG-v2.receipt.json`.
- Desktop synchronization/recovery: `development-support/release_sync_receipt.json`.
- Current Git commit: `git log -1`; release manifest also records the commit.
- Primary working source remains
  `C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2`.

The build/synchronization receipts are authoritative for final handoff. If a
disconnect occurs during the final archive/copy step and a receipt is missing,
resume that step below; do not repeat completed fitting or verification.

## Completed

- Actual DINOv3 ViT-S/16 nearest-normal inference for PCB1, capsules and cashew;
  calibrated score, Good/Anomalous/Uncertain result and coarse heatmap.
- FastAPI, React + Vite, SQLite history, batch inspection/filtering, local review
  alerts, printable reports and CSV export.
- LangChain source loading, chunking, local BGE retrieval and persistent index;
  LangGraph scope/retrieval/evidence/generation/validation/fallback workflow.
- Genuine local Qwen explanations and follow-ups. The model selects a source
  sentence by ID and writes its explanation; the application attaches the original
  quote and source ID, then validates citation/number consistency. No generated
  explanation is represented as a deterministic template.
- Fixed wrong-method evidence: current-detector questions exclude Dinomaly
  reconstruction passages. Follow-up retrieval uses the prior user topic, and
  stale assistant facts are excluded after knowledge changes.
- Completed README, architecture diagram, portfolio description, licenses/notices,
  frontend production build, verification report and desktop screenshots.
- ZIP packager verifies CRC, all file hashes, duplicate entries and required assets.
  Dataset, secrets, runtime history/uploads, dependency overlays, node_modules,
  caches and Git objects are excluded from the release.

## Verified results

**29 software tests passed**, no failures, one upstream AnyIO deprecation warning:
`results/software-tests.xml`.

**Extracted release candidate passed on Python 3.11.15**:
`results/release_extraction_verification.json`. Imports were confirmed to come
from a new extraction. It served the frontend, uploaded a real VisA image, loaded
the bundled model, produced a real score/heatmap, saved/retrieved the record, used
bundled knowledge/embeddings with a genuine Qwen answer, and served report/CSV.
The final archive has the same runtime/frontend/model assets, plus final reports
and release utilities.

Other authoritative results:
- `results/acceptance.json`: six original predictions, source retrieval, genuine
  generation, follow-up persistence, batch filtering, reports, alerts and failures.
- `results/evidence_scope_verification.json`: real current-method explanation and
  genuine follow-up after the final source-sentence contract.
- `results/browser_verification.json`: two real uploaded images completed,
  Good/Anomalous displays, combined history filters, alert acknowledgement, report
  images and cited answer rendered; no captured browser JavaScript errors.
- `results/startup_verification.json`: actual Windows launcher/model verification
  on Python 3.11.15 with torch 2.5.1+cu121 and transformers 4.57.6.
- `results/serving_profile.json`: one clean bounded GPU profile and CPU smoke.
- `results/preservation_verification.json`: 15 frozen model/evaluation artifacts
  match the pause-checkpoint hashes, including all weights, banks and final results.

## Frozen performance and scope

| Product | Final images | AUROC | AP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.896625 | 0.866319 | 0.779070 | 0.837500 | 0.807229 |
| Capsules | 140 | 0.825000 | 0.888730 | 0.838235 | 0.712500 | 0.770270 |
| Cashew | 130 | 0.970500 | 0.983017 | 1.000000 | 0.700000 | 0.823529 |

64 normal fit images/category; 32 distinct normal + 20 reassigned official test
anomalies calibrate max-F1 thresholds; remaining official test identities are
held out. This is a modified VisA protocol, not the full official benchmark.
Â±5% review band is heuristic, not calibrated confidence. Capsule localization
remains weak (pixel AP ~0.045). No named defects, counts, root causes, factory
tolerances or product-safety/acceptance guarantees are inferred.

Clean RTX 4060 model medians: **54.59 / 53.875 / 65.615 ms**; total
file/decode/inference/overlay medians about **173 / 159 / 230 ms**. PyTorch allocated
GPU peaks about **66 / 78 / 90 MB**, excluding driver, other processes and LLM.
CPU inference passed. Earlier frozen evaluation/timing records remain preserved.
The shipped method is frozen DINOv3 patch memory, **not Dinomaly**.

## Explicit remaining verification limitations

- Docker compose configuration passed; container execution unverified because the
  Docker daemon was unavailable.
- Responsive CSS is implemented, but mobile visual QA is unverified: the browser
  ignored the requested 390 px override and stayed at 1280 px, including in a new
  tab. The override was reset after testing.
- Python 3.11 verification reused the existing Conda runtime plus an isolated
  compatibility overlay. A clean dependency installation in a new venv was not run.
- Anomalib decoder training, browser ONNX/WebGPU export, Supabase, n8n and public
  deployment remain optional/future work; none was executed or provisioned.
- Quote/ID validation establishes traceability, not guaranteed semantic entailment.

These limitations are documented in the README and verification report. Do not
restart successful experiments to remove a documentation caveat.

## Start / continue without rebuilding

For ordinary standalone use, read README and run `Start-DefectRAG.cmd -Setup`
once in a compatible Python environment, then `Start-DefectRAG.cmd`.
The dashboard build, weights and knowledge index are already bundled.
Qwen is optional and separately installed through Ollama; no automatic LLM download.

Existing verified development runtime (unchanged):
`C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe`,
with `PYTHONPATH` set to the workspace sibling `.test-deps`.
Python 3.11 runtime:
`C:\Users\User\anaconda3\envs\defectrag\python.exe`,
with `PYTHONPATH` set to sibling `.test-deps311` and `USE_TF=0`.
Do not reinstall those completed overlays or change the original environments.

A development preview may still run at `http://127.0.0.1:8766`.
Its last startup reported PID **32284**; verify identity before stopping it.
Shared Ollama is at localhost:11434, `qwen2.5:3b`.
No fitting/training/benchmark jobs remain active.

If final packaging was interrupted:
1. Inspect Git status and the existing ZIP/receipt. Preserve any newer edits.
2. If the final ZIP does not exist, run `python -m scripts.package_release`.
   It refuses to overwrite an existing archive.
3. With source committed and the release bundle present, run
   `python -m scripts.sync_release` with Desktop write permission.
   It requires a clean Desktop tree and fast-forwards Git without rewriting history.
4. Check the generated receipts. Do not repeat the completed model evaluation.

The code-only release recovery bundle is
`development-support/git/DefectRAG-v2-release.bundle`.
Prior Git commits, code bundles and timestamped checkpoint ZIPs remain preserved.
Historical progress is under `docs/PAUSE_CHECKPOINT_20261016.md` (excluded from the
clean release archive).

## Preservation

The original `DefectRAG-Verified` source, Git history and installed dependencies
were not changed. Existing VisA data at
`C:\Users\User\Downloads\VisA_20220922` was read only.
All original model banks, weights, checkpoints and evaluation records remain.
The new app's development history stays in workspace `runtime/`; earlier safe
SQLite backups remain under `development-support/saved-runtime/`.
Never replace a newer database with an older backup. No public deployment,
paid service, cloud resource or external notification was initiated.
