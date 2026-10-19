# Personal, team and public workspace upgrade

## Findings at checkpoint 99bfb72

The existing signed-in backend uses `StaffRepository`, which writes directly to
`shared_inspections` and the staff-readable `team-inspections` bucket. All approved
staff can see active records. Thus cloud persistence exists, but private personal
cloud history does not. Guest history is isolated server-side SQLite, keyed by a
random browser workspace secret; IndexedDB retains pending batch files locally.
Guest history is temporary on the Space and is not a cloud account history.

Dashboard queries poll every 15 seconds, while Staff workspace uses independent
browser Supabase queries. Selection races, absent reconnect handling, the fixed
1000-row statistics limit and unclear scope labels need improvement. Existing
SQL files define allowlisted staff, developer recovery and private team storage.
Their exact live catalog definitions are not available through the public API;
prior actual anonymous/invalid-token denials were verified. Do not confuse source
inspection with verification of every live policy.

The public gallery is already active, separately protected and verified. Its
tables, dedicated capability and existing published items must stay unchanged.

## Proposed behavior

| Workspace | Persistence and visibility |
| --- | --- |
| Guest | Existing isolated temporary browser workspace; no automatic sharing/import |
| Personal | New owner-only Supabase tables and private bucket; approved accounts only |
| Team | Existing shared tables/bucket; explicit share; approved colleagues only |
| Community gallery | Existing opt-in public snapshots; separate counts and permissions |

New authenticated inspections default to Personal. Team mode is for collaboration
on explicitly shared records; it cannot silently turn a new upload into a shared
inspection. Team and personal conversations/reviews become separate after sharing.
Optional conversation inclusion defaults off. Private review notes are not copied.
Existing team records remain team records and are not automatically copied into
personal histories. Database administrators retain normal project access, but the
application developer role does not bypass owner-only personal RLS.

## Migration review

Review [supabase_personal_workspace.sql](../deployment/supabase_personal_workspace.sql).
Run manually once, only after approval. A repeated run fails safely inside the
transaction because this is a versioned migration, not a reset script.

| Change | Permission/security effect |
| --- | --- |
| `personal_inspections`, `personal_notes`, `personal_audit` | RLS enabled. Approved users can read only their own rows. Direct updates/deletes denied. Notes/audit append-only. |
| `personal-inspections` bucket | Private. Approved owners can read/insert only under their own UUID prefix. Existing team/gallery buckets unchanged. |
| `defectrag_personal_action` | Requires active owner. Atomic conversation append or idempotent alert acknowledgement with actor/time/audit. |
| `defectrag_personal_archive` | Owner-only archive/restore; records/files retained. No access to another user's private history, including for app developers. |
| `defectrag_share_personal` | Approved active owner only. Verifies already-uploaded team artifact paths; snapshots original measurements and optionally conversation. Duplicate share does not overwrite or increase counts. |
| `defectrag_workspace_stats` | RLS-aware full-scope aggregation, with separate personal/team totals. Never includes public-gallery data. |
| Insert audit triggers | Append future create/share/review actions. Do not change existing records or fabricate historical actors. |
| Existing `defectrag_acknowledge_review` | Same signature/staff boundary; now records actor/time and one audit event per acknowledgement. Historical acknowledgements remain as originally saved. |

Security-definer functions have a fixed empty search path, qualified relations,
explicit membership/ownership checks and bounded inputs. Execution is revoked
from PUBLIC/anon. Only the listed non-trigger RPCs are callable by authenticated
users, and they still validate staff membership. No service-role key is used.

**The new feature must remain disabled until the reviewed migration succeeds.**
The activation variable will be `DEFECTRAG_PERSONAL_WORKSPACE=1` in HF Settings.
It must be enabled only after the compatible application has been deployed and
the SQL is confirmed. Existing legacy team mode remains operational meanwhile.

## Synchronization approach

Use bounded polling, immediate refresh after mutations, focus/online refresh and
cross-tab notification. Keep one authoritative query per selected workspace,
discard late responses after account/scope changes, prevent overlapping poll
requests, and show stale/offline/error state. Realtime publication setup is not
required. Counts are recomputed from database state instead of incrementing local
counts in response to events, preventing event duplication from inflating totals.

## Verification and resuming

Consult the latest DEVELOPMENT_PROGRESS.md milestone. Do not mark the upgrade
complete until migration confirmation and hosted end-to-end tests are finished.
Keep source-based policy review, mocked/software tests and actual live checks
reported separately. A second real staff/non-staff account may be unavailable;
record that coverage gap rather than claiming it passed.

## Local implementation checkpoint — 19 October 2026

Implemented the separate personal repository, workspace-bound request/artifact
authorization, explicit guest saving/team sharing, separate personal/team
statistics, owner recovery, idempotent immutable uploads and stable single-image
submission IDs. Team and personal reviews/conversations are polled while open;
private image links refresh periodically. Polling coalesces overlapping events,
refreshes on focus/reconnect and signals offline/stale data. Mutations notify
other tabs without broadcasting any token or record payload. Staff workspace
refreshes selected notes/conversations, with stale-account/selection guards.
Gallery publication state also refreshes without auto-publishing anything.

