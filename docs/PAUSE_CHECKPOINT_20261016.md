# DefectRAG v2 — PAUSED development checkpoint

**16 October 2026, Asia/Kuala_Lumpur. Paused at the user's explicit request.**
Do not start servers, installs, tests, training or development until the user asks to resume.

## Resume from these files, not from scratch

Primary working source:
`C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2`

Desktop copy synchronized for this pause:
`C:\Users\User\Desktop\DefectRAG-v2`

The previous checkpoint ZIP remains unchanged. A new timestamped development
checkpoint ZIP, SHA256 receipt, source manifest and code-only Git checkpoint are
created for this pause. See `development-support/git/receipt.json` for the exact
commit hash and code-bundle path. The pause ZIP is not the final accepted release.
Git excludes model weights, banks, dataset, runtime history, package overlays,
frontend build and secrets; these remain saved locally outside Git.

Read this file first on resume. The older progress document is retained as
`docs/DEVELOPMENT_PROGRESS.previous.md`; its unfinished RAG status is superseded.

## Completed and preserved

- Frozen DINOv3 ViT-S/16 + fitted nearest-normal patch banks for PCB1, capsules,
  cashew. Encoder/embedding assets, bank files, model cards, checksums and all
  original split/prediction/evaluation JSON remain saved. **No refitting or model
  experiments were restarted during this resume.**
- FastAPI inspection, heatmaps, image validation, batch execution, SQLite history,
  filtered queries, local alerts, printable reports and CSV export.
- React + Vite dashboard and its already-built `frontend/dist`. No frontend
  dependency installation or build was repeated during this resume.
- LangChain loading/chunking/BGE retrieval and LangGraph evidence workflow.
- Fixed Qwen's missing-quote failure by passing a Pydantic JSON schema to Ollama.
  Validated source IDs and exact quote checks remain enforced. Added rejection of
  invented numeric facts, visible fallback reasons, malformed-response handling,
  a concise paraphrase prompt and citation-tag cleanup.
- Knowledge index compatibility now fingerprints the embedding weights/config,
  tokenizer and corpus. Its five-passage index was regenerated for this necessary
  compatibility change. Missing embedding assets do not prevent dashboard startup.
- User/assistant messages are saved in a single SQLite transaction. Inspection
  reports now include retrieved source text, source URLs and scope.
- Live acceptance now reuses the six existing real-image records and saves partial
  results on failure. No duplicate six-image acceptance batch was created.
- Saved diagnostic/check scripts and `scripts/profile_inference.py`. The profiling
  script has **not been run**.
- Optional Anomalib experiment has explicit layer/fusion groups. It remains
  **unverified and unexecuted**; do not train it merely to resume.
- Upstream BGE license downloaded to `models/BGE-LICENSE.txt`; DINOv3 license
  remains in `models/DINOV3-LICENSE.md`. Final attribution inventory is unfinished.

## Actual verification results

**23 software tests passed**, no failures, one upstream Starlette/AnyIO deprecation
warning. Authoritative report: `results/software-tests.xml`. Synthetic fixtures
are limited to software checks and are not model-performance evidence.

**Live HTTP acceptance passed**: `results/acceptance.json`.

- Six saved original VisA predictions, two per category, were reused and checked
  against frozen evaluation scores (absolute tolerance 1e-5).
- Saved input/heatmap access, record retrieval, batch filtering, report serving,
  relevant BGE retrieval, conversation persistence, alerts and invalid-upload
  rejection passed.
- Two actual Qwen answers passed source-ID and exact-quote validation.
- A root-cause question correctly abstained.
- Earlier raw missing-quote diagnostic: `results/rag_diagnostic.json`.
- Intermediate live generation trace: `results/rag_live.json`.

Real browser interaction also completed: sample selection, running an actual PCB
prediction, measured anomaly display, heatmap/original toggles, linked assistant
request and a visible `LOCAL LLM · CITED` answer. The resulting local inspection
ID is `7732bca0cede4431b212a15858795cd0`; its source/heatmap/history are preserved
in the runtime backup. Full mobile/history/alert UI QA remains unfinished.

### Known correctness issue found immediately before pause

For the browser question “What does the heatmap show?”, retrieval included the
general **Dinomaly reconstruction** document and Qwen paraphrased it as feature
reconstruction. The shipped detector actually uses **nearest-normal cosine patch
distance**. The quote is real, but document applicability to the current detector
needs tightening. This issue has **not been fixed yet**.

Next change: in `EvidenceWorkflow.validate_evidence`, exclude Dinomaly-specific
mechanism passages for questions about the current detector unless the user
explicitly asks about Dinomaly/reconstruction/comparison. Retrieve/use the project
screening policy for current heatmap explanations. Add a meaningful scope
regression, verify a real heatmap answer, and retain separate image measurements.
Citation validity alone does not prove semantic correctness. Do not call the
application fully accepted until this is addressed.

## Frozen measured model performance

| Product | Final images | Image AUROC | AP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.896625 | 0.866319 | 0.779070 | 0.837500 | 0.807229 |
| Capsules | 140 | 0.825000 | 0.888730 | 0.838235 | 0.712500 | 0.770270 |
| Cashew | 130 | 0.970500 | 0.983017 | 1.000000 | 0.700000 | 0.823529 |

