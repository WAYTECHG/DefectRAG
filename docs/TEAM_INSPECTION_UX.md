# Team inspection input clarity

Implemented locally on20 October2026 from `7e6d92e`, branch
`feature/auth-mfa-inactive`. **Not deployed.**

## Cause and intended workflow

The disabled Team button is intentional. The React submit handler and the cloud
server both reject new inspections in Team scope when Personal Workspace is
enabled. New inspections save privately; team sharing is a separate explicit
action. That restriction remains unchanged.

The old button used only a disabled attribute, leaving a prohibited cursor without
an adjacent reason. The old scope-switch handler also cleared the selected files.

## User-visible change

The disabled Team button now displays:

> New inspections are created in Personal Workspace. Switch to Personal to run an inspection, then share the result with your team.

A **Switch to Personal Workspace** button changes the existing client scope without
reloading. On a safe Team-to-Personal transition it retains the exact uploaded
File objects, selected product and batch label. It discards saved result images,
conversations, review state and workspace lists, and invalidates old asynchronous
responses. It performs no upload, inspection, database write or sharing operation.
Opening a saved record and starting a new inspection retain their existing reset
behavior. Switching accounts/signing out still clears files. Moving from Personal
to Team clears the draft images rather than carrying private input into Team view.
Scope changes are disabled while inference, evidence generation or record loading
is active; direct invocation of the new switch also respects this boundary.

The Run button now explains checking permissions, pending/rejected/revoked access,
required MFA, provider unavailability, missing/unsupported/oversized images, batch
constraints, connection loss and work in progress. The reason is visible text,
linked with `aria-describedby`, and available as a title. Existing dashboard
classes, icons, CSS, responsive layout and transitions are reused.

Signed-in readiness uses the existing native Supabase own-status RPC. A denied or
failed signed-in check never falls back to anonymous access. Stale responses after
an identity change/unmount are ignored; focus/reconnect/auth events and the normal
15-second polling refresh readiness. This is a UI check: backend, RLS, native MFA
and explicit-sharing authorization remain authoritative and unchanged. Anonymous
Demo Mode and offline local inference remain available in their original scopes.

Client validation checks MIME/extension, file size/count, category and batch input.
The existing backend still validates actual image bytes/dimensions and permissions.
GPU quota/capacity cannot be predicted by a health check; request-time errors retain
the existing error/retry behavior. UI tests render real JSX and exercise production
handlers with fixtures. No browser end-to-end or new live Supabase/HF/model-inference
acceptance pass is claimed for this undeployed change.

## Files and validation

- `frontend/src/main.jsx`: wire action/readiness; retain safe draft during switch.
- `frontend/src/InspectionAction.jsx`: existing-style action, explanation and switch.
- `frontend/src/inspectionReadiness.mjs`: input/access readiness and stale-safe watcher.
- `frontend/tests/inspectionReadiness.test.mjs`: actual JSX rendering/handlers,
  draft identity, context invalidation, input states, auth changes and outage tests.
- `results/team-inspection-ui-20261020.json`: sanitized verification receipt.

96 frontend tests passed (including34 new focused cases).55 existing offline
backend auth/MFA, Personal Workspace and cloud security tests passed. Local,
showcase and cloud production builds passed into isolated runtime folders.
The verified cloud bundle was staged locally; the publisher's **offline-only**
readiness check passed. No remote publisher or SQL was executed.

CSS remains `index-Bn4HF2vD.css`, SHA256
`087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661`.
Existing installed local/static builds were not replaced. No dependencies installed,
models run/retrained, secrets changed, staff decisions made or notifications sent.
Existing nonfatal Vite runtime-config/Gradio browser warnings remain; static/dynamic
auth-helper imports also produce a harmless chunk-optimization warning.

## Approval and next verification

The new UI is ready for deployment review, with verified artifacts in
`runtime/team-inspection-ui/cloud` and local publisher input
`development-support/space/ui-dist`. These are ignored generated files, not GitHub
uploads. Code checkpoint `b859d67` was synchronized to Desktop; its staged cloud
artifact/source checks passed and working config/local/static hashes were preserved.
The final documentation/formatting checkpoint follows, with the same verified
normalized source fingerprint. Nothing has been uploaded to HF.
**Do not deploy or push without explicit approval.**

After approval, use the verified existing HF publisher. Then manually verify a
valid draft under Developer AAL2: Team restriction/explanation -> switch -> same
image/category/batch in Personal -> successful private inspection -> separate
explicit team share. Also check pending and AAL1 messages. Do not approve the
existing pending applicant or publish/share test images without permission.
Do not repeat signup, SMTP/MFA enrollment, model experiments or SQL migrations.