The existing stylesheet is byte-for-byte unchanged. The additions are storage
labels, a Personal/Team selector and explicit sharing/saving controls. All twelve
model profiles, evaluation results, encoder/banks and Qwen generation are unchanged.

Software validation: full backend suite **117/117**, then final focused privacy,
session and gallery suite **43/43** including two additional cases; this covers
119 distinct cases across runs, not one full 119-case run. Frontend **15/15**.
Local, cloud and static builds passed. These do not prove live RLS, account
privacy or hosted team synchronization; those remain gated by migration approval.

The reviewed migration SHA-256 is
`63e561bd234294286c6fc65b075ea130e9c021d60cf164ebf13d74a7c1f13ca1`.
No change was made to this SQL after requesting approval. The optional
[rollback-only policy checks](../deployment/supabase_personal_policy_checks.sql)
can be reviewed and executed manually AFTER that migration. They use synthetic
rows and roll back all changes, test an existing approved owner, a non-staff UUID
and anonymous role; they do not prove a second real account login. They have not
been executed against the live project by the agent.

### Next steps after approval

**Current decision:** the user explicitly said "Not approved yet; continue
independent code and tests." Keep the migration unexecuted, the feature flag
disabled and this upgrade undeployed. Continue from the saved source checkpoint;
do not repeat successful experiments or the approval request.

1. Owner manually executes the reviewed migration; confirm success here.
2. Deploy the compatible application, verify legacy team/gallery access first.
3. Enable `DEFECTRAG_PERSONAL_WORKSPACE=1` in HF Settings and restart once.
4. Verify one real personal inspection, same-account second browser, guest denial,
   explicit sharing, review/note and acknowledgement propagation, archive/restore,
   duplicate replay and failures. Use labeled QA fixtures; preserve existing data.
5. Verify public gallery publication/status/withdrawal regression. Reuse a prior
   sample where possible; do not retrain or repeat benchmark experiments.
6. Record real results and remaining multi-account coverage gaps before claiming
   production readiness. Optional policy-check SQL results supplement these checks.

Current hosted app remains on the previously verified version while approval is
pending. No activation, new SQL execution, public deployment or paid action has
been performed for this upgrade yet. Source changes and manual review files are
ready; end-to-end acceptance is unfinished.

### Operational bounds

- Dashboard aggregates query the full chosen workspace. History displays the
  latest 500, staff table the latest 200, alert lists up to 1,000 active records;
  CSV supports 10,000. No gallery rows enter these aggregates.
- New personal batch recovery uses a separate per-account browser key. Legacy
  batch checkpoints are preserved under their original keys and are not silently
  replayed into a new storage scope. A pending legacy batch needs review before
  resuming; completed experiments must not be repeated.
- Explicit guest saving imports its saved conversation up to a bounded 40 KB;
  oversized imports fail before uploading. Guest review provenance is retained
  as clearly labeled, unverified imported notes, not a newly authenticated review.
  Those notes are not automatically team-shared. Original guest records remain.
- Failed partial uploads can leave immutable orphan objects; retry reuses their
  hash paths. No automatic deletion is performed. Capacity/quotas still apply.
- Signed image URLs are bearer capabilities with bounded expiry. Revocation of
  staff membership does not recall already downloaded or cached image copies.
- Team storage/recovery policies remain the existing reviewed policies. Existing
  historical shared records do not become private through this upgrade.
- Model provenance is still not cryptographically attested; approved users can
  submit data through their authorized APIs. This task adds privacy and auditing,
  not validated factory acceptance or prediction attestation.

Supabase upload retries account for both HTTP 400 duplicate-object errors and
409 database conflicts, without swallowing permission/validation failures.
See [official standard-upload behavior](https://supabase.com/docs/guides/storage/uploads/standard-uploads).

### Independent hardening while approval is withheld

After checkpoint `6142375`, sharing controls now invalidate old completion
callbacks when their view/record changes or unmounts. Actual handler tests check
that a late success cannot reopen the previous inspection and a late failure
cannot display an error in the new context. A successful server mutation still
emits a data-free refresh event. Polling retains Offline if connectivity drops
during either a successful or failed request; it no longer reports false Synced.

Private-image team copies now stream at most 10 MiB per image, reject empty and
denied responses, and sanitize interrupted/network-transfer errors. Failed reads
do not reach the team-sharing RPC. Existing copies return without downloads or
uploads. Partial earlier uploads may remain as immutable orphan objects, as
documented above; retry uses their hashes and never deletes originals.

Focused backend tests **51/51** and frontend tests **20/20** passed. This includes
the exact 40,000-byte conversation import boundary, no truncation, oversized
rejection before upload, failed transfers, duplicate shares and context changes.
Local/cloud/showcase builds passed with the unchanged `index-Bn4HF2vD.css` asset.
The full backend suite was not rerun after these focused changes; its earlier
117-case result remains the previous checkpoint's result. The first focused
invocation used a nonexistent test filename and collected no tests; the corrected
51-case run passed. No new dependencies, GPU inference or live database writes.

The exact reviewed SQL and its SHA-256 above remain unchanged. Actual live RLS,
same-account persistence across sessions, second-account isolation and hosted
personal/team synchronization still require approved migration and later E2E
verification. Current production does not yet provide the new personal history.
