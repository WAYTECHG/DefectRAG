# DefectRAG v2 — verified local release

Updated **16 October 2026**, Asia/Kuala_Lumpur. User-authorized continuation completed
the remaining implementation and local verification. No fitting, dataset download
or expensive experiment was repeated.

## Deliverables and authoritative completion records

- Source and assets: `C:\Users\User\Desktop\DefectRAG-v2`.
- Final release: `C:\Users\User\Desktop\DefectRAG-v2.zip`.
- ZIP verification/checksum: adjacent `DefectRAG-v2.receipt.json`.
- Desktop synchronization/recovery: `development-support/release_sync_receipt.json`.
- Current Git commit: `git log -1`; release manifest also records the commit.
- Primary working source remains
  `C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2`.

The build/synchronization receipts are authoritative for final handoff. If a
disconnect occurs during the final archive/copy step and a receipt is missing,
resume that step below; do not repeat completed fitting or verification.

## Completed

- Actual DINOv3 ViT-S/16 nearest-normal inference for PCB1, capsules and cashew;
  calibrated score, Good/Anomalous/Uncertain result and coarse heatmap.
- FastAPI, React + Vite, SQLite history, batch inspection/filtering, local review
  alerts, printable reports and CSV export.
- LangChain source loading, chunking, local BGE retrieval and persistent index;
  LangGraph scope/retrieval/evidence/generation/validation/fallback workflow.
- Genuine local Qwen explanations and follow-ups. The model selects a source
  sentence by ID and writes its explanation; the application attaches the original
  quote and source ID, then validates citation/number consistency. No generated
  explanation is represented as a deterministic template.
- Fixed wrong-method evidence: current-detector questions exclude Dinomaly
  reconstruction passages. Follow-up retrieval uses the prior user topic, and
  stale assistant facts are excluded after knowledge changes.
- Completed README, architecture diagram, portfolio description, licenses/notices,
  frontend production build, verification report and desktop screenshots.
- ZIP packager verifies CRC, all file hashes, duplicate entries and required assets.
  Dataset, secrets, runtime history/uploads, dependency overlays, node_modules,
  caches and Git objects are excluded from the release.

## Verified results

**29 software tests passed**, no failures, one upstream AnyIO deprecation warning:
`results/software-tests.xml`.

**Extracted release candidate passed on Python 3.11.15**:
`results/release_extraction_verification.json`. Imports were confirmed to come
from a new extraction. It served the frontend, uploaded a real VisA image, loaded
the bundled model, produced a real score/heatmap, saved/retrieved the record, used
bundled knowledge/embeddings with a genuine Qwen answer, and served report/CSV.
The final archive has the same runtime/frontend/model assets, plus final reports
and release utilities.

Other authoritative results:
- `results/acceptance.json`: six original predictions, source retrieval, genuine
  generation, follow-up persistence, batch filtering, reports, alerts and failures.
- `results/evidence_scope_verification.json`: real current-method explanation and
  genuine follow-up after the final source-sentence contract.
- `results/browser_verification.json`: two real uploaded images completed,
  Good/Anomalous displays, combined history filters, alert acknowledgement, report
  images and cited answer rendered; no captured browser JavaScript errors.
- `results/startup_verification.json`: actual Windows launcher/model verification
  on Python 3.11.15 with torch 2.5.1+cu121 and transformers 4.57.6.
- `results/serving_profile.json`: one clean bounded GPU profile and CPU smoke.
- `results/preservation_verification.json`: 15 frozen model/evaluation artifacts
  match the pause-checkpoint hashes, including all weights, banks and final results.

## Frozen performance and scope

| Product | Final images | AUROC | AP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.896625 | 0.866319 | 0.779070 | 0.837500 | 0.807229 |
| Capsules | 140 | 0.825000 | 0.888730 | 0.838235 | 0.712500 | 0.770270 |
| Cashew | 130 | 0.970500 | 0.983017 | 1.000000 | 0.700000 | 0.823529 |

