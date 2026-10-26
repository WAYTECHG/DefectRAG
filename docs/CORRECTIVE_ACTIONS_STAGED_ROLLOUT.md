# Corrective Actions staged rollout — 24 October 2026

CURRENT: Owner confirmed manually approving additional Staff B, reconciling the
one approval/membership exception. Native Stage2 passed within documented scope;
production corrective-action automation remains FALSE. Stage3 hands-on local n8n
begins with owner creating a separate blank workflow. Existing published workflow
stays untouched; no import, execution, credentials or live callback tested yet.

Earlier: Native Stage2 case/lifecycle/assignment/authorization/privacy and ordinary
Team collaboration matrix PASS. Final case Closed/version9;9audit entries,
9queued events/0attempts/0effects; case automation FALSE. Original inspection/
note/Gallery counts excluding QA and existing security definitions/settings match.
One Developer approval at16:41MYT independently changed Staff3->4/pending2->1;
owner confirmation pending before full preservation sign-off. No agent account
permission action; do not undo the approval. Local n8n editor opened read-only,
existing published workflow preserved; next practical step is the separate inactive
9-node template import after reconciliation. Live callback/delivery is NOT yet
verified. See docs/N8N_LOCAL_HANDS_ON.md and live final evidence.

Earlier checkpoint: Owner manually applied the exact reviewed SQL. Production SELECT-only
installation checks and twelve preservation comparisons PASS. CASE automation
remains OFF. Native Developer AAL2 read/worker isolation and anonymous denial PASS.
Live Staff owner/supervisor/Developer lifecycle and negative checks remain in
progress. Local n8n practical teaching is Stage3 and cannot start before Stage2
passes. No React application change or production deployment was made. Do not
rerun the successful migration. Evidence: results/corrective-actions-live-20261024/.

Earlier checkpoint: Owner approval RECEIVED for the exact reviewed SQL, with automation OFF. The
219-line migration is prepared and hash-verified in a separate SQL Editor query.
OWNER manual execution is pending; the agent has not clicked Run. Approval alone
is not installation evidence. Await the owner's success/error before postflight
and native live QA tests. Proceed to hands-on local n8n only after Stage2 passes.

Latest status: private recovery rehearsal now PASSED. See
SUPABASE_PRIVATE_BACKUP.md and results/private-recovery-complete-20261024/.
Original database/role statements, critical row contents,38Storage files,
Vault root-key decryption and actual native GoTrue TOTP/AAL boundaries verified
in an isolated runtime. Bootstrap-role mismatch is fixed without grantor rewrites.
Fresh production preflight24October15:47MYT confirms supabase_admin atOID10,
no case objects installed, baseline counts/Staff/policies/RPCs/triggers/grants and
Developer email settings unchanged. The remaining Stage1 gate is explicit owner
approval for the unchanged reviewed migration, followed by owner execution.
No migration, production permission or automation activation has been performed.
Historical unsatisfied-backup statements below describe earlier checkpoints.

Continues checkpoint 6637039. This plan supersedes the earlier requirement to
choose always-on n8n hosting before any local integration work. Oracle signup is
blocked externally; no Oracle account or paid service is needed for local work.

## Stage 1: current preflight

The reviewed owner/supervisor/Developer migration is unchanged:
`deployment/supabase_corrective_actions.sql`, canonical UTF-8/LF SHA256
`DEACD409A1E1CBC568CA04CD2FB8090ABCF6D8BAAE44A97D4CA40DEAAE9F26A6`.
Earlier local SQL/security and 186-test release results remain valid; no executable
code changed and no models or completed experiments were repeated.

Fresh SELECT-only `deployment/corrective_actions_preflight.sql` was executed:

- PostgreSQL 17.11; none of the five case tables/eight case functions exist.
- Existing referenced column types/keys match; authenticated/service roles have
  public schema USAGE. No partial installation or rerun is appropriate.
- MFA and registration remain true. Developer email automation and its existing
  five-minute Cron remain enabled; no notification setting was modified.
- Counts: Team9, Team notes6, Personal10, Personal notes7, Gallery6, Staff3,
  pending applicants2. Team/private buckets remain nonpublic, with18/20 objects.
- Stored fingerprints of existing policies, critical RPC definitions/ACLs,
  noninternal triggers and Staff membership, plus existing table ACLs. These
  exclude new case objects so the same query supports a post-install comparison.

These metadata/count records are NOT a private database backup.

### Explicit Data API grants

Supabase's official 28 April announcement applies the new defaults to existing
projects on 30 October2026: NEW tables require explicit grants; existing tables
retain their grants. RLS is a separate layer. This migration already explicitly
revokes defaults and grants only the intended new access:

| New object | Explicit access |
| --- | --- |
| Cases/history | authenticated SELECT with Staff+native-AAL2 RLS |
| Event/effect tables | authenticated SELECT on named safe columns only, with RLS |
| Settings | no browser or service-role table privileges |
| Staff case RPCs/helpers | authenticated EXECUTE; approved Staff/native AAL2 checked internally |
| Claim/schedule/effect/finish RPCs | service-role EXECUTE only; bounded definer functions, no direct table grants |
| Anonymous users | no case-table column access or case-RPC EXECUTE |

