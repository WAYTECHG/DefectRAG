# Authentication deployment-readiness assessment

Audit date: 20 October 2026 (Asia/Kuala_Lumpur). Application baseline: `fa5e499`,
branch `feature/auth-mfa-inactive`. This assessment changes documentation and adds
a read-only catalog checklist only. Application code and migration remain unchanged.
No tests were rerun; no services, models, deployments, SQL, mail or settings were activated.

## Verdict

**Ready for a controlled schema/integration review; not cleared for mandatory MFA
or notification activation.** The source schema and authorization design match the
recorded project, but no live catalog or native MFA integration was inspected.
The notification worker also needs a bounded runtime before enabling its schedule.
Local passes do not substitute for live Supabase RLS, Auth, Storage or n8n tests.

## Findings and release gates

| Finding | Evidence | Required before activation |
| --- | --- | --- |
| Live schema compatibility is conditional | Migration references existing private tables/functions and `auth.mfa_factors`; no live catalog snapshot was available in this audit. Earlier user execution confirmations establish history, not absence of subsequent drift. | Review the read-only preflight against the actual project, then validate migration on an authorized isolated matching environment. Do not claim an execution pass yet. |
| Worker can exceed free runtime | `worker.mjs:22` permits 15 s per database call, line 25 claims 5 events, lines 28–47 sequentially permit 20 s webhook + 15 s completion per event. Nominal timeout envelope is 15 + 5 × (20 + 15) = 190 s, before overhead. Hosted free Edge duration/request idle limit is 150 s. | Before notification activation, reduce claim size (e.g. 2) and impose an invocation budget with margin (e.g. 100–120 s), preserving leases/retries. Add targeted slow-response/lease tests and verify on the actual Edge runtime. This audit does not modify the worker. |
| Developer lockout safety is conditional | SQL defaults MFA off, own status is AAL1-readable, and configure refuses mandatory MFA without an active developer's verified TOTP. It does not prove that the current developer can complete a fresh real login/challenge or has a recoverable device. | Prove fresh developer AAL2 in a second browser session and independent administrator recovery before mandatory enforcement. Do not rely only on an existing session or a stored factor row. |
| Release directory can contain the old dashboard | Verification builds are in `runtime/auth-build/cloud`; `publish.py:33` and subsequent frontend traversal publish `development-support/space/ui-dist` instead. Successful isolated builds do not update that release directory. | Assemble an approved cloud build at the publisher's actual input path, preserving existing public config. Verify index-referenced assets and the two public flags. Do not run the publisher during this assessment. |
| Automation is prepared, not provisioned | Edge wrapper, handler, inactive n8n JSON and config exist. No scheduler is installed, n8n version/host and SMTP are unconfirmed. | Confirm hosting, reachable HTTPS webhook, credentials, node compatibility and mail-sink receipt before production notifications. |

