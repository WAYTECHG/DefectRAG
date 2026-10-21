# Exact disposable QA account removal — review pending, 21 October 2026

Target ONLY: saputangan1404@gmail.com. Never select another email in the Auth
Dashboard; a previous screenshot showed a different account selected.

User-provided live preflight reports exactly one Auth account with Staff role:
membership1, access request1, access audit2, notifications2. Personal/team
inspections, notes, workspace audits, archiver references, other-account decisions
and matching artifact paths were all0. No sending notifications reported.
Storage ownership was NOT covered by the path count; cleanup checks both owner
column variants and aborts on any owned objects. Attempts/provider preparation
were also not returned; cleanup requires all notifications unattempted/unprepared.

## Proposed scope; no deletion authorized or performed yet

1. Run deployment/qa_account_backup_PRIVATE.sql (SELECT only) and export its ONE
   JSON result to a private location outside Git/project folders. Do not send it
   to chat. Check it contains 1 membership,1 request,2 audit,2 outbox records.
   This is a metadata recovery snapshot, not an Auth/database/Storage backup.
2. Review deployment/qa_account_cleanup_REVIEW_ONLY.sql. It contains a destructive
   transaction deleting precisely those SIX QA metadata rows. It does not delete
   the Auth account, other users, schema, Gallery, models or any inspection.
   Obtain explicit approval for this file and exact target before running it.
3. Keep notification delivery0 and workers/schedulers inactive. The SQL cannot
   verify external Edge secret values. Recheck the target is disposable QA and
   the private backup exists. Do not change production secrets as part of cleanup.
4. After approval, manually execute the ENTIRE cleanup file once as project owner
   in SQL Editor. The guards reject Developer/revoked/missing targets, changed
   counts, prepared/attempted/live notification work, extra live FK-linked data,
   unknown incoming dependencies, custom triggers and Storage ownership. Locks
   and timeouts are bounded. Any exception rolls back the transaction; do not
   delete dependencies or bypass guards to force success. Review the error.
5. Only after confirmed COMMIT, manually select the EXACT target email under
   Authentication > Users and delete it. That is a separate irreversible Auth
   action, never a raw auth.users SQL delete. If deletion fails, inspect the new
   error; do not repeat cleanup or delete other accounts. The application is
   preserved, but this target's Staff access ends when membership is removed.
6. Once Auth deletion is confirmed, re-register with the same email privately,
   confirm it, submit a Staff request, and STOP at Pending. A new Auth UUID is
   expected. No automatic restore/migration of old identity or permissions.
   Verify the new pending notification before any separately approved send.

## Recovery and verification limits

Before COMMIT, a SQL error causes rollback; on uncertain SQL Editor status check
current counts before retrying. After COMMIT and BEFORE Auth deletion, restoring
the six metadata rows requires a separately reviewed transaction using the private
snapshot and unchanged Auth identity; it is not automatic. After Auth deletion,
that snapshot cannot restore the original identity/password/MFA/session state.
Do not treat re-registering the same email as restoration of the old account.

Files were locally reviewed against the source schema and supplied live FK
metadata. No PostgreSQL runtime is available here; neither cleanup nor backup SQL
has been executed by the agent. No live deletion/restore/regression claim is made.
No runtime/UI code changed, so completed model experiments/tests were not repeated.
Existing Developer/other QA accounts and native mandatory MFA remain unchanged.
This one QA exception deletes its two access-audit records; do not generalize it
into a production user-deletion policy or relax immutable audit access controls.