64 normal fit images/category; 32 distinct normal + 20 reassigned official test
anomalies calibrate max-F1 thresholds; remaining official test identities are
held out. This is a modified VisA protocol, not the full official benchmark.
±5% review band is heuristic, not calibrated confidence. Capsule localization
remains weak (pixel AP ~0.045). No named defects, counts, root causes, factory
tolerances or product-safety/acceptance guarantees are inferred.

Clean RTX 4060 model medians: **54.59 / 53.875 / 65.615 ms**; total
file/decode/inference/overlay medians about **173 / 159 / 230 ms**. PyTorch allocated
GPU peaks about **66 / 78 / 90 MB**, excluding driver, other processes and LLM.
CPU inference passed. Earlier frozen evaluation/timing records remain preserved.
The shipped method is frozen DINOv3 patch memory, **not Dinomaly**.

## Explicit remaining verification limitations

- Docker compose configuration passed; container execution unverified because the
  Docker daemon was unavailable.
- Responsive CSS is implemented, but mobile visual QA is unverified: the browser
  ignored the requested 390 px override and stayed at 1280 px, including in a new
  tab. The override was reset after testing.
- Python 3.11 verification reused the existing Conda runtime plus an isolated
  compatibility overlay. A clean dependency installation in a new venv was not run.
- Anomalib decoder training, browser ONNX/WebGPU export, Supabase, n8n and public
  deployment remain optional/future work; none was executed or provisioned.
- Quote/ID validation establishes traceability, not guaranteed semantic entailment.

These limitations are documented in the README and verification report. Do not
restart successful experiments to remove a documentation caveat.

## Start / continue without rebuilding

For ordinary standalone use, read README and run `Start-DefectRAG.cmd -Setup`
once in a compatible Python environment, then `Start-DefectRAG.cmd`.
The dashboard build, weights and knowledge index are already bundled.
Qwen is optional and separately installed through Ollama; no automatic LLM download.

Existing verified development runtime (unchanged):
`C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe`,
with `PYTHONPATH` set to the workspace sibling `.test-deps`.
Python 3.11 runtime:
`C:\Users\User\anaconda3\envs\defectrag\python.exe`,
with `PYTHONPATH` set to sibling `.test-deps311` and `USE_TF=0`.
Do not reinstall those completed overlays or change the original environments.

A development preview may still run at `http://127.0.0.1:8766`.
Its last startup reported PID **32284**; verify identity before stopping it.
Shared Ollama is at localhost:11434, `qwen2.5:3b`.
No fitting/training/benchmark jobs remain active.

If final packaging was interrupted:
1. Inspect Git status and the existing ZIP/receipt. Preserve any newer edits.
2. If the final ZIP does not exist, run `python -m scripts.package_release`.
   It refuses to overwrite an existing archive.
3. With source committed and the release bundle present, run
   `python -m scripts.sync_release` with Desktop write permission.
   It requires a clean Desktop tree and fast-forwards Git without rewriting history.
4. Check the generated receipts. Do not repeat the completed model evaluation.

The code-only release recovery bundle is
`development-support/git/DefectRAG-v2-release.bundle`.
Prior Git commits, code bundles and timestamped checkpoint ZIPs remain preserved.
Historical progress is under `docs/PAUSE_CHECKPOINT_20261016.md` (excluded from the
clean release archive).

## Preservation

The original `DefectRAG-Verified` source, Git history and installed dependencies
were not changed. Existing VisA data at
`C:\Users\User\Downloads\VisA_20220922` was read only.
All original model banks, weights, checkpoints and evaluation records remain.
The new app's development history stays in workspace `runtime/`; earlier safe
SQLite backups remain under `development-support/saved-runtime/`.
Never replace a newer database with an older backup. No public deployment,
paid service, cloud resource or external notification was initiated.
