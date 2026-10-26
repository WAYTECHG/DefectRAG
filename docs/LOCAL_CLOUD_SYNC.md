# Private synchronization between the local app and Hugging Face

## Live activation checkpoint — 23 October 2026

The user manually applied `supabase_personal_sync.sql`. Do **not** rerun it.
Read-only production catalog checks confirmed the column, private receipts,
expected RPC signature/ACLs, enabled triggers, private bucket, owner-only RLS and
restrictive native TOTP guards. Registration and mandatory MFA remain true.
Anonymous history, receipt and exact-signature RPC probes returned 401/42501.

Desktop and Work started at `73c3fc5`. Desktop's preserved public configuration
matches the live Supabase project/publishable key. Its missing local auth UI flag
was enabled by appending `window.DEFECTRAG_PUBLIC_CONFIG.authWorkflowEnabled=true`;
the original is retained privately at
`runtime/local-sync-activation-20261023/config.before.js`. No secrets were changed.
The local backend runs with `DEFECTRAG_LOCAL_SYNC=1` in its process environment.
The React development server uses the latest source without replacing working
`frontend/dist` or the showcase. **No HF deployment or HF flag change occurred.**

The user privately verified Developer MFA at both local and HF origins, and a
different approved account with MFA at the separate `localhost` origin. One real
DINOv2 Capsules sample produced QA inspection
`c82bf820f305459988c6e94494514edf`, batch `QA-SYNC-20261023`, score
0.20568740367889404, threshold 0.1439922600984573, inference 973 ms.
Live evidence is in `results/local-cloud-sync-live-20261023/`:

- Local creation, private image/heatmap upload, HF display and matching saved
  measurements/conversation passed. Both HF images decoded at 640×427.
- Cloud review returned to local; independent refresh retained the saved history.
- Replayed the ORIGINAL create UUID/body/base from a backed-up QA-only queue to
  simulate lost acknowledgment. Cloud revision/receipts stayed unchanged: no
  duplicate row or conversation. No existing history was imported.
- A temporary QA-ID-restricted harness interrupted only sync RPC dispatch. The
  real local write/queue persisted across refresh, retried six times with backoff,
  and saved once after transport was restored. This was **injected transport
  failure**, not a physical internet outage. The normal backend was restored.
- A concurrent real cloud/local QA review produced an explicit conflict. Choosing
  cloud retained the unsent local edit in a downloadable recovery backup; backup
  download passed and contained no authentication tokens.
- A different approved AAL2 account could not read the private cloud row/image,
  retrieve it through the local API (404), read receipts or replay its operation
  (42501). No membership or approval changes occurred. The temporary diagnostic
  page used normal SDK authorization and was removed afterwards.
- QA alert acknowledgment, cloud archive → local recovery, and local restore →
  cloud history passed. QA finishes active, acknowledged, revision 9, four saved
  notes, two conversation entries, zero pending operations and zero conflicts.
- HF reads/images and a new QA review worked while the local backend was stopped;
  that review returned after normal backend restart. **Actual laptop power-off and
  a separate physical device were not tested.**

Team copying/publication remained explicit and were not invoked. The production
QA metadata checks showed zero Team copies. Notifications/n8n were untouched.
No migration, permission, model, deployment, or existing-record modifications
were performed by this activation; only the disposable QA record was exercised.

### Starting the verified local setup again

**Recommended single-terminal startup (stale-build fix, 23 October 2026):**

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2'
& '.\deployment\run_local.ps1'
```

Open `http://127.0.0.1:8765`. Stop an already running backend with Ctrl+C first.
The launcher checks the source/output receipt, backs up an older `frontend/dist`
under `runtime/frontend-backups/<timestamp>/dist`, rebuilds only when needed, sets
the process-only sync flag, and starts one loopback backend serving React itself.
It does not change PowerShell execution policy, secrets, Supabase or notifications.
Sign in/complete MFA for this origin separately from the development/cloud origins.
Never remove MFA checks to resolve a refresh error.

The backend refuses to serve stale/unreceipted local sync dashboards and displays
the rebuild instruction instead. `/config.js` uses current public configuration
with the required native-auth UI enabled; HTML/config are not cached. No UI
appearance changes were made. The old screenshot's `index-CCMYEeeT.js` sent bare
private requests, hence401; repeatedly retrying that bundle could not fix it.

**Optional two-terminal source-development setup.** Backend:

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2'
$env:DEFECTRAG_LOCAL_SYNC='1'
./.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --workers 1
```

Frontend, in the other terminal:

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2/frontend'
npm run dev -- --strictPort
```

Use `http://127.0.0.1:5173`, sign in with the same approved account as HF and
complete required MFA. This session is separate from HF. Do not also start a
second backend on port 8765. The opt-in environment flag must be set again after
closing the terminal. The launcher handles that flag for single-terminal startup.

### Existing-history audit and import gate

