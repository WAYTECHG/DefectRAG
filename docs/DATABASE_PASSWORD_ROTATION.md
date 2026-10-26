# Controlled database-password rotation — 24 October 2026

CURRENT UPDATE: owner remembered the existing password and reports a successful
connection. No reset is needed or performed. The earlier reset approval was NOT
used and is superseded by the owner's decision to retain the working password.
Do not execute the reset/check sequence below; it is historical contingency
planning. Continue with SUPABASE_PRIVATE_BACKUP.md and the existing password,
entered only at private export prompts. No extra login test was performed.

Status: AUDIT/PREPARATION ONLY. The existing password is unavailable. No password
guess, rotation, authentication attempt, migration or restore was performed.
Separate approval is required BEFORE the owner privately performs the reset.

## Verified project connection

Read directly from this project's authenticated Connect -> Direct -> Session
pooler panel, not inferred from region:

| Parameter | Value |
| --- | --- |
| Project | zrzqpbcomlorfzszolrs |
| Pooler host | aws-0-ap-northeast-1.pooler.supabase.com |
| Port | 5432 (Session pooler, not transaction port6543) |
| Database | postgres |
| Client username | postgres.zrzqpbcomlorfzszolrs |
| Password | Existing unavailable; only the owner enters a new value privately |
| TLS for prepared check | verify-full with the cached container's system CA bundle |

The reported FATAL establishes that a pooler answered but rejected credentials;
it does not establish which candidate password or shell/URI interpretation failed.
The pooler routes the project-specific client identity to database role postgres,
so a backend error mentioning postgres alone is not proof that the project suffix
was omitted. The new test prompts directly instead of interpolating a password
into a URI, command argument or environment variable.

## Dependency audit and interruption assessment

Tracked runtime sources in backend/, deployment/ and frontend/src/ were scanned
without reading secret files or printing environment values. No runtime direct
PostgreSQL driver, DATABASE_URL, PGPASSWORD or database-password dependency found.
The three POSTGRES_PASSWORD matches are synthetic network-isolated SQL test
containers, not production Supabase credentials.

| Existing component | Actual connection/credential path | Expected reset impact |
| --- | --- | --- |
| HF and local Personal/Team history/sync | StaffRepository/PersonalRepository and local_sync use HTTPS PostgREST/Storage, publishable API key + user JWT | No database-password configuration update identified |
| Staff registration, MFA, approval | Native Supabase Auth and bounded Data API RPCs | Does not reset end-user passwords, factors, approvals or JWT signing keys |
| Community Gallery | backend/gallery.py SupabaseGallery.rpc uses HTTPS + public API key; gallery purpose key remains separate | No database-password dependency identified |
| DINO/Qwen/RAG/local history | Model runtime and local SQLite; cloud persistence uses the above HTTPS path | No direct database-password dependency identified |
| Developer notification Cron | Native DB Cron calls existing enqueue RPC; pg_net calls hyper-worker over HTTPS with the dedicated Vault bearer | No password literal/direct external Postgres client in this path |
| hyper-worker -> Supabase/Resend | HTTPS RPCs with server service-role API key; Resend/purpose credentials | Database password is not these API keys; do not rotate any of them |
| Existing local n8n | Actual DB_TYPE defaults to SQLite, no DB/PG env keys, zero stored credential rows, one active form workflow | No direct Supabase-password dependency identified; retain workflow/volume |
| Ad-hoc Docker psql/backup clients | Direct database credential | Must use the new password after rotation |
| Other/offline BI, ORM, scripts or clients outside audited scope | Not exhaustively discoverable | Any saved old password must be replaced before reconnecting |

n8n was inspected read-only: one Code, one Form and one Form Trigger node; the
Code node had no Postgres URI/driver/project/pooler/environment-credential markers.
No workflow executed or deactivated; no credentials decrypted/exported. Inspection
is not a proof about arbitrary future/dynamically generated code.

Live SELECT-only baseline: no OTHER postgres client backends visible in the
snapshot; this does not rule out disconnected clients or managed services using
different DB roles. User records remain Team9/Personal10/notes6/Gallery6/Staff3;
MFA+registration true, Developer delivery enabled, expected five-minute Cron active.
HF public health and Gallery both HTTP200. No fresh authenticated end-user flow or
new email was triggered. This is a before-reset baseline, not a post-reset result.