Seed 42; 64 official training normals fit each bank, 32 different training normals
+ 20 official test anomalies calibrate its threshold; remaining official test
identities form the final evaluation. Content-hash separation is checked.
This modified protocol is **not the full official VisA benchmark**.
The ±5% review band is an operational heuristic, not calibrated confidence.
Capsule localization is weak (pixel AP about 0.045). No named defect classifier,
factory acceptance guarantee, root-cause diagnosis or process tolerance is supported.

Do not rerun fitting or tune against final test labels. Existing timing values
came from overlapping earlier runs; one clean serving profile is still required.
GPU memory reports are PyTorch allocated peak, not total device/process memory.
No profile was started during the pause preparation.

## Process state and hibernation

`results/pause_processes.json` records the actual process inventory and stop
actions. The new app's test servers on 8765/8766 were targeted by their exact
module/port command. No matching owned server or installer remained after pause.
The Python 3.11 overlay installer finished successfully before the pause check.

- **No DefectRAG v2 training, fitting, evaluation, generation, installation or
  background development job is left running after checkpoint completion.**
- Shared Ollama is deliberately left running; no new generation is requested.
  Original-project processes and unrelated services are left untouched.
- No training needs in-memory continuation. Saved weights/banks and test results
  are sufficient. After hibernation, start one v2 server when explicitly resuming;
  do not rely on old process IDs, tool-session IDs or open browser connections.
- SQLite is preserved with its online backup API, with saved inspection artifacts
  under `development-support/saved-runtime/`. Do not overwrite a newer runtime
  database with this backup.

## Python environments — preserve both

Verified development runtime is read-only:
`C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe`
(Python 3.12.4, torch 2.8.0+cu126, transformers 4.57.6).

Its small additional LangChain overlay remains at:
`C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\.test-deps`
and is copied into `development-support/langchain-overlay/` for offline recovery.
Do not install into the original project's environment.

An existing Python 3.11.15 Conda runtime was found at:
`C:\Users\User\anaconda3\envs\defectrag\python.exe`
with torch 2.5.1+cu121, torchvision 0.20.1+cu121 and sentence-transformers 5.7.0.
Its initial import failed because existing transformers 5.15.0 required
huggingface-hub <2 while that environment had hub 2.0.0.

Compatible Transformers 4.57.6 and LangChain/LangGraph dependencies were therefore
installed **only into this isolated folder**, leaving Conda files unchanged:
`C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\.test-deps311`

That install completed with exit 0. Application imports/inference have **not yet
been retried** on 3.11. Pip warned about pre-existing optional TensorFlow dependency
conflicts, including NumPy <2 vs overlay NumPy 2.4.6. This app uses PyTorch; on resume
consider `USE_TF=0` for the isolated check. Do not claim clean Python 3.11 acceptance.
Do not redownload/reinstall the completed overlay unless a concrete failure requires
it. The overlay remains saved at the above local path; it is not a release asset.

## Exact next steps AFTER the user asks to resume

1. Inspect Git status and this progress file. Reconcile any Desktop/source edits.
2. Fix the document-applicability issue described above; do not repeat model fitting.
3. Start one server using the verified environment, then verify the corrected
   real heatmap answer. Reuse saved records for remaining acceptance checks.
4. Finish browser follow-up, report, history filters, alerts, batch input and mobile
   viewport QA. Capture final screenshots; no screenshots were saved as local
   deliverables yet.
5. Run the already-written bounded serving profile once. Verify launcher startup,
   CPU inference and Python 3.11 compatibility using existing assets/overlays.
   Docker remains configured but untested.
6. Finish concise README, architecture diagram, portfolio description,
   third-party notices and final test report.
7. Create and test final `DefectRAG-v2.zip`, excluding secrets, dataset, live
   runtime/history, package overlays, node_modules, caches and Git objects.
   **The final release ZIP does not exist yet.**

PowerShell, only AFTER explicit resume:

```powershell
Set-Location 'C:\Users\User\Desktop\DefectRAG-v2'
$env:PYTHONPATH = Join-Path $PWD 'development-support\langchain-overlay'
$devPython = 'C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe'
# Confirm the desired port is free; start only one instance.
& $devPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8766
```

Use the workspace primary path instead if continuing there. Runtime test history
is still in the workspace `runtime/`. The checkpoint's independent SQLite backup
is under `development-support/saved-runtime/`. To restore into a new runtime,
copy that folder to `runtime/` only if no runtime database already exists.

Dataset is already local:
`C:\Users\User\Downloads\VisA_20220922`.
No download is necessary. Qwen model: `qwen2.5:3b` on local Ollama port 11434.

## Local Git recovery

The new application has its own code-only Git repository; the original project's
Git history is untouched. The pause commit is on `main`. Use `git log -1` to see
it; the exact hash is also in `development-support/git/receipt.json`.
The code bundle preserves the commit independently of the working directory:

```powershell
git bundle verify .\development-support\git\DefectRAG-v2-code.bundle
# Recovery into a NEW, empty directory only:
git clone .\development-support\git\DefectRAG-v2-code.bundle C:\path\to\new-code-recovery
```

Git restores code/configuration/results; recover weights, samples, index and
runtime artifacts from the development checkpoint ZIP or existing asset folders.
Never reset or overwrite a newer working directory to resume.

## Preservation and authorization

Original `DefectRAG-Verified`, VisA files, existing models/caches and synced
`sources/` are preserved. No public deployment, cloud creation, paid service,
notification or extended GPU training was started. Ask before major downloads,
extended training, destruction, paid services or public release. Stay paused until
the user explicitly requests continuation.