Read-only audit: legacy SQLite has **20 records: 5 active, 15 archived**. This
Developer's cloud history has **4 active, 0 archived**, including the new QA record
(three pre-existing cloud records). The five active legacy candidates have no
same-ID duplicates/conflicts or matching image hashes in this account's cloud
history. All ten JPEG artifacts exist and are within upload bounds, totaling
**1,615,152 bytes (about 1.54 MiB)**, plus row/conversation/note overhead. This is a
point-in-time comparison and must be rechecked immediately before an import.

Detailed private audit: Desktop
`runtime/local-sync-activation-20261023/import-audit-private.json`. Only aggregate
counts are saved in source results. **No import has been authorized or executed.**
The existing importer lists active legacy records; it cannot import the 15 legacy
archived records while preserving their archive state. They remain untouched in
the original local database. Never restore them merely to force an import.
An archive-preserving importer is a separate change if those records are wanted
in the cloud. ID conflicts during any future import must stop for review.

Before separately approving an import:

1. Stop the local backend and copy the entire Desktop `runtime` directory to a
   dated private backup **outside** the project/runtime directory. Preserve the
   account mirrors, SQLite files and any WAL files, artifacts and queued work.
   Do not overwrite an earlier backup or commit this backup to Git.
2. Export the intended account's existing cloud rows (including personal notes,
   conversations, audit and synchronization receipts) and download its private
   Storage objects using authorized tooling. A table CSV alone does not back up
   images/heatmaps. Keep the export private and check row/file counts.
3. Re-run the read-only duplicate/artifact audit and review the five selected IDs.
4. Obtain explicit approval for those records. Import through the authenticated
   Personal UI, verify counts/metadata/hashes, and retain originals/backups. Never
   reset the cloud to a backup over other users' newer work.

### Remaining operational limits

- Sync is polling (about 15 seconds plus request/pagination/backoff time), not an
  instantaneous push service. Both local services and its dashboard must be open
  to process the local queue. Cloud-confirmed data remains in Supabase when they
  stop; pending local work does not exist in the cloud yet.
- Protected new operations fail closed if native authorization is unavailable;
  this does not provide offline authenticated editing.
- A concurrent remote archive of the currently open inspection can show a
  transient “Selected conversation / Selected review” refresh warning. Recovery
  and restoration worked; a focused stale-selection UI improvement remains.
- The result's “Storage: local device” caption describes its local cache. Use the
  synchronization status/queue for cloud-confirmation state, not that caption.
- Actual internet disconnection, physical laptop power-off and additional-device
  testing remain manual checks. Pending/revoked/AAL1 regressions previously passed
  local tests; this activation did not change accounts to rerun them live.

## Original implementation and activation reference

Implementation checkpoint starts at `4390e82`. This feature is **inactive** until
the reviewed additive SQL is manually applied and the local feature flag is enabled.
No production migration, activation or deployment was performed during development.

## What connects the applications

The local app runs its existing visual model and RAG on the laptop. An approved
account's new results are saved immediately to an account-specific SQLite database
and a durable operation queue in the same transaction. The dashboard's existing
15-second refresh uploads pending operations and downloads private cloud results
from **the same Supabase personal workspace used by Hugging Face**. There is no
dependency on a running Hugging Face GPU for synchronization itself.

Cloud-created records, JPEGs, heatmaps, conversations, personal review notes,
alert acknowledgments, archives and restores are mirrored. Model scores, model
identities and thresholds are preserved; synchronization never reruns inference.
Team sharing remains explicit. No automatic team copy, gallery publication,
notification dispatch, invitation or account approval occurs.

The local dashboard must be open, signed in with current required MFA, and online
for synchronization. Opening it again resumes queued work and the cloud scan.
JWTs are not written into the queue or SQLite. New protected account operations
require fresh native authorization; this does **not** grant offline staff access.
The original unassigned local workspace remains usable separately. Its old history
is never assigned to whichever account happens to sign in.

## Storage and account boundaries

- Original history remains at `runtime/inspection.sqlite3` and `runtime/artifacts/`.
- Each account uses `runtime/local-sync/accounts/<verified-user-uuid>/inspection.sqlite3`
  with its own `artifacts/` directory. The server obtains the UUID from Supabase,
  never from a browser-provided owner field.
- Native Supabase `defectrag_auth_status`, staff allowlist, required MFA, personal
  RLS and private Storage policies are reused. No service-role key is needed.
- Every protected local request checks account authorization. Account changes,
  pending/revoked membership, missing MFA and verification outages fail closed;
  they do not fall back to another account or unassigned history.
- Signed artifact URLs reuse the existing scoped capabilities. The backing JWT
  stays in process memory and is checked again before serving protected content.
- The adapter rejects non-loopback clients and untrusted browser origins. Run one
  server worker on `127.0.0.1`; do not expose this private mirror through a tunnel.
- Local caches and explicit recovery downloads contain private plaintext data.
  They need the laptop's normal OS/disk protection. Revocation prevents new app
  access and synchronization; it cannot recall files already downloaded/exported.

