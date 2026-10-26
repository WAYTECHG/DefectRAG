# Private Supabase backup export — updated 25 October 2026

## Fresh paired recovery fully verified within documented limits

25October: new supplement recovery-20261025-140457-bfb9c42b belongs to the fresh
supabase-20261025-134008-d593ba5b DB export. All44encrypted files/checksums/private
ACLs pass. Every one of42Storage files (4,000,558bytes) decrypts and matches its
SHA256; original paths/IDs/sizes exactly match the fresh DB snapshot.

Actual offline pinned Supabase PG17 restore preserves original role grantors and
selected row contents including CA/outbox/sync. Backed-up root key decrypts the
restored Vault row. Actual local GoTrue rejects wrong TOTP422 and accepts correct
TOTP200; restored Staff helper denies native AAL1 and accepts native AAL2. No
emails/production calls; all disposable containers removed. Same-profile DPAPI,
excluded role passwords and non-clone/isolated-signing-key limits below still
apply. This is not a production or existing-password restoration test.

Recovery gate is now SATISFIED for the proposed QA extension, within this scope.
Live SELECT-only preflight also passes all5booleans; case1/events9/effects0.
No SQL migration/permissions/keys/flags changed. Separate owner approval and
manual execution of the exact reviewed QA SQL remain required. No more backup
export or token prompt needed for this gate.

Safe receipts: results/private-backup-refresh-20261025/full-recovery-verification.json,
recovery-gate-review.json and live-qa-preflight.json. Original private export
manifests deliberately retain historical status; they were not overwritten to
declare success. The following supplement-pending text is historical.

## Fresh refresh: database restore passed; supplement pending

Owner completed supabase-20261025-134008-d593ba5b. Both encrypted checksums and
DPAPI decryption/readback pass. Actual archive857entries/63data sections restored
successfully in the pinned network=none Supabase PG17 runtime with Cron OFF and
original role grantors. All selected counts AND private row fingerprints match
this same archive. The verifier now includes the optional current CA ledger,
notification outbox and sync receipts. Eight focused tests pass for that change.

Fresh snapshot contains42Storage objects, while the earlier verified24October
supplement contains38. Reusing the old inventory would omit four newer objects.
The fresh database-only restore does NOT establish current Storage byte/root-key/
native Auth recovery. Keep QA migration blocked. No production restore occurred.
Safe receipts: results/private-backup-refresh-20261025/.

Next private action, with the previously saved Supabase PERSONAL ACCESS TOKEN:

```powershell
& 'C:\Users\User\Desktop\DefectRAG-v2\deployment\export_supabase_recovery_material.ps1' -BackupDirectory 'C:\Users\User\AppData\Local\DefectRAG\PrivateBackups\supabase-20261025-134008-d593ba5b'
```

This is NOT the database/Staff password, worker secret or project API key. Enter
the token only at the hidden prompt. Existing helper reads root-key/Storage
material and creates a new encrypted owner-only supplement; no key reset, writes
to Supabase, settings or email. Avoid image uploads/deletes while it snapshots
Storage. Return only its safe completion message/directory. Do not rerun DB export.
Cross-check the fresh supplement against the fresh archive before declaring
complete recovery. Older proof below remains valid only for the earlier snapshot.

## Current result: recovery rehearsal verified; migration approval pending

This result supersedes the earlier incomplete-recovery sections below. The owner
completed recovery-20261024-152520-f22c5428 under the completed database export.
Verified40 encrypted supplement files: the root key, encrypted inventory and38
Storage objects (3,988,970 original bytes). Every ciphertext checksum, DPAPI
decryption, object SHA256/length and private ACL passed. All38 paths, IDs and sizes
match the original database snapshot. No PAT, service key, root key or private
image/row payload is included in repository evidence.

Actual Vault decryption PASSED against the original restored Vault row using the
backed-up key, inside a disposable network=none Supabase PG17 container. The local
runtime must PRELOAD supabase_vault and use its private getkey script at startup;
loading the SQL extension alone does not initialize its root key. No project key
was changed. No host plaintext key/dump/image file was written.

The earlier grantor adaptation is REMOVED. Fresh live preflight confirms the
production bootstrap superuser atOID10 is supabase_admin. Initializing the
isolated cluster with the SAME bootstrap identity allows all22 original role
membership statements, including21 GRANTED BY clauses, to replay unchanged.
Only the redundant CREATE ROLE for that already-created bootstrap role is omitted;
all original ALTER ROLE attributes/GRANT options/attribution are preserved.
PostgreSQL17 documents the bootstrap-grantor rule:
https://www.postgresql.org/docs/17/sql-grant.html

Database restore PASSED with original roles. Critical COPY row content, not just
counts, matches the archive for Team/Personal inspections and notes, staff/access
requests, Gallery, Auth users/MFA factors, Storage metadata and Vault secrets.