Assessment: no interruption requiring a DefectRAG credential update is expected
from the audited dependencies. Zero downtime is NOT guaranteed: direct clients
using the old password will fail, existing sessions may disconnect, and the shared
pooler can briefly cache old credentials after rotation. Supabase's managed
database/service behavior and untracked external clients are outside this audit.

## Reviewable rotation procedure — perform only after separate approval

1. Keep the migration blocked and preserve the saved baseline. Confirm there are
   no untracked direct clients needing coordinated credential updates. Use a quiet
   window; no schema change, project restart, HTTP-key rotation or forced logout.
2. The OWNER opens Database -> Settings -> Database password -> Reset password.
   Enter/generate, confirm and submit the new password privately. The agent must
   not enter, retrieve, photograph or store the new value. Save it privately in
   a password manager under a dedicated project/database entry, separate from the
   notification worker secret and Staff login. Do not paste it into chat, source,
   connection URLs in shell history, .env screenshots or logs.
3. Change ONLY the postgres database password, once. Do not change Auth SMTP,
   Staff passwords/MFA, API/JWT/service keys, Vault bearer, Resend, gallery keys,
   n8n encryption key, SSL enforcement, network restrictions or access policies.
4. Wait for the dashboard's success confirmation and allow at least30seconds for
   the pooler to refresh. Do not rerun old guessing commands or reset repeatedly.
5. From the interactive Desktop project terminal run, once:

   ```powershell
   & '.\deployment\verify_pooler_readonly.ps1'
   ```

   The helper was validated OFFLINE with cached PostgreSQL17.11 and system trust
   roots. It prompts privately through psql -W, publishes no ports and saves no
   password. Its ONE connection verifies TLS hostname/certificate, executes BEGIN
   READ ONLY, selects current_user/current_database/read-only state and database-
   side TLS metadata, then ROLLBACK. Expect user postgres, database postgres and
   read_only=on. Behind a pooler pg_stat_ssl describes the database-side connection;
   libpq verify-full enforces client-to-pooler TLS separately.
6. On failure, stop after that one attempt. Keep only the error text, not a URI or
   credential. Certificate failure must not be mistaken for a bad password; do not
   downgrade TLS. A post-rotation 28P01 can be transient pooler caching. Diagnose
   timing/circuit-breaker/network first; any later reconnect is a separately
   deliberate check with the SAME new password, never guessing or another reset.
7. Once connected, compare the read-only SQL baseline and public endpoints; owner
   privately verifies Staff sign-in/MFA, Personal/Team visibility and Gallery as
   needed. Check existing Cron/worker outcomes WITHOUT creating a request or
   sending another QA email. Do not switch off working Developer delivery.

No old password is available for rollback. If a direct client breaks, update that
client to the newly saved credential. Do not weaken RLS/MFA, restore an old
database, change API keys or repeatedly rotate to troubleshoot credential failure.
Escalate a persistent pooler-only failure using Supabase's supported diagnosis.

## Backup and recovery AFTER successful credential verification

Prepare the complete private database backup outside Git, covering roles, schema,
data, grants/RLS, native Auth/MFA and custom managed-schema policies, with a
manifest/checksums. Account for Supabase encryption/root-key recovery requirements
using the official restore procedure. Preserve Storage object bytes separately.
No password in backup command arguments/history; the owner supplies it privately.

Restore/rehearse only into an isolated compatible Supabase/Postgres runtime with
outbound network and schedulers disabled, never into production. Verify integrity,
critical table/record counts, RPC/policy definitions, Auth/MFA recoverability and
image bytes. A successful pg_dump, archive listing or plain-PG mock does not alone
prove full native Supabase recovery. Report scope/limitations explicitly and keep
the Corrective Actions migration blocked until this backup gate is met.

## Official references checked 24 October 2026

- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/kb/troubleshooting/how-do-i-reset-my-supabase-database-password-oTs5sB
- https://supabase.com/kb/troubleshooting/supavisor-error-password-authentication-failed-after-password-rotation
- https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore

The temporary-access alternative was reviewed but not enabled: it changes database
authentication mappings and requires SSL enforcement. The current settings show
SSL enforcement off. No JIT/SSL/IP/account-access configuration was changed.
