# Confirmed email-worker 503 cause — 22 October 2026

## Current status: approved correction applied

Following explicit user approval, the exact guarded correction below was applied
once through the signed-in Supabase SQL Editor. Its transaction succeeded and
verified unchanged function owner, grants, security and configuration. Independent
post-commit SELECT confirms the unsafe statement is absent and WHERE singleton is
present; anonymous/authenticated execution remains denied and service-role
execution remains allowed. Registration and mandatory MFA remain enabled.

The selected QA event remains queued with zero attempts, applicant Pending and no
staff membership. Credential-free worker POST at 2026-10-22 05:32:08 UTC returned
503 notifications_disabled. No claim, provider request, email, automatic retry,
account change or secret change occurred. Evidence is saved in
results/email-clock-fix-live-20261022/. Actual claim/provider execution after the
repair remains untested and requires separate single-event-send approval.

The sections below retain the original diagnosis and reviewed repair procedure;
their pending-approval wording describes the earlier checkpoint, not current state.

## What was verified live

After the user authorized agent-managed no-send diagnosis and signed into the
existing Supabase project in the in-app browser, only hyper-worker was updated
with the tested diagnostic package from source checkpoint eb9c267. The previous
deployed source was copied through its UI editor for rollback; normalized SHA256
matched the previously reviewed a70e89e05d66918ed00a78bfdc769c2afd761fb10e376be0e12903147cd82017.
After deployment and page reload, persisted code exactly matched diagnostic bundle
31db630590f852fc56eb5660b72a7f45fb4b577fd14352378e4be3632b31f453.
No other function, HF app, secret, key, account, permission or database schema was
changed. Delivery0 verified before deployment and afterward using public503.

The user privately entered the saved worker bearer into the prepared diagnostic
header field. Agent did not read/copy it and cleared it immediately after the
no-send invocation. Live HTTP200 returned delivery_disabledtrue/ready_for_qatrue
with every configuration-shape check true. Unauthorized diagnostic401 verified
without a credential. These tests cannot call a database RPC or email provider.
They establish configuration presence/format, not provider key validity.

A SELECT-only Dashboard audit independently confirmed: applicantPending/no
membership, selected eventqueued/attempts0/nosnapshot; registrationtrue,
mandatoryMFAtrue; direct claim owned bypostgres/SECURITYDEFINER/emptysearchpath;
anonymous/signed-in execute false, service_role true; clock one row and ready.
Reading pg_get_functiondef was inspection ONLY, not a function invocation.

## Root cause confirmed, no longer a guess

Historical PostgreSQL log a0e3292a-89e5-4407-845c-53ffdabc957c at
2026-10-21 05:52:38.949 UTC (13:52:38.949 Asia/Kuala_Lumpur) reports SQLSTATE21000:
UPDATE requires a WHERE clause. Raw context names line26 of the direct claim RPC
and the exact failing statement:

```sql
update public.notification_dispatch_clock
set next_claim_at=now()+interval '30 seconds';
```

Correlated API Gateway log at13:52:37 shows POST to that RPC returning400. The
worker turned its RPC error into generic503dispatch_unavailable. The late clock
error rolls back the function's entire transaction, including the provisional
outbox claim, hence attempts0/nosnapshot/no provider send. This was a bug in the
prepared notification SQL, not proof of a Resend problem or Edge compute quota.
The database's safety protection is working; do not disable it to bypass the bug.

Evidence folder: results/email-diagnostic-deployment-20261022/ contains sanitized
response/grants/state, public gate checks, historical context and safe screenshots.
No worker credential, provider key, private email body or Auth token was saved.

## Exact correction prepared; NOT applied to production

Use ONLY deployment/supabase_notification_clock_where_fix.sql after approval.
It reads the current function definition, requires exactly one known bad statement,
substitutes WHERE singleton, and recreates only that function. It preserves and
verifies function owner, ACL, SECURITYDEFINER and search_path configuration in one
transaction. No row is claimed, updated, approved or mailed by applying it.
Unknown/already-fixed definition or metadata drift causes rollback. Bounded locks/
timeout apply. Do NOT rerun the original direct-notifications migration.

Corrected statement:

```sql
update public.notification_dispatch_clock
set next_claim_at=now()+interval '30 seconds' where singleton;
```

The fresh-install migration source has the same one-line correction so new
installations do not inherit the bug. Historical applied code remains in Git.
The local SQL fixture now requires active safeupdate protection and probes that
an unqualified fixture UPDATE fails while a scoped UPDATE works, before exercising
the real direct claim. This SQL fixture has NOT been run: local Docker engine is
stopped and no isolated PostgreSQL stack was started/downloaded. Earlier48 worker
tests/7 bundle smoke checks still apply; no worker changes since those tests.
The corrective SQL is reviewed/prepared, not claimed runtime-validated.

## Next controlled action

Obtain explicit approval for the exact corrective SQL. Agent can then apply it
through the signed-in Dashboard (no credential in chat), retain delivery0 and run
deployment/email_clock_where_fix_verification.sql SELECT. Expected unsafefalse/
scopedtrue, same owner/grants, auth flags true, applicantPending/membershipfalse
and queuedattempts0. No Resend call, account decision or automatic retry included.
Keep no-send diagnostic available. Require separate approval for any new real send;
the earlier one-attempt permission does not authorize another attempt after repair.

If migration errors, its transaction rolls back. If uncertain, inspect the SELECT
before any repeat. Keep delivery0; do not reset outbox/idempotency state or disable
safety/RLS. Do not restore the broken clock function as routine rollback. Any new
fix after an unexpected result needs review. Code-only diagnostic rollback can
restore runtime/email-diagnostic-backup-20261022/hyper-worker-before.ts with delivery0.

React/workspace/gallery/model/RAG behavior is unchanged. Its existing release
fingerprint is stale from worker/migration source edits; rebuild/verify/stage only
when a future HF release is authorized. No HF or GitHub publishing performed.
