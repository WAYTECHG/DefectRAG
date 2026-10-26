# Current local n8n result — 26 October 2026

The hands-on integration is COMPLETE within its sink-only test scope. Existing draft **DefectRAG CA - LIVE QA SINK ONLY - INACTIVE** (yx3NG0Ac1kIv8L37) passed all9 nodes against real Supabase; one local test message, durable receipt/finalization and SAME case Closed/version7 were independently verified. The test sink is stopped, QA is OFF and execution input was cleared. Do not rerun consumed grants, generate keys or publish the workflow to repeat an old lesson.

Current operating guide: [LOCAL_OPERATION_20261026.md](LOCAL_OPERATION_20261026.md). Full result: [CA_N8N_COMPLETION_20261025.md](CA_N8N_COMPLETION_20261025.md). Inspect the saved workflow screenshot to explain its validation, effect reservation, SMTP acceptance and receipt steps. Separate simulated duplicate/receipt-loss lessons below remain useful, but do not prove hosted production delivery.

The owner chose local operation and deferred always-on hosting and Multimodal RAG. Production Corrective Action notifications remain inactive; independent cloud Developer registration emails remain unchanged.

## Historical practical lessons (already completed)
# Corrective Actions: local n8n practical lessons

## Native failure lesson — verified 25 October 2026

The owner opened the IF node; native panel confirms execute=false/done=true on
False Branch(1 item). Agent then demonstrated a separate synthetic receipt-loss
scenario using two deliberate GUI runs. First: local SMTP accepts1, receipt HTTP
503 with simulated_receipt_failure. Then restore the fixture endpoint without
resetting state. Second: callback denies another execution and Require durable
completion reports Ambiguous notification requires manual reconciliation. Actual
sink count remains1, finish calls1, begin calls2. Both expected errors are PASS
for the safety behavior, not production outages. Do not enable the generic HTTP
node's suggested automatic retry or manually rerun SMTP to clear this message.

Temporary simulator stopped. The ledger stays simulated/in-memory; production
SQL's processing->uncertain transition is not reproduced by this lesson. No live
Supabase effect, delivery, permission or production setting changed. Evidence is
practice-ambiguity-review.json plus native output/counters. Next live approval
gate and local/cloud connectivity limits: docs/CA_LIVE_BRIDGE_NEXT_GATE.md.

## Local callback, SMTP sink and duplicate branch — verified 25 October 2026

Separate inactive practice workflow DRCALocalPractice20261025 completed two native
GUI runs: first accepted one synthetic mail and recorded completion; second got
execute=false/done=true and skipped SMTP. Actual fixture counts begin2/finish1/
accepted1/realEmails0. Six focused new simulator tests passed, including failure
quarantine and HTTP input limits. Existing isolated8scenario suite not repeated.
Original authenticated draft and all production settings remain unchanged.

Next hands-on action: in **DefectRAG CA - SIMULATED CALLBACK + MAIL SINK**, inspect
**Reserve notification effect** OUTPUT JSON (`execute:false`, `done:true`), then
open **Effect requires execution** and follow its false branch. No execution,
credentials or publishing is needed to learn this decision.

Temporary helper was stopped after evidence capture. This uses an in-memory
simulated ledger with fixed dummy IDs, loopback SMTP with no login or relay, and
a manual trigger/final no-op. It is NOT live Supabase callbacks, crash durability,
inbox/content verification or laptop-off hosting. Full boundaries and restart
instructions are in deployment/n8n/LOCAL_PRACTICE.md. Production CA remains OFF.

## Latest verified result — 25 October 2026

Owner transport JSON confirms HTTP500,14readiness checks and ONE credentialed
submission. Helper passed=null is intentional; independent native 'Invalid case
event [line1]' completes the check. Authentication acceptance + intended malformed
schema rejection PASS. Do not repeat or rotate keys because of this expected500.

Found403 cause: the actual credential Connection **Name** did not match
X-DefectRAG-CA-Key; the display title is a separate field. Corrected public Name,
owner saved, secret Value unchanged/unread by agent. Same NEW local key now gets
through native Header Auth; the partial Validate node returns **Invalid case
event [line 1]** for the deliberately malformed body. This is the intended
rejection. Callback/SMTP nodes did not run. Exact output saved in
results/n8n-hands-on-20261025/validation-output.txt. Owner transport status confirms
HTTP500/14checks/ONE submission; native node evidence completes the expected
rejection check. Do not repeat the probe or treat passed=null as failure.
All production CA automation remains OFF. Live positive Supabase callbacks,
effects, SMTP delivery and hosting are NOT established by this partial test.

## Synthetic pinned-input validation — verified 25 October 2026