UUID defaults require no sequence grants. No global default-privilege adjustment,
existing table grant, Staff role, storage policy or existing RPC change is needed.
The migration creates no custom triggers: its bounded write RPCs write immutable
history/events in the same transaction. Existing inspection/sync/audit triggers
must compare unchanged after installation. Foreign-key internal triggers are
expected PostgreSQL implementation details, not missing application triggers.

References checked24October2026:
- https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically
- https://supabase.com/docs/guides/api/securing-your-api

### Backup and approval gates — historical checks; latest result above

Latest24October: owner completed the encrypted export. Checksums/DPAPI decryption
passed, and the actual archive restored into a disposable official Supabase PG17
container with network=none and Cron off. Critical record counts match the same
archive. Exact hosted-role recovery remains unverified:21 membership grantors
needed local-only bootstrap adaptation after the original role replay failed an
ADMIN-option check. Native Auth/MFA recovery, Vault root-key custody and actual
Storage-byte backup remain pending. See SUPABASE_PRIVATE_BACKUP.md and the private
backup rehearsal evidence. This is NOT approval to migrate or a complete recovery
claim. No production password, role, data or Developer notification was changed.

Owner explicitly confirmed **No verified backup yet**. The project's Backups page
states **Free Plan does not include project backups**. No complete backup or
successful recovery is claimed. Do not upgrade the plan, reset the database
password, execute the migration or restore anything into production.

The Connect -> Direct -> Session pooler panel is prepared for the next private
backup step. Host `aws-0-ap-northeast-1.pooler.supabase.com`, port5432,
database `postgres`, user `postgres.zrzqpbcomlorfzszolrs`; TLS required.
The password is entered privately by the owner, never into chat, URLs in shell
history, source files or logs. Existing Staff passwords/API keys are not the
database password. No existing-password availability is assumed.

Update24October (supersedes the next historical paragraph): owner subsequently
remembered the existing password and reports a successful connection. Retain it;
no reset was performed. Follow SUPABASE_PRIVATE_BACKUP.md for the next private
export action; full recovery is still unverified and the migration remains gated.

Earlier24October: owner confirmed existing password unavailable after failed
candidate tests. The actual connection and source/live service dependency audit
are recorded in DATABASE_PASSWORD_ROTATION.md. No reset approved or performed.
Use that reviewed rotation procedure and privately prompted, one-attempt read-only
verification only AFTER separate owner approval; then return to the backup gate.

A recovery-ready backup must include applicable schemas/data, roles/grants/RLS,
Auth users/MFA records and user customizations to managed schemas. Preserve
project encryption/recovery requirements using the official restore procedure;
do not claim a plain PostgreSQL fixture reproduces native Supabase Auth/MFA.
Preserve Storage object bytes separately; a database dump contains metadata only.
Keep all backup bytes/credentials outside Git, protected privately. Record a
manifest, checksums and successful recovery into an ISOLATED compatible runtime.
An archive listing, metadata export or zero-error dump alone is not a restore test.
Disable outbound network/schedulers during a restore rehearsal so restored Cron
or webhook definitions cannot emit real notifications. Never restore to production.

Official backup guidance:
- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore

After backup recovery is confirmed, request explicit approval for this exact SQL.
The owner will execute it manually, as requested. Then read the consolidated
`deployment/corrective_actions_postflight.sql`, verify automation=false, compare
the old-policy/RPC/trigger/ACL/Staff fingerprints and counts, and preserve the
successful result. Stop on errors/partial objects; never rerun a successful install.

## Later stages — pending, not passed

2. Use designated real approved Staff/Developer/pending sessions and native TOTP.
   Disposable QA records only. Test case creation, owner/supervisor/Developer
   editing, unassigned read-only/self-assignment denial, transfer/revocation
   boundaries, AAL1 denial, lifecycle/deadlines and audit; regress Personal sync,
   explicit Team sharing, reviews/conversations and cross-owner privacy. SQL
   Editor impersonation is not proof of native user authorization. See the live
   matrix in CORRECTIVE_ACTIONS_ACTIVATION.md. No existing account revocation.
3. ONLY after Stage2 passes, teach local n8n one practical action at a time: reuse
   existing Docker volumes/workflows; user imports/configures new inactive workflow
   and performs each step. Verify inputs/outputs, JSON/expressions, IF branches,
   header auth, callback HTTP nodes, notification sink, errors, retries, duplicate
   and ambiguity handling, deadlines/escalations, export and backup. Do not
   silently configure everything for the user or activate old Staff mail workflows.
4. Controlled QA walkthrough: inspection -> explicit Team share -> human review/
   separate defect confirmation -> case assignment -> authorized event -> local
   execution -> QA notification/task -> audited resolve/close. Distinguish actual
   Supabase events from simulated fixture events; real sends require separate
   authorization. Unattended production n8n delivery remains off.
5. AFTER local verification, export the tested workflows and prepare a reviewed
   Ubuntu ARM64-compatible Compose package with persistent state/key custody,
   backup/recovery, HTTPS, fixed webhook auth and rollback. No Oracle access,
   purchase, public editor, Trello or production automation activation.

Connectivity constraint: Supabase Edge cannot call a Windows localhost webhook.
A local integration must use a deliberately authenticated private/local bridge
and outbound access, or an approved manual dispatch design. Do not invent a public
tunnel as a shortcut. n8n must not receive a Supabase service-role key. Any bridge
credentials stay server-side and any live dispatcher needs scoped QA selection;
it must not consume unrelated queued events. This local path is not yet verified.
