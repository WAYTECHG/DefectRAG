# No-send configuration diagnostic — deployment approval pending

UPDATE22October: approved diagnostic now deployed and verified with HTTP200,
all checks true, delivery0. Source persisted hash verified after reload. A separate
read-only log investigation found the original503's exact clockSQL error; see
docs/EMAIL_503_ROOT_CAUSE.md. SQL correction still requires separate approval.

User reports delivery1 was saved before the failed POST, then0 afterward. Current
QA event remains queued/attempts0/no snapshot; generic503 still has no preserved
body. Configuration or first claim failures remain hypotheses, not confirmed.
No further send is authorized. This change supports diagnosis without dispatch.

## Exact local changes

Only the existing staff-notification worker adds an explicit authenticated mode:
POST with X-DefectRAG-Check-Event set to the expected QA event UUID. It NEVER
falls through to dispatch, including invalid mode values. The dedicated worker
bearer remains required. Delivery must be exactly0 or it returns409. Unknown or
incorrect bearer returns401, invalid expected UUID returns400. Ordinary POST{}
without the diagnostic header retains the original disabled503/auth/send path.

Response contains only booleans for: resend transport, sandbox1, HTTPS project
URL, service-role/provider-key presence, test sender, Developer-recipient format,
configured QA UUID equals expected UUID, and existing emailConfiguration checks.
No environment values, keys, addresses, payloads, lease tokens or account IDs
are returned/logged. No SQL claim/prepare/finish, provider/network request, email,
permission change, schema change or frontend/auth/MFA behavior is involved.

ready_for_qa=true means CONFIGURATION SHAPE ONLY. It does not prove key validity,
Resend account-owner match, DB RPC permissions/runtime or a successful send.
False checks pinpoint settings to review; do not replace unrelated platform keys.
200 is diagnostic success, not notification acceptance. Do NOT enable delivery
even if every check passes. Further live sending still requires separate approval.

## Exact proposed deployment scope — NOT performed

Ask approval to update ONLY existing hyper-worker code with the tested bundle,
while retaining delivery0 and all existing secrets/settings. No new consumer,
HF deployment, n8n, migration, provider call, account decision or send approval.
Package: runtime/email-diagnostics-release/index.ts + manifest.json. Original
runtime/email-function-release files retained unchanged for rollback/reference.
SHA256:31db630590f852fc56eb5660b72a7f45fb4b577fd14352378e4be3632b31f453.

After approval, owner opens hyper-worker Code, replaces complete source with
that index.ts, and deploys ONLY existing function. No management connector is
available to agent. Preserve prior JWT gateway setting and dedicated handler
authentication; do not create another function or reveal private secrets.

Then Test with delivery0: POST, body{}, headers entered PRIVATELY:
- Authorization: Bearer followed by one space and saved worker secret.
- X-DefectRAG-Check-Event: 3d25e7b3-04c4-43c8-a49e-e473be3bcbdc

Return ONLY status/body. A wrong/missing diagnostic header with delivery0 cannot
send: ordinary request returns503; an explicit malformed header returns400/401.
409 means gate isn't exactly0: restore0 and inspect, never enable for diagnosis.
If configuration passes but original failure remains unresolved, next stage is
read-only RPC/schema/log inspection. Never retry a real send to produce logs.

## Local evidence and rollback

48 notification tests passed (19 new diagnostic tests +29 existing regression
tests) using injected fetch fixtures; no live network/services. Seven bundled
offline smoke checks passed, including disabled/auth/gate behavior and no network.
No tests/model experiments or frontend build repeated beyond relevant workers.
Production source equality and live diagnostic behavior await approved deployment.

Rollback code only: restore previous approved function bundle with delivery0;
no database/data rollback. Worker source change invalidates the existing React
release source fingerprint even though no UI changed: do not publish Hugging Face
with a stale release manifest; future HF release must rebuild/verify/stage through
the established publisher. No HF publishing is part of this diagnostic milestone.
