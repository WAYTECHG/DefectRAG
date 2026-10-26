# Release blockers corrected; inactive implementation

**Subsequent Step5 rollout completed:** compatible source `1dfb01e` deployed to
HF commit `b9b5fd90e38f421007912f56663db26e9208bd6d`. Current live/browser results
are in `CONTROLLED_DEPLOYMENT_20261020.md`. Account Security bootstrap is on;
registration, mandatory MFA and notification delivery remain inactive. The user
confirmed manual migration/postchecks; no SQL was executed by the agent. The
original pre-deployment evidence below is retained for audit/resume.

COMPLETED: code checkpoint `2c92849` is synchronized to the Desktop feature branch.
Both copies pass62 frontend tests, verified cloud staging/offline checks (87 files),
with identical source fingerprints and original CSS. Desktop local build also
passed. Five offline publisher/preflight and two guarded-sync tests passed.
See `results/desktop-sync-verification.json` for preserved file checks and the
complete synchronized file list. No activation, migration or deployment occurred.

Baseline: `91da4df`, branch `feature/auth-mfa-inactive`, 20 October 2026.
No database migration, MFA activation, cloud deployment, real notification,
production secret modification or GitHub push is part of this milestone.

## Notification runtime and delivery

The worker now processes at most two events per invocation, claiming **one at a
time**. It reserves 52 seconds before each claim: 15 s claim, 20 s webhook, 15 s
completion, plus overhead. There is a **100-second monotonic deadline**, leaving
50 seconds below the documented Free Edge duration/idle ceiling. Individual fetch
and response-body parsing share the timeout; stalled bodies cannot hang forever.
The deadline cannot be raised above 100 seconds through the test injection.

No next row is leased if insufficient time remains. Those events retain their
queued status/attempt count. A failed webhook is recorded through the existing
outbox completion RPC and follows its backoff. Failed/ambiguous completion stops
the invocation; the existing five-minute lease provides durable recovery. No SQL
or new outbox RPC was necessary; the reviewed migration is byte-for-byte unchanged
after LF normalization (SHA256 `cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983`).

Stable event IDs are reused on retry, sent as `X-DefectRAG-Event-ID` and
`Idempotency-Key`. Existing transactional unique keys, leased row claims and sent
state prevent normal duplicate scheduling and concurrent claims. The worker also
rejects repeated event IDs within one invocation and never immediately resends
after a lost completion acknowledgment. n8n/SMTP does **not** automatically honor
an Idempotency-Key header. A crash after SMTP acceptance before durable acknowledgment
can still duplicate an email on later recovery. Exactly-once SMTP is not claimed;
an idempotent mail provider would be needed to close that ambiguity. Permissions
and approvals never depend on notification success.

Tests cover slow/stalled bodies, deadline exhaustion, partial batches, unauthorized
requests, failed webhook codes, durable completion failures, stable retry IDs,
duplicate outbox responses and normal sent-event replay suppression. Native Deno,
actual database leases/concurrency and real n8n/SMTP remain live integration gates.

## Verified React release synchronization

`runtime/auth-build/cloud` is a verification output, while
`development-support/space/ui-dist` is the HF publisher's release input. Previously
they had no enforced connection. Now:

1. `build_ui.mjs` records `<build-directory>.build.json` after a successful build.
2. `frontend_release.mjs verify` runs the real frontend/worker suite, rechecks
   source/artifact/configuration hashes and marks that exact build verified.
3. `frontend_release.mjs stage` copies only current verified Rollup/public files
   into the publisher input, then commits its receipt last. It refuses differing
   installed public configuration; build with that configuration instead.
4. `publish.py` validates the source/test fingerprint, successful verification and
   every selected file hash before contacting HF. It uploads only the manifest
   allowlist, captures frontend bytes and rechecks immediately before publication.
5. Unverified, changed, stale-source, changed-config and tampered builds fail closed.
   Old chunks can remain on disk for recovery but are not selected for upload.
   Source fingerprints normalize text CRLF/LF for portable Desktop checkouts.

