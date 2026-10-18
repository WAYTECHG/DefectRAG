# Phase 4 readiness — 18 October 2026

Status: prepared in source, **disabled in the deployed Space**. User confirmed the
reviewed SQL has NOT been executed. No migration, staff RPC test, account creation,
schema/policy/storage modification or authenticated database write was performed.
Unchanged reviewed SQL SHA256:
025ef75f224fbefda7d24b9a291b4532ec43b014d8f7659209cd8de4578beb47.

## Existing integration reused

StaffRepository validates each supplied staff JWT with Supabase Auth and checks the
existing staff allowlist through RLS. It uses existing shared_inspections records,
conversation JSON, private team-inspections bucket and archive/restore RPCs. It
does not use service credentials. Failed uploads/inserts propagate errors; partial
uploads can leave orphan objects for future operator cleanup, not false success.
Lists avoid signing every image or fetching conversation contents, and exports
paginate1000 rows per request. Stats currently cover latest1000 active records.
Archive considers up to500 matching records, restricting ordinary staff to their
own records and preserving developer authorization. RLS is the ultimate boundary.

Signed-in transport forwards the user's JWT; browser auth events refresh views.
Signed-out views discard the open result/messages. Original React components and
CSS stay unchanged; isolated build changes transport and accurate cloud wording.
These prepared changes have build/software checks, not live staff acceptance.

## Exact migration gate and remaining acceptance

1. User manually executes the unchanged reviewed file
   deployment/supabase_additive_conversations.sql in their existing development
   project's SQL Editor, then explicitly confirms success in this conversation.
   Do not execute it on their behalf or assume approval means execution.
2. Only after that confirmation, write the private
   development-support/space/migration-confirmed.json with
   {"user_confirmed_manual_execution":true} and the confirmation date. Publisher
   refuses phase4/5 without this gate; do not bypass it.
3. Build isolated frontend using existing Desktop public config. Publish phase4
   incrementally, using existing free hardware. Check runtime before requests.
4. User signs in themselves to the existing Staff workspace. Use their approved
   account to create one disposable public-fixture inspection and exercise
   defectrag_append_conversation and defectrag_acknowledge_review. Verify data
   persisted, report includes conversation, reload and a second authorized staff
   session see the expected shared state. Do not ask for passwords in chat.
5. After SQL confirmation, test both RPCs without a user JWT and with a real
   existing authenticated nonstaff account. Expect denied execution/no mutation.
   A missing function is not authorization proof. If no nonstaff account is
   available, record that acceptance gap; do not create an account implicitly.
6. Confirm archive ownership, developer recovery, private storage/RLS and expired
   or foreign sessions. Preserve existing records; archive/restore only own test
   fixtures. Finish remaining Phase5 acceptance and save sanitized evidence.

The publisher's confirmation file is an operational guard, not independently
verified database attestation. No live RLS/RPC success/denial is claimed yet.

## Explicit future hardening limits

- Approved staff can submit conversation answers without verifying their model
  provenance. Authorization and JSON/size checks do not attest model output.
- Alert acknowledgement currently stores a boolean, without acknowledging user
  or timestamp. The reviewed migration does not add this audit trail.
- Signed file URLs are bearer capabilities with expiry. Anonymous records are
  ephemeral; staff durability requires enabled backend, valid account and storage.
- Stronger provenance, acknowledgement audit and broader aggregate queries need
  separately reviewed changes. Do not silently enlarge the approved SQL.

Nine local software security checks passed, including nonstaff membership
rejection, isolated records, signed-capability tamper/expiry, export pagination,
own-only archive selection and upload failure propagation. They do not substitute
for account-based acceptance against actual Supabase policies.
