# Phase 1 results — 18 October 2026 (Malaysia)

**Status: core compatibility proof passed with follow-up issues; stopped after Phase 1. Phase 2 requires
user approval.** Cloud request timestamp: 17 October 2026 16:12:35 UTC.

The existing React dashboard was served by `gradio.Server` locally and in the
previously empty `Wizzas/DefectRAG` Gradio ZeroGPU Space. One genuine browser
inspection was run in each environment through `@gradio/client`. No training,
benchmark rerun, RAG migration, Qwen download or Supabase schema change occurred.

Test Space: https://huggingface.co/spaces/Wizzas/DefectRAG
Direct app: https://wizzas-defectrag.hf.space
Final cloud source commit: `84df9af3f59b2fe43fdb6ad14a1820c930329abc`.
The separate running `Wizzas/defectrag-inference` Space was not modified.

## Acceptance evidence

| Requirement | Observed result |
|---|---|
| Preserve React appearance | Original components, CSS, colors, layout and navigation sources unchanged. Local and cloud served CSS matches the production CSS byte for byte. Screenshot captured. |
| Navigation and primary controls | All nine other local page headings verified; local comparison slider changed to 65%, zoom to 125% and back to 100%. Existing report, images, history, evaluation, benchmark and CSV routes returned HTTP 200 locally and in cloud. |
| React calls Gradio | Isolated Vite transform changes only the inspection transport plus one test caption. JS client 2.7.1 invokes queued `/inspect`. Direct REST `/api/inspect` returns 409, preventing a legacy API fallback. |
| Image upload | Browser file chooser uploaded the actual public PCB1 JPEG locally. Cloud selected the same public sample into the existing input and sent its bytes through the JS client. |
| Genuine DINOv2 output | Existing frozen encoder and normal bank produced anomaly score, verdict and newly rendered 32 x 41-grid heatmap. Neither request used cached predictions. |
| Actual ZeroGPU | Cloud readiness and result both reported ZeroGPU=true, CUDA and the actual Blackwell MIG device. Scheduled `spaces.GPU(duration=30)` returned CPU data for persistence/rendering. |
| Preservation | No changes to existing backend/frontend source, model weights, thresholds, datasets, evaluation files, production dependencies, static showcase or Supabase settings. All new implementation is under deployment/zerogpu_phase1. |

CSS: `assets/index-Bn4HF2vD.css`, SHA256
`087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661`.
Responsive CSS and existing transitions remain intact; a full mobile/browser
matrix was not performed. No TSX/React component source was edited.

## Single-fixture measurements

| Measurement | Local Windows | HF ZeroGPU Linux |
|---|---|---|
| Product/input | pcb1_anomalous.jpg | Same public JPEG |
| Model | dinov2-highres-pcb1-v1 | Same encoder/bank |
| Inspection ID | b01ad894f1c6490ead703e3793c52539 | a976ff7df0cf4da9beab53582d54c477 |
| Device | RTX 4060 Laptop GPU | RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb |
| Score | 0.31308862566947937 | 0.31300604343414307 |
| Threshold | 0.16181933879852295 | Unchanged |
| Review margin | 0.008090966939926147 | Unchanged |
| Verdict | Anomalous | Anomalous |
| Measured compute | 1188.57 ms | 783.16 ms |
| Model orchestration/render time | 1224.58 ms | 1606.69 ms |
| Peak tracked PyTorch allocation | 113.71 MB | 120.99 MB |

Absolute score difference: **0.00008258223533630371**, within the predeclared
single-fixture absolute tolerance 0.001. This is limited numerical agreement,
not all-category parity, AUROC, throughput or end-to-end queue latency evidence.
Times are one observation, not a performance guarantee. Peak allocation excludes
other CUDA/context/process memory.

Bank SHA256: `14e71cb6285f22e3d12d2b0d6357c552a26685a8f03a9b626a3e8999e8a89c65`.
Encoder SHA256: `ae1e99fcefd534ed978cdeb8326f08030c96e28b7a81ffcbc98a857c84d14be1`.

## Versions and diagnosed compatibility issues

| Package/runtime | Local isolated proof | Observed cloud |
|---|---|---|
| Python | 3.12.4 | 3.12.12 |
| PyTorch | 2.8.0+cu126 (existing install) | 2.8.0 (ZeroGPU-managed) |
| Gradio / spaces | 6.30.0 / 0.51.3 | Same |
| Transformers | 5.20.1 | Same |
| Hugging Face Hub | 2.2.0 | Same |
| FastAPI | 0.142.2 | Same |
| Browser @gradio/client | 2.7.1 | Same compiled build |

