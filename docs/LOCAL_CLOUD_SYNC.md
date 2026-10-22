# Private synchronization between the local app and Hugging Face

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