Native Auth recovery PASSED using the official pinned GoTrue2.197.0 binary and
migrations in that SAME network=none container. A restored approved QA Staff
identity obtains a local native AAL1 session through an admin-generated magiclink
(NO email); the original backed-up TOTP factor rejects a wrong code422, accepts a
correct code200 and issues AAL2. Restored actual Staff helper denies AAL1 and
accepts AAL2. Email, JWT, factor seed and codes remain private in-process. The test
uses a fresh isolated signing key, not the production project's signing key.
All containers are removed afterward; live users/sessions are unchanged.

This proves native TOTP recovery and the restored guards; it does NOT claim an
existing-password login test, full hosted-platform clone, production restoration
or live Corrective Actions authorization. DPAPI still requires this Windows
profile, role passwords remain excluded, and portable/off-site custody requires
separate planning. Do not delete the Windows profile or upload backup material.

Recovery passed PowerShell7 and Windows PowerShell5.1, plus9 focused unit tests.
Fresh production SELECT-only preflight shows all pre-existing metadata/counts/
permissions/fingerprints unchanged and no Corrective Actions objects installed.
Evidence: results/private-recovery-complete-20261024/. The backup gate for the
reviewed additive migration is satisfied within these stated recovery limits;
SEPARATE owner approval and owner-run SQL execution are still required.

Reproduce privately with restore_private_backup.ps1 using -BackupDirectory,
-RecoveryDirectory and -NativeAuth. This never connects to production or prompts
for credentials; its two official image digests are pinned in the helpers.

## Latest verified status: export and isolated database rehearsal

Owner completed `supabase-20261024-122741-b53247aa`. Both encrypted sizes and
SHA256 values match its manifest; both decrypt under the current Windows profile.
The custom archive has 789 entries, 58 data sections and 25 policy entries.
No original backup was modified. The earlier failed folders remain untouched.

An actual local archive restore completed in the official Supabase PG17 image
`17.6.1.136`, pinned digest
`sha256:f371b5f3f2ac0a05703f33d6e6134515fb2498cab708fb948a0aeb7481467c00`.
The disposable container used network=none, no host mounts or exposed ports,
Cron off, and was removed afterward. Decrypted exports travelled only through
binary stdin pipes; no host plaintext archive/SQL file was created.

Counts compared against COPY sections in the SAME encrypted archive all match:
Team9/notes6, Personal10/notes7, Staff3, requests4, Gallery6, Auth users5/MFA
factors5, Storage object metadata38. Personal/Team RLS and registration/MFA=true
were retained. The resulting catalog has27 policies including extension policies.

**Limit:** the unmodified global-role replay hit hosted PostgreSQL ADMIN-option
grantor restrictions. For the disposable data rehearsal only,21 GRANTED BY
clauses were rebound to the local bootstrap admin; no recipient or membership
option was removed and the source export was not rewritten. Exact managed-role
grantor recovery is NOT verified. This adjustment must not be copied to production
or used as proof of identical hosted Supabase security.

**The complete recovery gate remains unsatisfied.** Native Auth/MFA login has not
been exercised, Vault's root key has not been backed up/verified, and the38 actual
Storage files have not been copied. The database dump contains metadata, not
image bytes. Supabase's official manual-restore procedure requires separate root
key custody for Vault; it is absent from logical dumps:
https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore

The next owner-assisted step needs a privately entered Supabase Personal Access
Token to READ recovery material through the official Management API. Never paste
a PAT/root key into chat, a command, a Git file or a screenshot. Do not PUT/reset
the project's root key, reset passwords, change permissions or migrate yet.
The token is distinct from the database password and app API keys. Endpoint
permissions must be checked before its use; do not assume a generic read-only
token is sufficient. Official API documents `project_admin_write` for this GET:
https://supabase.com/docs/reference/api/v1-get-pgsodium-config

Owner confirms a token is saved privately. Next ONE hands-on action:

```powershell
& 'C:\Users\User\Desktop\DefectRAG-v2\deployment\export_supabase_recovery_material.ps1' -BackupDirectory 'C:\Users\User\AppData\Local\DefectRAG\PrivateBackups\supabase-20261024-122741-b53247aa'
```

Enter the existing Supabase PERSONAL ACCESS TOKEN at its hidden prompt. This
helper reads the existing root key and existing service-role API key through
Management GET endpoints (no key creation/reset). It uses the latter in memory
only to list/download Storage objects. The Storage list POST is a read operation;
there are no uploads, deletes, permission updates, SQL or email operations.
Redirects are disabled, destinations/methods restricted, and a256MiB object-byte
safety cap is enforced. No token or service key is saved. New encrypted files are
written in a unique owner-only recovery subdirectory of the original private
backup. Original archives/manifests remain unchanged. Names/paths/bucket metadata
are encrypted in storage-inventory.dpapi, not printed or included in the safe
summary. Root-key/object encryption is read back and hash-checked before success.
This is a current Storage read, not an atomic cross-service database snapshot;
do not add/change/delete inspection images during the export.