1. Original Transformers 4.57.6 requires Hub <1; Gradio 6.30.0 requires Hub
   >=1.16. A separate small environment uses Transformers 5.20.1/Hub 2.2.0.
   The production Windows environment retains its original versions.
2. HF rejected `torch==2.8.0+cu128` before building, listing 2.8.0 as supported.
   One narrow requirements correction to `torch==2.8.0` (and torchvision 0.23.0)
   with the CUDA 12.8 extra index resolved CONFIG_ERROR. No architecture change.
3. Cloud pip warned that its preinstalled, unused `datasets==5.0.0` requires
   Hub <2. The proof does not import datasets and executed successfully. This
   dependency warning remains a cleanup item before a broader migration; do not
   claim that the whole preinstalled image passes pip check.
4. Vite required the isolated source transform to run before esbuild (`enforce:
   pre`). Node-only client branches were externalized; the actual browser request
   passed. Original package manifests and lockfile were not edited.
5. After successful result delivery, the cloud log contains three Gradio SSE
   errors: `HTTPException: 404: Not Found`, then `Caught handled exception, but
   response already started`. Inspection of installed Gradio routes.py:1837
   identifies the immediate condition: the stream's session hash is absent from
   `pending_messages_per_session`. Whether this came from client reconnect,
   cleanup or proxy timing is not established. The delivered GPU result and
   subsequent HTTP checks passed; stream/session lifecycle still needs a bounded
   diagnosis before production migration. No framework patch or speculative
   dependency change was attempted to hide the errors.

Official constraints: [HF ZeroGPU documentation](https://huggingface.co/docs/hub/spaces-zerogpu),
[Gradio Server mode](https://gradio.app/guides/server-mode).

## Important limits

- The public test accepts **only byte-identical pcb1_anomalous.jpg**. Only its
  bank is deployed. All 12 existing category cards/results remain viewable as
  historical evidence; this does not enable all 12 cloud inspection categories.
- RAG and batch submissions return an explicit Phase 1 error. Their existing UI
  remains visible. No Qwen model or embedding model was published/downloaded.
- Cloud config deliberately has blank Supabase settings. Existing Desktop public
  and built configs and production database remain unchanged. No staff sign-in,
  cloud writes, schema changes or RLS verification were performed.
- Only public fixture data enters an isolated ephemeral SQLite history. It is not
  suitable for private uploads or durable multi-staff production history.
- The direct hf.space **guest browser** path worked. Authenticated HF iframe
  quota identity, dual HF/Supabase authentication, cancellation, quota exhaustion,
  concurrent users, cold restart and mobile layouts were not acceptance-tested.
- Existing local/private-runtime labels remain visible except the inspection test
  caption. Space README explains the scope; this is not a complete public release.
- DINOv3 was preserved and not deployed/executed in Phase 1.

## Saved artifacts, processes and exact resume point

Saved under `development-support/zerogpu-phase1`: local-verification.json,
cloud-verification.json, navigation.json, dependency plans/install report,
space-upload.json, space-config-correction.json, space-runtime.json, build/run
logs, local-inspection.png, cloud-inspection.png, isolated venv, compiled UI and
the allowlisted payload. The new local inspection/database/artifacts are under
`runtime/zerogpu-phase1`. Small public verification records are also copied into
`docs/zerogpu_phase1/`; cloud screenshot is in docs/screenshots.

The owned local adapter on port 8783 was stopped after testing. No training,
benchmark or background model request remains. The HF compatibility Space remains
hosted and idle between requests; it can sleep/restart and its test history may
disappear. No other user server or Ollama process was stopped.

To resume: first inspect Git status and these saved reports. See
`deployment/zerogpu_phase1/README.md` for the already-installed local launch and
read-only cloud status commands. Do not repeat successful GPU requests, installs,
training or benchmark work just to resume. Do not rerun the initial publisher.

**STOP. Next work requires Phase 2 approval.** Proposed next gate is bounded
vision migration: diagnose SSE session cleanup, resolve the unused datasets/Hub warning, verify HF iframe quota
identity and restart lifecycle, then adapt the remaining existing category banks
with a small approved parity sample. RAG generation and durable Supabase backend
remain later, separately approved work. No new model training is justified here.
