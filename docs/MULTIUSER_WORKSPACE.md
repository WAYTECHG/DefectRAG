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