Runtime source: [Supabase Edge limits](https://supabase.com/docs/guides/functions/limits).
Timeout recovery retains outbox rows, but mail accepted before an interrupted
acknowledgment can be delivered again. This affects notification reliability, not
approval authority. No precisely-once SMTP delivery guarantee is possible here.

## Migration compatibility review

The review compared `deployment/supabase_auth_mfa.sql` with:
`deployment/supabase.sql`, `deployment/supabase_additive_conversations.sql`,
`deployment/supabase_personal_workspace.sql` and `deployment/supabase_public_gallery.sql`.

| Existing component | Source-level compatibility | Remaining live check |
| --- | --- | --- |
| `staff_members` | Retains user ID, name and staff/developer role; adds nullable revocation columns, leaving existing members active. No backfill into pending state. | Column types, constraints, helper ownership/grants; no conflicting auth objects/columns already installed. |
| Team inspections/notes/audit | Existing data, policies and RPC signatures retained. Restrictive guards intersect existing permissions. Replaced membership helpers preserve their names, argument lists and boolean return types. | Confirm no additional public/anon policy or alternate privileged RPC bypasses the intended checks. |
| Personal workspace | Existing owner restrictions are retained; new guards add active membership/MFA. There is no developer exception granting access to another owner's private records. | Direct cross-owner REST/RPC/Storage denial with real staff accounts. |
| Private Storage | Restrictive policy targets only `team-inspections` and `personal-inspections`; existing bucket/owner policies remain necessary. Application switches to authenticated reads when enabled. | Both buckets must still be private; inspect all applicable policies and direct downloads. |
| Community Gallery | No Gallery tables, RPCs, grants, public snapshots or records are changed. Private-source publication uses the new authenticated-byte path; owner/size checks remain. | Public reads, guest consent/withdrawal, authenticated owner publication and authorized moderation after rollout. |
| Native Auth | Uses `auth.users` verification and native `auth.mfa_factors` status/type; no custom OTP generator or new auth provider. | Hosted Auth schema fields/enums, TOTP availability, actual SDK session upgrade and factor removal behavior. |

New SQL adds four tables (settings, requests, access audit, outbox), authorization/
status/decision/worker functions and restrictive policies. It **replaces two
authorization helper bodies**; “additive” does not mean permission semantics never
change. MFA is off by default and existing nullable revocations are inactive.
The migration is intentionally one-shot, not blindly rerunnable: existing new
objects/columns/policy names must be reconciled, not skipped with IF NOT EXISTS.
Its transaction should abort on an error; verify full success and schema-cache
visibility rather than running fragments or rerunning old setup SQL.

Exact reviewed migration LF SHA256:
`cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983`.

`deployment/supabase_auth_preflight.sql` was prepared but **not executed**. It
selects catalog/column/policy/grant/bucket metadata, checks required signatures and
detects collisions inside a read-only transaction. It does not select accounts,
MFA seeds or inspection rows. Review output privately. Passing the catalog review
still does not prove PL/pgSQL execution, RLS behavior or native Auth integration.

## Authorization and revocation

- `defectrag_request_access` derives subject identity from verified `auth.uid()`/
  `auth.users`, requires DB registration enabled and creates pending status only.
  There is no client role input or staff insert in registration.
- `defectrag_decide_access` requires active developer membership and AAL2/current
  verified TOTP, serializes decisions, checks expected version, denies self-actions,
  and grants only staff. Request state, membership, audit and outbox commit together.
- `defectrag_is_staff` requires an unrevoked membership and, when mandatory MFA is
  enabled, AAL2 plus a currently verified TOTP factor. `defectrag_is_developer` adds
  the developer role. Restrictive RLS/Storage guards and existing RPC helper checks
  cover direct access; hiding frontend pages is not the enforcement mechanism.
- The check verifies AAL2 and existence of a verified TOTP, not a particular factor
  ID or recent challenge timestamp. If other second factors are enabled, this is
  not a policy requiring that every AAL2 token was specifically obtained via TOTP.
- `StaffRepository.__init__` uses the presented user JWT for a fresh Supabase status
  RPC in the enabled mode, without the legacy 45-second membership cache. Gradio
  inspection validates the repository before GPU work; assistant, private images,
  history, report/export and Gallery protected operations resolve the same boundary.
- Revocation does not revoke the person's entire Supabase identity. It denies new
  protected DefectRAG operations even while a JWT is otherwise valid. Own access
  status and public functions remain available by design. In-flight work may
  finish or fail at its next authorized access; this is not GPU-job cancellation.
- App-issued old private signed links can persist 10 minutes (backend) or 15 minutes
  (Staff page). RLS cannot revoke previously issued signed URLs or downloaded copies.
  Authorized clients can also mint Storage signed URLs directly; the app switching
  to authenticated delivery does not remove that capability from Supabase itself.
- Rejected/revoked users cannot auto-reapply to restore membership. Administrative
  reconsideration/reinstatement remains a separate policy, not an implemented UI action.

These guards match the native AAL/RLS approach described in
[Supabase MFA documentation](https://supabase.com/docs/guides/auth/auth-mfa).
Application code, SQL checks and existing local tests support this design review;
they do not justify claiming a live security certification.

## Exact automation inventory and configuration

| File / endpoint | Role |
| --- | --- |
| `deployment/n8n/staff-notifications.json` | Import inactive. Webhook v2 → Code v2 validation → Email Send v2.1 → Code v2 SMTP acceptance → Respond to Webhook v1.4. Credential IDs and sender are placeholders. |
| `POST https://<n8n-host>/webhook/defectrag-staff-notifications` | Typical production webhook URL; use the actual Production URL shown by n8n, including any configured base path. Native Header Auth: `X-DefectRAG-Webhook-Key`. Never use the test URL or immediate-start acknowledgment. |
| `deployment/supabase/functions/staff-notifications/index.ts` | Deno Edge entry point. |
| `deployment/supabase/functions/staff-notifications/worker.mjs` | Purpose-secret authentication, bounded individual calls, leased claim/finish RPCs, payload allowlist and receipt validation. Overall runtime correction remains required. |
| `deployment/supabase/config.toml` | `verify_jwt=false` for this worker only; its independent dedicated bearer-secret check is mandatory. This is not the config for user-facing functions. |
| `POST https://<project-ref>.supabase.co/functions/v1/staff-notifications` | Scheduler invokes with `Authorization: Bearer <dedicated worker secret>`. No browser invocation or privileged key in n8n. |
| Supabase Cron/pg_net + Vault | Planned scheduler; not installed/provisioned. CLI project root must resolve `deployment/supabase`, rather than assuming a root-level `supabase` folder. |

Webhook response must be JSON `{event_id: <same event ID>, delivered: true}` after
SMTP accepts the intended recipient. n8n's immediate response only means the
workflow started. Its current Email Send source returns Nodemailer result metadata;
the actual installed version and provider still need a test. See
[n8n webhook response modes](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
and [Email Send implementation](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/EmailSend/v2/send.operation.ts).

| Location | Exact settings | Status / requirement |
| --- | --- | --- |
| Existing public dashboard config | `supabaseUrl`, `supabasePublishableKey`, `authWorkflowEnabled`, `registrationEnabled` | Preserve existing URL/public key. Both new flags missing/false until authorized. Public flags are not security controls. |
| HF backend | `DEFECTRAG_AUTH_WORKFLOW` | Missing/0 now; later 1 after reviewed migration and compatible deployment. Preserve existing `DEFECTRAG_STAFF_BACKEND`, `DEFECTRAG_PERSONAL_WORKSPACE`, `DEFECTRAG_GALLERY_ENABLED`, live RAG and existing secrets. |
| Database | `defectrag_auth_settings.registration_enabled`, `.mfa_required` | Both false after migration; owner-only configure function controls later activation. |
| Edge runtime | `DEFECTRAG_NOTIFICATIONS_ENABLED` | Missing/0 until runtime correction, configuration and explicit real-notification permission. |
| Edge secret | `DEFECTRAG_NOTIFICATION_WORKER_SECRET` | Separate random secret, minimum 32 characters; also stored securely for the trusted scheduler. |
| Edge secret | `DEFECTRAG_N8N_WEBHOOK_URL` | Actual reachable HTTPS production webhook. |
| Edge/n8n server credential | `DEFECTRAG_N8N_WEBHOOK_SECRET` | Separate random secret, minimum 32 characters; n8n native Header Auth value. |
| Edge built-ins | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Trusted Edge environment only. Verify the provided service-role credential is accepted by this project's REST API; arbitrary publishable/secret keys are not interchangeable with a JWT bearer. Do not manually create reserved `SUPABASE_` secrets. |
| n8n | Native SMTP credential, verified From sender, host/port/TLS | Configure placeholder credential references and sender, without adding team data or privileged DB keys to n8n. |
| Supabase Auth | Native TOTP, custom SMTP, Site URL/redirect allowlist, signup/abuse controls | Dashboard configuration not inspected or changed. External confirmations/invites/reset mail need suitable SMTP. |

Supabase's default Auth SMTP restricts recipients to organization-team addresses
and is currently limited to two messages/hour. That organization list is different
from the DefectRAG staff allowlist. See [SMTP requirements](https://supabase.com/docs/guides/auth/auth-smtp).

Laptop off/local n8n offline: cloud approval and login remain independent; events
wait/retry in Supabase and dead-letter after eight attempts. A developer can retry
after n8n returns. Always-on delivery requires an independently reachable approved
n8n host. No host, paid resource, schedule or working mail service is assumed.

## Implemented versus integration-tested

| Capability | Implementation at fa5e499 | Verification status |
| --- | --- | --- |
| Registration/request/developer decisions | Inactive frontend + SQL | Local adapters/guards tested; real native signup, approval and direct SQL/RLS tests pending. |
| TOTP enrollment/challenge/verification | Native SDK calls and SQL/backend checks | Mocked/local tests passed; existing developer's real factor/session/recovery unverified. |
| Revocation/private storage | Soft revoke, fresh posture, authenticated reads | Software tests passed; real existing-token cross-role/Storage/report tests pending. |
| Notifications | Outbox/leases/retries + worker + inactive n8n template | Fake delivery tests passed. Runtime budget fix, Edge deploy, n8n import/SMTP and failure tests pending. |
| Public Recruiter Demo | Existing anonymous isolated browser workspace, samples, real queued inspection and text evidence assistant; separate static showcase | Previously live-tested baseline and local privacy regression evidence. Not retested live in this audit. No staff registration/MFA needed; HF GPU login/quota/capacity can still limit inference. |
| Dedicated recruiter tour/demo switch | No separate guided-tour or demo-toggle feature found | Optional separate UI milestone. Existing guest functionality already provides public demo use. |
| Multimodal RAG | **Not implemented at this checkpoint** | Separate development milestone, not a feature to advertise as complete. |

Guest isolation is per browser workspace capability, not per physical human sharing
one browser profile. Public Gallery intentionally exposes consented redacted
snapshots. Neither feature grants access to private staff or personal tables.

Actual current RAG is **vision-assisted, text-based RAG**: `backend/rag.py:36`
loads text documents, `KnowledgeIndex.search` at line 92 uses BGE text vectors and
NumPy similarity, `retrieve` at line 210 queries text, and `generate` at line 234
formats textual inspection fields/passages. LangChain and LangGraph are used.
`deployment/space/generation.py:56` selects text-only Qwen3-4B-Instruct-2507 using
`AutoModelForCausalLM`; `generate_text` supplies token IDs, not image pixels or
visual embeddings. DINO reference-bank comparisons are detection, not historical
image retrieval. No joint image/text index or visual-example RAG was found.

Historical local evidence remains 123 distinct Python tests, 49 frontend tests and
three successful builds with unchanged CSS; see `results/auth-mfa-milestone.json`.
These reports were inspected, not rerun. No scientific model experiments are needed
to assess this authentication release.

## Deployment, activation and acceptance checklist

Every state-changing step below requires separate approval. This document performs none.

1. **Freeze and inventory:** preserve fa5e499 and current HF commit/config; obtain a
   database backup/recovery plan and independently working Supabase owner access.
   Record existing private/Gallery counts without exporting confidential content.
2. **Schema preflight:** manually review the read-only catalog script, native Auth
   configuration, grants/owners and collisions. Stop on missing/drifted objects.
   Validate SQL/permissions in an authorized isolated matching environment before
   the existing project; no such execution has occurred yet.
3. **Notification runtime gate:** before activating automation, approve a focused
   worker runtime correction and targeted slow-response/lease tests. This gate can
   remain separate while staff integration is staged with notifications disabled.
4. **Migration:** after approval, manually execute only the exact reviewed new auth
   migration, once. Verify atomic success, new RPC visibility and both switches
   false. Do not re-run earlier Team/Personal/Gallery migrations.
5. **Release assembly/deployment:** after approval, build into the actual cloud
   publisher input with preserved existing public configuration. Verify all referenced
   assets and unchanged CSS. Include modified `backend/gallery.py` and cloud Python
   modules. Edge/n8n deploy separately; the HF publisher does not deploy them or SQL.
   Deploy compatible HF code with backend `DEFECTRAG_AUTH_WORKFLOW=1` and frontend
   `authWorkflowEnabled:true`; keep registration, DB MFA and notifications off.
6. **Existing-feature acceptance:** verify anonymous demo/cross-browser isolation,
   Staff/Personal history, review/alerts/recovery, explicit Team sharing, reports,
   Gallery read/publication/withdrawal/moderation and one approved inspection/RAG
   smoke test only if needed. Preserve prior records and measured results.
7. **Developer bootstrap:** existing developer performs native enrollment and real
   verification. Test a fresh password + TOTP sign-in in a second browser, failed
   code and unfinished enrollment handling. Confirm protected developer access at
   AAL2 and independent admin recovery. No sole-device/single-session assumption.
8. **Mandatory MFA:** after separate approval, owner enables mandatory MFA while
   registration stays off. Test real AAL1 denial and AAL2 allow across direct REST,
   existing RPCs, Storage, Gradio inspection/assistant, images/reports/export and
   moderation. Test factor removal/stale tokens and restore the approved test setup.
9. **External signup and approval:** after SMTP/mail permission, enable approved
   signup/redirect/rate-limit settings, DB registration and public registration flag.
   With dedicated approved test accounts: confirmation → pending denial even at
   AAL2 → developer decision → staff allow. Test regular-staff approval denial,
   duplicate/concurrent decisions and reject/revoke, without touching real staff.
10. **Notifications:** after runtime gate and permission, deploy Edge from the correct
    project root, configure private credentials/Vault, import/configure n8n inactive,
    validate with a mail sink, then separately activate workflow/worker/scheduler.
    Test unauthorized invocation, wrong header, real receipts, outage, retries,
    lease expiry and dead-letter UI retry. Document at-least-once duplicates.
11. **Revocation/recovery acceptance:** revoke only a dedicated approved test account
    with an existing AAL2 token, prove new protected operations denied and own/public
    status retained. Check app-issued old signed links until expiry, simultaneous
    owner isolation and archive/recovery. Never delete actual records for a test.
12. **Release sign-off:** label each pass by source/local/live, record actual code,
    migration hash, environment/version and unresolved limitations. Keep mandatory
    rollout and notification activation blocked if any relevant gate fails.

## Rollback checklist

1. Record the failing step; stop new registration and notification scheduling under
   explicit authorization. Preserve outbox, audit, staff and inspection records.
2. If MFA lockout occurs, use independently verified Supabase owner access. An
   authorized emergency call to `defectrag_configure_auth(false,false)` disables
   registration/MFA enforcement without dropping records or clearing revocations.
   This is a deliberate security downgrade requiring approval, not an app bypass.
3. For a lost authenticator, the administrator resets the affected native factor
   through supported Supabase admin tools after identity verification; re-enroll
   and prove fresh login before restoring enforcement. Password reset alone is not
   the recovery procedure. No custom backup-code service exists.
4. Prefer leaving compatible code deployed with DB switches off over blindly
   rolling back to pre-MFA code. Disabling only frontend/backend flags while DB MFA
   remains required hides setup and can restore stale preflight behavior.
5. If an older HF release must be restored, first approve/reconcile database auth
   state and its implications, preserve public config and report commit IDs. Never
   run old setup SQL to overwrite the new authorization helpers.
6. Leave the new schema/audit/outbox intact. No DROP/DELETE or old database restore
   is needed for a normal feature rollback. Reinstating a deliberately revoked user
   is a separate audited administrative decision; changing MFA flags does not do it.
7. Recheck existing workspaces, public Demo/Gallery and privacy boundaries, then
   record rollback evidence and keep affected features disabled until resolved.