The separate Gradio client `deployment/zerogpu_phase1/client/package-lock.json`
is included in this fingerprint. Its existing exact version is 2.7.1. On this
Desktop copy the two locked client packages were initially missing; offline
`npm ci --ignore-scripts --no-audit --no-fund` installed only those two packages,
with no network request or manifest/version change. For the first Desktop cloud
build, use its preserved `frontend/public/config.js` because there is no previous
release config to preserve at the release-directory path.

The publisher has an **offline-only** `--check-frontend` option that returns before
importing/using Hugging Face APIs. Passing it is not authorization to deploy.
Manifests are local operator integrity receipts, not signed supply-chain attestations.

From the project root, for a future code change (these do not deploy):

```powershell
$env:DEFECTRAG_PUBLIC_CONFIG_FILE=Join-Path (Get-Location) 'development-support/space/ui-dist/config.js'
$env:DEFECTRAG_SPACE_BUILD_OUT=Join-Path (Get-Location) 'runtime/auth-build/cloud'
node deployment/space/build_ui.mjs
node deployment/space/frontend_release.mjs verify runtime/auth-build/cloud
node deployment/space/frontend_release.mjs stage runtime/auth-build/cloud
python -m deployment.space.publish --check-frontend
```

Preserve the installed public configuration. Never source secrets from `.env` or
copy `supabase.txt` into public configuration. Registration/MFA/notification flags
remain inactive; staging local assets does not update the live Space.

## Final read-only database preflight

`deployment/supabase_auth_preflight.sql` checks required private/Gallery tables,
columns/types, exact RPC signatures, native Auth helpers/enums, function ownership,
RLS policies, table and expanded function ACLs (including implicit PUBLIC EXECUTE),
private buckets, roles and collisions with new auth objects. It uses a read-only
transaction and metadata SELECTs only; no account/factor/inspection rows are read.
It was **not executed**. Review output privately before manually executing any
migration under separate approval. Source schemas match; live drift is unverified.
No change to `supabase_auth_mfa.sql` was required.

## Desktop synchronization and preserved state

The initial Desktop HEAD was `d0ff630` on main. Existing modifications were limited
to `deployment/RUN_AND_DEPLOY.md` and `frontend/public/config.js`. Both are preserved
by exact pre/post hashes, never overwritten with development defaults. Untracked
`VisA_20220922/` and `supabase.txt`, ignored models, environments and runtime records
are outside the code synchronization and are never read/copied by it.

`sync_code.ps1` now follows the selected source branch/commit rather than hardcoded
main, rejects overlapping local edits/diverged history, creates the matching feature
branch on Desktop when needed and uses a fast-forward only. Existing Desktop main
and all history remain. Timestamped preservation receipts are written under
`development-support/space/desktop-sync-*.json`; older receipts/builds are retained.
Local fixture tests prove nonconflicting config preservation and conflict refusal.

Desktop verification builds must be separate from working `frontend/dist` and
`frontend/dist-static`. Build/verify/stage the Desktop cloud release with its own
existing public configuration; no model/data/package installation is needed.

## Remaining approval gates

- Review actual Supabase preflight results and approve manual auth migration.
- Deploy compatible inactive code only after explicit HF permission; preserve all
  existing feature variables and secrets. No SQL is deployed by the HF publisher.
- Prove real Developer TOTP and independent admin recovery before enforcement.
- Approve SMTP/external registration and role/privacy/revocation tests with test accounts.
- Configure approved n8n hosting, native Header Auth and SMTP, deploy the inactive
  Edge worker, test against a mail sink, then separately approve activation/scheduling.
- A laptop-only n8n remains unavailable while powered off. Outbox persistence and
  retry/dead-letter/manual recovery do not make local n8n an always-on mail service.

Public guest Demo, explicit-consent Gallery, private workspaces, DINO models and
vision-assisted text RAG are preserved. No Multimodal RAG upgrade was implemented.