Owner requested agent completion of this step. Started the existing stopped
Docker engine, opened the original inactive QA workflow, and used Edit Output
to save ONLY the synthetic body fixture. Native output explicitly showed pinned
data and no original headers. The pin survived navigation. Execute step on
Validate case event returned one item containing exactly the fake event_id and
lease_token. No listener/private prompt, Supabase callback or SMTP node ran.
This proves valid local shape and projection, not a genuine Supabase lease.
Evidence is saved under results/n8n-hands-on-20261025/synthetic-validation*.

Next practical lesson is the simulated local callback/effect ledger and mail
sink. Keep the workflow unpublished and production automation OFF. No new key
or repeated malformed probe is needed.

## Reference: sanitized synthetic input procedure (completed)

Use deployment/n8n/fixtures/validation-event.json, which reuses public fake IDs
from the existing isolated test harness. Open Authenticated case event OUTPUT,
choose JSON then Edit output. REPLACE THE ENTIRE editor contents with that fixture
and Save; n8n pins edited output for manual development. Never pin/export the
original webhook headers. Confirm the saved sample has ONLY body, no headers.
Do not publish/execute the whole workflow. Later execute ONLY Validate to inspect
the two projected fake IDs. This validates local shape/flow, not a genuine cloud
lease or Supabase permission. No secret, new key or model call is needed.
[Official pin/edit documentation](https://docs.n8n.io/build/work-with-data/pin-and-mock-data.md).

## Earlier private test procedure (historical diagnostic reference)

Live waiting-mode result:10no-key checks, ONE credential submission,403rejected.
Registration timing is resolved for this attempt; schema validation has NOT run.
Owner is correcting the credential selected on ORIGINAL QA webhook: Connection
Name=X-DefectRAG-CA-Key, Value=raw NEW local key without Bearer prefix. Credential
title is just a label. Save/close, then retry waiting-mode once; no new key or
production credential change. Scoped output is empty, consistent with rejection.

The manual Enter/listener timing produced repeated404 without testing a key.
Updated helper adds `--wait-for-listener` to malformed mode. Owner runs it in a
private terminal, enters the NEW LOCAL key and presses Enter normally. The helper
prints a waiting notice. Owner reports **Probe waiting**; only then the tester
arms Validate's partial Execute step. Helper automatically detects the registered
route using no-key checks, then submits the credentialed malformed event ONCE.

Waiting is loopback-only, bounded180s/2s interval with<=3s requests, no keys sent
in readiness checks, no redirects/proxies. Unexpected or unprotected responses
stop; timeout sends zero credentials. No automatic retry of an authenticated
event. Nine focused local tests pass. Correct-key/schema behavior still needs
the real node output; HTTP500 alone is insufficient. All production remains OFF.

24 October 2026. Existing editor: http://localhost:5678/. Existing published
workflow **Smart Task Prioritize** stays unchanged. Supabase case automation is
FALSE; the production corrective-action bridge is not deployed. Developer emails
use their existing separate cloud worker and must not be duplicated through n8n.

Native Supabase case/security tests passed within the recorded test scope. Owner
confirmed the independently audited approval was the additional Staff B account;
membership drift is reconciled. No agent account-approval action. No workflow has
been executed by this lesson. Owner has now imported the separate inactive draft
and renamed it **DefectRAG CA - LOCAL QA ONLY**; all nine nodes verified in browser.
Evidence: results/n8n-hands-on-20261024/inactive-import.png. Credentials still
unconfigured, callback URLs still placeholders, Publish disabled. Progress one
lesson at a time. Dedicated native Supabase QA sessions have been locally signed
out and the temporary console closed after live tests finished.

## Lesson 1: import and inspect an inactive copy

After membership-change reconciliation:

1. In Overview choose **Create workflow**. Do not open/edit the existing workflow.
2. In the new editor's workflow menu choose **Import from File** and select
   `C:\Users\User\Desktop\DefectRAG-v2\deployment\n8n\corrective-actions.json`.
3. Rename the new copy **DefectRAG CA — LOCAL QA ONLY** and save it. Leave it
   unpublished/inactive. Do not choose Execute, Listen for test event or Publish.

Expected: nine connected nodes with one IF branch. Missing-credential warnings
are expected at this stage; do not attach existing Gmail or other real mail
credentials to silence them. The template contains placeholders, not secrets.
Do not import the scheduler template yet. Report that the canvas is ready.

The flow is: authenticated event -> validate the small event envelope -> reserve
one notification effect -> IF execution is needed -> notify supervisor -> check
acceptance -> record receipt -> require durable completion -> webhook response.
The false IF branch checks completion without resending the notification.
Import alone does not call Supabase, run a model, approve an account or send mail.

## Lesson 2: separate the local test webhook path — verified

Double-click **Authenticated case event**. Change only **Path** to
`defectrag-ca-local-qa`, leaving HTTP Method POST and Authentication Header Auth.
Do not choose credentials or start the test listener yet. Report the path is set;
verify the actual node panel before teaching its next setting. This is a local
draft edit, not production configuration. The webhook is the entry point; Header
Auth will later check a purpose-specific inbound credential before accepting an
event. No credential was created during import.

Owner set the path; browser verifies POST/Header Auth and response-node mode.

## Lesson 3: private local credential and authentication boundary — in progress

Owner privately created a fresh Header Auth credential and selected it. Agent
observed selection only; the value was never read/exported. Intended header Name
is `X-DefectRAG-CA-Key`, with a NEW random secret of at least32characters kept by
the owner, separate from all production/Supabase/Resend credentials.

Actual no-header and wrong-header probes each returned403/PASS with no trigger
output. One request per case; no real secret or valid event was submitted.
Owner then stopped the listener and used **Execute step** on Validate case event;
browser confirms partial execution waiting for the preceding Webhook input. This
isolates the next test to two nodes, before callback/SMTP. See
[n8n partial executions](https://docs.n8n.io/build/understand-workflows/understand-executions/types-of-executions.md).
Now malformed mode uses a privately prompted local secret; confirm the
Validate node rejects missing event fields before any HTTP callback or SMTP node.
HTTP500 alone does not prove the intended validation rejection.

`deployment/n8n/probe_local_hook.py` disables proxies and redirects and hardcodes
the loopback-only test URL. It never supplies valid event IDs or capabilities,
and never reads/logs response bodies or secret headers. It makes one request per
invocation and has no retry loop. A404 means the temporary listener is not armed;
it is not an authentication pass. Native installed n8n Header Auth uses403 for
both missing and wrong credentials. Three focused probe security tests pass,
including control-character rejection and secret redaction. The owner has the
Desktop PowerShell command for malformed mode; correct-key/schema result is still
pending. Do not read or share webhook input headers; only status JSON and the
validation error are needed. HTTP500 alone does not establish the right rejection.

First privately submitted malformed probe returned404; browser validation output
remains empty. The temporary test webhook expired/was not registered, so key
correctness and validation have NOT been verified. Updated probe reports this as
test_webhook_not_registered/authentication not tested, without automatic retries.
Clarify the password-manager entry is the NEW local Header Auth Value, not the
old Supabase notification worker secret. Re-arm Validate's Execute step only when
the key is ready, then run the private command immediately; do not wait for chat
between arming and submission. No production credential reset is needed for404.

Owner reported using the older Supabase/worker password-manager value at the
private prompt. Before retry, replace ONLY the local QA Header Auth Value with a
fresh32-byte random key generated privately and copied to clipboard without
printing. Store it separately in Edge: website http://localhost:5678, username
DefectRAG-CA-LOCAL, password=new key. The username labels the key; it is not the n8n
owner login. Keep existing worker entry and production secrets unchanged. Owner
enters/saves the local replacement privately, closes the dialog and confirms.
Agent must never read the clipboard, credential Value or webhook input headers.

Owner confirmed the separate local key replacement. A different imported draft
was open; returned to ORIGINAL DefectRAG CA - LOCAL QA ONLY (RROoU7Cf31FpC5rS),
verified its saved POST/Header Auth/path and opened Validate. Other draft untouched.
For retry: copy NEW local key first, click Validate's Execute step, immediately run
private malformed probe, then report status JSON/exact error. Do not wait for a
chat reply after arming. Correct-key/schema tests remain pending until actual
output establishes the rejection; expiry/wrong-draft404 does not test credentials.

Second private attempt also returned404. Agent immediately armed the ORIGINAL
QA Validate partial execution and sent one no-key diagnostic:403/PASS, proving
that exact partial run can register the route. Stopped the diagnostic wait.
Use improved order: FIRST start the private terminal prompt and paste the NEW
local key WITHOUT pressing Enter; report prompt ready. THEN arm the partial run,
and only then press Enter. This removes key-retrieval delay from the listener's
short lifetime. Do not repeat earlier auth tests or change the production key.

## Later lessons — not executed or verified yet

- Inspect trigger/validation input and output using synthetic event IDs.
- Configure purpose-specific inbound and callback credentials privately. n8n
  never receives a Supabase privileged key. No credential is entered in chat.
- Use a local test mailbox/sink, never real recipient delivery, for first runs.
- Verify the IF branch, errors, retries, duplicate suppression and ambiguous
  acceptance against the effect ledger. SMTP acceptance is not inbox delivery.
- Verify real Supabase callback boundaries using a separately approved, bounded
  QA plan. With database automation FALSE, positive lease/effect delivery is
  intentionally unavailable; do not toggle the global gate as a test shortcut or
  consume unrelated queued events. A simulated callback is not a live RPC pass.
- Save/export the tested inactive workflow, then rehearse local restart/recovery.

Supabase Edge cannot reach Windows localhost. A deliberate authenticated local
bridge/manual dispatch design is required; no public tunnel is authorized.
Production deployment, scheduler activation, real sends and reliable online
hosting remain separate decisions. Local Docker stops with the laptop; it does
not establish laptop-off availability for corrective-action automation.