Expected: encrypted root-key, Storage files/inventory, and recovery_manifest.json
with status encrypted_recovery_material_exported_not_full_restore_verified.
Return only the completion message/directory or safe HTTP error. On401/403, stop;
do not guess passwords or expand token permissions without review. This owner-run
remote export has NOT yet been tested with a real PAT. Offline synthetic fixture
validation passes PowerShell7 and5.1 (nested listing, encryption/readback, rejected
write/off-host requests and overwrite protection). Native Auth/MFA and exact
hosted-role grantor recovery remain separate unverified checks.

Helpers: `inspect_private_backup.ps1 -BackupDirectory <private-directory>` reads
only archive metadata offline. `restore_private_backup.ps1` runs the isolated
database rehearsal and explicitly reports remaining gaps. Neither changes the
original manifest into a claim of complete recovery. Evidence is in
`results/private-backup-rehearsal-20261024/verification.json`.

The sections below retain the earlier export instructions for reference.

The owner remembered the existing database password and reports a successful
connection. No reset is needed or performed. Do not repeat the login test or use
the earlier rotation instructions. This is owner-reported success, not a new
agent-observed authentication test.

## First hands-on action: export

The first owner-run export failed at certificate verification, before a valid
backup was produced. The earlier helper incorrectly used the generic Alpine CA
bundle; its offline check proved readability, not trust of this project's CA.
This is corrected: the official public Supabase CA is pinned and mounted read-only
into Docker, with `verify-full` retained. A credential-free TLS/hostname check now
runs BEFORE a new backup directory or password prompt. Live TLS1.3 verification
passed; no database authentication was attempted by that check.

Do not reset the working password or switch to `sslmode=require`. Retain the
failed `supabase-20261024-121947-2ffff669` directory as incomplete; the helper does
not overwrite or delete it. Rerun the corrected helper below in a new attempt.

From an interactive PowerShell terminal:

```powershell
& 'C:\Users\User\Desktop\DefectRAG-v2\deployment\export_supabase_backup.ps1'
```

Use the SAME working database password at the TWO hidden prompts. These are
database and global-role exports, not password guesses or extra login tests.
Do not paste a connection URI/password into the terminal command or chat.
The helper uses the actual project Session pooler and cached official PG17.11,
with client certificate/hostname verification, no image download or published ports.

It exports the database into a custom archive (schema/data/ownership/grants) and
global role definitions separately. Custom database-role passwords are excluded;
future custom-role login recovery requires separate credential custody. Auth table
rows are included in the database archive subject to source-role permissions.
If the managed database denies an object, export fails rather than silently
omitting it or escalating production permissions.

Private output is under `%LOCALAPPDATA%\DefectRAG\PrivateBackups\supabase-...`.
Each attempt creates a new directory with inheritance disabled and current-user
access only; no old backup is overwritten. Native Windows DPAPI CurrentUser seals
each completed export. The helper reads it back, compares hashes, and only then
removes its newly generated plaintext file. No recursive deletion or existing
application/cloud data change occurs. A failure can leave a partial plaintext
export in that private directory; do not share it or mistake it for a good backup.

Expected files after successful export:

- `database.dump.dpapi`
- `roles.sql.dpapi`
- `manifest.json`: `status=exported_not_restore_verified`, ciphertext sizes/hashes,
  and explicitly false storage/key-recovery/isolated-restore flags.

DPAPI recovery requires this Windows account/profile; the Supabase password is
not its decryption key. The ciphertext is not independently portable to Oracle
or another machine. Do not delete the profile or treat an off-site ciphertext
copy alone as disaster recovery. A portable encrypted/key-custody plan can be
prepared separately, without publishing any credential.

The corrected script has passed OFFLINE tool/version/pinned-CA mount and synthetic
DPAPI/file/ACL validation under PowerShell7 and Windows PowerShell5.1. Its separate
credential-free probe has verified live certificate/hostname trust. The failed
owner-run export is not a usable backup; no successful real export or isolated
restore has yet been verified.
On a connection, permission, encryption or export failure, stop and report only
the error text. Never retry candidate passwords, reset credentials, relax TLS or
change production grants to force success.

## After export: do not migrate yet

Report only completion and the printed backup DIRECTORY path, not file contents.
Then inspect the safe manifest, decrypt/rehearse restoration in an isolated
compatible Supabase/Postgres environment with no outbound network or schedules,
compare relevant objects/counts/permissions, verify native encryption recovery
requirements and preserve original Storage object bytes separately. A logical
dump contains Storage metadata but not those bytes. Native Supabase Auth/MFA
recovery cannot be claimed from a plain-PG mock or successful archive listing.

Only after the complete required recovery checks pass may the separately approved
Corrective Actions migration proceed. Existing Developer emails, n8n workflows,
Auth/MFA, Personal/Team/Gallery records and all model/RAG functions remain unchanged.
