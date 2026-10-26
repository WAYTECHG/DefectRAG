# Phase 2 — verified 18 October 2026

Phase 2 live inspection passed locally and in `Wizzas/DefectRAG` cloud commit
`3784513453133497d4249a00f7daa32571a3bfef`. Continue authorized Phases 3–5; this
checkpoint does not claim their completion.

- All 12 existing DINOv2 highres category banks loaded with SHA256 checks. Same
  frozen encoder, preprocessing, PCA foreground rule, scoring, calibration and
  heatmap restoration. No fitting, threshold changes or accuracy benchmark rerun.
- Real arbitrary valid uploads replace the Phase 1 fixture-only restriction.
  Existing JPEG/PNG/WebP and 10 MB/25 MP limits remain; aspect ratio is bounded to
  4:1 for scheduled work. GPU jobs request at most 20 seconds. Sequential batch
  transport preserves per-file errors and accepts up to 20 images with a label.
- Exactly one normal and anomalous resized public sample per category passed
  locally and in cloud (24 each). This is a functionality/parity smoke test,
  not a claim that every benchmark anomalous input is correctly detected.
- All 24 local/cloud verdicts agree; largest absolute score difference is
  0.00052985549, below the declared 0.002 tolerance. Peak tracked allocations:
  local 621.88 MB, cloud 612.47 MB; neither is total process/GPU memory.
- Example limitations remain: the resized macaroni1, macaroni2 and pcb2 anomalous
  previews received Good verdicts. Conservative thresholds/preview resizing can
  miss anomalies. Existing all12 benchmark metrics and thresholds are unchanged.
- Other browser session histories are empty; foreign record reads return 404;
  unsigned image access returns 401. Image/report URLs have one-hour HMAC
  capabilities. Anonymous SQLite/artifacts are temporary, not durable staff data.
- CSS remains byte-identical to the production dashboard. The build changes only
  transport, signed report links and cloud/privacy wording. Original dist,
  dist-static and React/CSS sources are preserved.
- Per-job Gradio clients are disposed instead of retaining idle queued sessions;
  expected AbortError during disposal is distinguished from actual errors.
  Gradio's optional SSR proxy is disabled for the existing static React build.
  Captured post-test cloud log contains zero missing-session/response-started
  errors. Invalid image and quota rejection traces are expected negative tests.
  Long-duration load/reconnect testing remains future hardening.
- Guest testing hit its run limit after seven successful cases. The verifier
  saved those cases, verified that the existing account is regular/free, and
  resumed only the remaining cases using its free allowance. No paid operations.
- Hub 1.31.0 is verified installed in cloud and satisfies both Transformers
  >=1.31 and the platform datasets<2 requirement. Original local production
  dependencies remain unchanged. Python3.12.12/Torch2.8/Gradio6.30/spaces0.51.3.

Sanitized evidence: docs/zerogpu_phase2/vision-summary.json. Private resumable
reports (including anonymous workspace access tokens), detailed logs and deployment
receipts remain Git-ignored under development-support/space. Never publish the
full private reports; they include image/report capabilities.

Phase 3 local live retrieval/Ollama generation/citations/history/abstention passed
using saved Phase 2 records. Cloud Qwen loading and generation are next, unverified
at this checkpoint. Qwen weights will download only in the Space.

Phase 4 implementation is being prepared against existing public Supabase config.
Anonymous table reads were rejected, but authenticated RLS is not yet verified.
The additive conversation/acknowledgement SQL was reviewed and approved for the
user to execute manually. **Do not execute SQL or directly alter their database.**
Wait for their successful-execution confirmation before RPC tests. The user can
sign in to an approved staff account when ready; no password should be requested.

Future hardening recorded at the user's request:

1. Approved staff can directly submit conversation content; stored answers do
   not have a server/model provenance attestation.
2. Alert acknowledgement stores a boolean without the acknowledging user or
   timestamp. Current migration intentionally preserves that reviewed scope.

Next: bounded cloud Qwen validation, existing-app regression checks, phase3 Git
checkpoint, then user-confirmed migration/staff login and RPC authorization tests.