## Retries, conflicts and recovery

Operations have stable UUIDs. Server receipts store owner, operation hash and
applied revision, so a lost response can be retried without duplicating a message
or inspection. Reusing an operation UUID with different contents is rejected.
Retries use persisted backoff, capped at 15 minutes, while the dashboard is open.
Only the first due operation for each inspection is eligible, so failures do not
starve unrelated records. Each cycle processes at most five operations/rows and
checks a time budget between requests; an in-flight HTTP call can outlast it.

The migration adds a revision counter. Existing cloud updates and personal note
inserts advance it, so cloud edits are detected without changing existing callers.
Conflicts retain both copies. The existing styled note exposes a review action:

- **Use cloud version** retains a recovery snapshot, then replaces the active local
  view with the owner's current cloud record. No cloud record is overwritten.
- **Retry local changes** explicitly rebases queued operations on the current
  cloud revision. An immutable inspection ID collision cannot be rebased.
- **Download recovery backup** exports the retained local conflict snapshot.

Archives are retained tombstones, not hard deletes. Cloud archives cannot be
silently resurrected by stale local edits. Direct administrator SQL deletions are
outside this protocol; use the application's archive/recovery actions instead.
Pull scans are paginated by immutable ID and resume across cycles. Changes behind
the current cursor are caught on the next full scan. Large histories take multiple
cycles; the UI marks incomplete scans instead of claiming instant synchronization.

## Existing local history

After signing in locally with MFA, choose **Import existing local history**. Select
up to ten of the latest 500 local-only inspections, then **Confirm private import**.
This is explicit consent to copy those records into that account. Original local
files remain unchanged. Repeating an import does not duplicate an inspection.
Conversations are preserved; old review decisions become clearly marked imported
notes with unverified original identity, rather than newly authenticated reviews.
Each record imports transactionally. In a multi-record import, earlier completed
records remain imported if a later item fails; retry skips already imported IDs.

## Review and safe activation

1. Back up the Supabase project using its available backup/export procedure and
   copy the local runtime folder privately. Do not commit runtime or credentials.
2. Review `deployment/personal_sync_preflight.sql` and run its **single SELECT**.
   Personal tables/guard/action/archive/private bucket must exist, mandatory MFA
   should still be true, and the three new sync objects should be absent. If only
   some exist, stop and inspect rather than partially rerunning SQL.
3. Review `deployment/supabase_personal_sync.sql`. With separate approval, execute
   it manually once. It adds `sync_version`, an owner/ID scan index, a private
   receipt table, version triggers and one owner/MFA-checked RPC. It does not
   delete inspection data or change staff permissions, gallery or notifications.
4. Confirm the new objects/ACLs and run the two-account live tests below before
   treating synchronization as production verified. No HF environment flag is
   required: existing cloud writes automatically advance the installed revision.
5. Preserve the Desktop `frontend/public/config.js` with the same Supabase URL,
   publishable key and `authWorkflowEnabled=true`. Never copy privileged keys.
6. Build the updated **local** React app without replacing the static showcase:

   ```powershell
   Set-Location 'C:/Users/User/Desktop/DefectRAG-v2'
   npm --prefix frontend run build
   $env:DEFECTRAG_LOCAL_SYNC='1'
   ./.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --workers 1
   ```

   Open `http://127.0.0.1:8765`, sign in with the existing approved account and
   complete MFA. Authentication is separate from the HF browser origin.
7. Verify a controlled local inspection, cloud appearance, cloud-created record
   download, conversation/review changes, archive/restore, disconnected retry,
   concurrent conflict, account switching, AAL1 and revoked/pending denial.
   Do not approve test accounts or expose private data to the team for this test.
8. The email-link cache fix (entry HTML/config `Cache-Control: no-store`) is code
   prepared for a separately approved HF deployment. The user reported the old
   warning disappears after Ctrl+Shift+R and Developer MFA. A new cache-control
   deployment has **not** been performed or verified live.

## Pause / rollback

Stop the local server, unset `DEFECTRAG_LOCAL_SYNC`, and restart normally. The
original local history is still present. Keep the new private account folders and
queued changes for recovery; do not merge them into unassigned history. The
additive SQL may remain in place: existing cloud APIs are compatible. Do not drop
the revision/receipt schema as an automatic rollback, because that discards replay
protection. No production secrets or authentication settings need to change.

## Verification scope

Automated tests use software inference fixtures and an injected cloud adapter;
they do not provide new model-performance evidence. Real PostgreSQL17 contracts
execute the existing personal workspace SQL plus this additive migration inside a
disposable container without networking, mounts or production credentials. Native
Supabase Auth/Storage, actual desktop-to-cloud end-to-end operation and cache
headers on the public Space remain activation gates, not claimed completed tests.

Automatic Developer notifications are a separate milestone: one controlled Resend
email was delivered, but the recurring job/delivery remain disabled pending the
previously documented Vault/configuration and activation approvals.
