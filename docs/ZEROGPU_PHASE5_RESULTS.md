# Phase 5 deployed integration — 18 October 2026

Public application: https://huggingface.co/spaces/Wizzas/DefectRAG

Final deployed commit: 3717008401fcf9c85612ce6d4c0c77b629c39f53.
Runtime verified RUNNING, existing free zero-a10g selection retained. Actual
allocation is Blackwell MIG48GB. Existing React/CSS, model weights, calibrations,
benchmark metrics, original local app and static showcase preserved. No training,
new dependency installation, paid service or destructive database operation.

## Verified flow

| Boundary | Evidence |
|---|---|
| Public dashboard → CPU API |13 boundary checks passed; exact original CSS SHA256,12 model categories, evaluation/benchmark/samples200, enabled staff persistence flag |
| Access protection | Missing workspace401; invalid staff credential403. Both anonymous Supabase RPCs401/42501 |
| Browser → DINOv2 → Supabase | Real PCB1 inspection a6351615259d42868b766a004f5dd303 saved, scored and displayed with private heatmap; see Phase4 results |
| Inspection → retrieval → Qwen → RPC | Saved measurement answer, genuine cited heatmap answer, then new contextual Qwen answer after deployment restart; six conversation turns returned after reopening |
| Staff notes/acknowledgment | Exact review note and acknowledged state persisted after reload; report confirmed Supabase storage and acknowledgment |
| History/recovery | Owned fixture archived and developer-restored; measurements, images, conversation and note retained |
| Actual process restart | Original staff record and prior four conversation turns/note survived Space rebuild; no re-inference or record recreation |
| Reports/export/private images | Signed report/CSV200 and both signed Supabase image URLs200; report includes actual conversation and retrieved documentation |
| Quota handling | Real guest rejection displayed. New scheduler stopped further submissions and preserved prior successful inspections; no automatic retry |
| Authenticated HF + staff batch history | Both Capsule images processed under PHASE5-STAFF-BATCH and returned by the other staff session's signed CSV: Good0.13208820 and Uncertain0.20549749. User submitted successive one-image runs; latest run1 completed/0 failed |
| Software/build | Existing44 regressions and9 security tests previously passed. Focused batch scheduler check and latest production build passed; CSS unchanged |

Independent pages/navigation already passed locally and in cloud during the saved
checkpoint; they were not rebuilt or exhaustively retested without a change.
Six saved conversation turns mean three user questions and three assistant turns.
Generated-answer validation includes cited retrieved quotes and saved measurement
context; it is not proof of diagnosis, process acceptance or complete entailment.

## Quota/stability investigation

The final direct-browser two-image staff batch was rejected on its first image
because guest ZeroGPU allowance was exhausted; the second was correctly **not
submitted**. No new inspection row or successful prediction was reported for it.
The earlier historical batch had one success and one quota failure. These are
different test runs and neither is a fully passed two-image batch.

After the user signed in to HF as the verified regular FREE Wizzas account and
to Supabase staff inside the iframe, both previously unfinished Capsule images
were processed and durably saved. IDs88b2489b5759419a9caad724ade0ae53 and
ee823f7db3ae4a8fb687bb7b4d50896c; inference687.53ms and803.74ms. The independent
direct staff session's signed CSV returned both records, confirming shared
persistence across these two isolated browser sessions of the same account.
These were successive one-image runs under one batch label; do not claim a
successful single-click two-file run. No successful model case was re-inferred.
Embedded upload automation failed to catch the file chooser; the user completed
the upload. This was a test-tool limitation, not a model/data replacement.

Hugging Face documents2 minutes for unauthenticated callers and5 minutes for free
accounts, reset24 hours after first GPU use. Supabase identifies staff/database
access; HF identity controls GPU allowance. The official client supports HF iframe
identity headers. Open the hosted Space while signed in to HF for available free
account quota. Do not embed an owner token in public frontend code or route every
visitor through the owner's token. No subscription/credit purchase was made.
[Official ZeroGPU quotas](https://huggingface.co/docs/hub/spaces-zerogpu#usage-tiers).

Short20-second vision/45-second text leases, one shared model-work queue, fresh
per-job clients and SSR/run-history disabled remain. CPU retrieval uses the
verified child process. No speculative lease reduction, quantization, dependency
change or broad performance experiment. Startup/interaction logs are bounded
observations; long-duration load, concurrency and repeated cold starts are not
certified. Free capacity, queues and quotas prevent an unlimited-availability claim.

## Deployment readiness and residual acceptance

Core application is deployed and the approved developer path is end-to-end
verified. This is suitable for a public portfolio/demo with the documented free
quota, benchmark scope and access limitations. It is not certified for factory
acceptance or unrestricted multi-user production load.

- Authenticated nonstaff RPC denial cannot be live-tested without an existing
  nonstaff account. User confirms none exists; no account/allowlist changes made.
- Ordinary-staff versus developer ownership and distinct second-user collaboration
  need future account-based tests; software/schema review is not a substitute.
- Both images now passed actual free-account inference/storage in successive
  one-image runs. A successful combined two-file submission remains unverified;
  multi-file quota/error parsing and the scheduler's behavior are separately tested.
- Staff answers lack model provenance attestation; acknowledgments lack actor/time
  audit. Existing permissions were not expanded to hide these limitations.
- Anonymous history is temporary; only authenticated enabled Supabase records are
  durable. Statistics/list/archive/export bounds remain documented in Phase4.

Private evidence and signed capabilities stay under Git-ignored development-support/space.
Only sanitized JSON and screenshots are committed. No additional large model ZIP
or model copy is created. The local Git checkpoint and Desktop sync preserve code
and existing configuration without duplicating datasets/environments.

Final bounded log snapshot: RUNNING on the stated revision; captured queue-session,
response-already-started, CUDA initialization and CUDA OOM occurrences all0.
Quota rejection is documented from the client. Logs are not a full request trace
or long-running reliability certification. See zerogpu_phase5_final/stability-summary.json.
