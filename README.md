# DefectRAG

The accuracy upgrade adds a separate high-resolution DINOv2 profile and overall
image/pixel AUROC and AU-PR. See [accuracy comparison](docs/ACCURACY_RESULTS.md) and
[settings and metric definitions](docs/ACCURACY_AND_METRICS.md). Original DINOv3
models, results, records and releases remain preserved.

Local visual anomaly screening with an inspection-linked evidence assistant.
React/Vite dashboard, FastAPI, frozen DINOv2 / DINOv3, LangChain/LangGraph, SQLite and
optional Qwen through Ollama. All **12 VisA product categories** are available.
The existing directory name `DefectRAG-v2` is retained for command compatibility.

## Start on this computer

Stop the previous server with Ctrl+C in its PowerShell window, then run:

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
$env:PYTHONPATH="C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\.test-deps"
$env:USE_TF="0"
.\Start-DefectRAG.cmd -Port 8767 -PythonPath "C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe"
```

Open http://127.0.0.1:8767. No rebuilding or model fitting is needed. Leave this
window running. In another terminal, `ollama list` checks your installed models.
The active detector profile is selected automatically from installed model assets.
Set `DEFECTRAG_PROFILE=legacy` before launch to use the original DINOv3 profile.
Only `qwen2.5:3b` is used by default; Ollama must run for generated document
explanations. Verdict and score answers work without an LLM.

On another computer, install Python 3.11 or 3.12, extract the local ZIP and
run `.\Start-DefectRAG.cmd -Setup` once, then `.\Start-DefectRAG.cmd`.
Setup downloads dependencies into a new `.venv`; weights and dashboard are bundled.
CPU works. NVIDIA acceleration needs compatible PyTorch CUDA wheels. Node is
needed only for editing the frontend. A fresh dependency install was not tested.

## Using the application

1. Select the correct product and upload a photograph, or choose a VisA sample.
2. Run inspection. Compare original/heatmap with the slider, zoom or expanded view.
3. Read the verdict, distance score, threshold and review band. A score of 0.09
   is **not 9% accuracy**. Higher distances indicate less normal appearance.
4. Ask “Is this image anomalous?” or “Does the score mean accuracy?” The answer
   uses that saved inspection, rather than quoting a generic policy definition.
5. Filter history, acknowledge alerts, export CSV or print a report.
6. **Clear history archives records**. Recovery restores evidence and images.
   Back up `runtime/` separately; archival is not an independent backup.

The assistant receives the saved inspection ID, category, verdict, score,
threshold and conversation. It **does not see the photograph**. Measurement
answers are separate from Qwen explanations backed by retrieved passages.
Exact quotes/IDs are checked, but this does not guarantee semantic correctness.
Unsupported causes, repairs and tolerances are not invented.
See [assistant data flow](docs/EVIDENCE_ASSISTANT.md).

## Official-split benchmark — accuracy improvement

The official VisA evaluation reports AUROC and AU-PR averaged across all 12
products. Mean image AUROC is our headline anomaly-detection number; mean image
AU-PR is reported alongside it. Pixel metrics assess localization separately.
There is no single official score combining image detection and localization.
See Section 4.2: https://arxiv.org/html/2207.14315 .

Both experiments use all 8,659 official training normals and the same 2,162 official
test images, with three fixed bank seeds 42/43/44. These are retrospective
benchmarks: earlier results informed development. They are not an untouched
external test or reproduction of a published method.

| Overall metric | Original DINOv3 | DINOv2 high resolution |
|---|---:|---:|
| Mean image AUROC | 85.38% | 95.13% |
| Mean image AU-PR | 86.47% | 95.74% |
| Mean pixel AUROC | 92.96% | 98.60% |
| Mean pixel AU-PR | 33.29% | 43.04% |
| Supplementary mean image AP | 86.58% | 95.77% |

Macaroni 2 image AUROC improved from 0.483 to 0.832. The candidate improves most
categories; Cashew regresses slightly in image AUROC and also in pixel AP.
All category results and regressions are in [the measured comparison](docs/ACCURACY_RESULTS.md).

The new profile is inspired by AnomalyDINO: frozen DINOv2 Small/14, 448px short
edge, retained aspect ratio, PCA foreground filtering and a larger normal memory.
It does not fine-tune weights and is not Dinomaly. Ground-truth masks are used
only for evaluation, never for fitting or foreground selection. Pixel evaluation
uses 224×224 maps. PCA can miss foreground and localization remains imperfect.
No factory diagnosis, wrong-product detection or product-safety guarantee is made.

Operational deployment uses a separate fixed-seed bank, with a content-grouped
10% normal training holdout excluded from fitting. Its threshold is the maximum
holdout normal score. The Model performance page reports that deployment profile's
actual precision/recall/F1; those depend on the threshold and review band.
At the current conservative maximum-normal threshold, macro precision is 97.59%,
recall 60.17% and F1 68.63%. Higher AUROC is not
the same as 95% classification accuracy, and this operating point can miss defects.
The three-seed benchmark uses every official training normal and reports ranking
metrics. These two profiles are clearly separated in the results.

Original DINOv3 banks, modified-split evaluations and historical inspection results
remain unchanged. Set DEFECTRAG_PROFILE=legacy to return to that detector. Existing
54–66 ms serving figures apply only to the original model, not the new profile.
See [settings, resume commands and metric definitions](docs/ACCURACY_AND_METRICS.md).

## Free public dashboard and shared staff history

`DefectRAG-static-accuracy.zip` contains **25 measured examples**, heatmaps,
recorded conversations, reports and both evaluation views. Serve the extracted
folder over HTTP, or use Vercel, Render Static Site or Hugging Face Static Spaces.
[Run/deploy commands](deployment/RUN_AND_DEPLOY.md).

Optional Supabase staff sign-in, shared snapshots, notes and recoverable history
are implemented. **No Supabase project has been created or connected. Hosted
authentication, RLS and storage remain untested.** Follow
[Supabase setup](deployment/SUPABASE_SETUP.md); the app shows setup instructions
until configured. Only explicitly shared inspections leave the local app.
Staff records require approved sign-in.

Static hosting cannot execute Python models or local Ollama. Cloud sharing does
not supply inference. The local API is single-user; do not expose it publicly
as a multi-user service. No cloud resources or paid services were provisioned.

## Development and preservation

```powershell
python -m pytest tests -q
python -m scripts.check_environment
cd frontend
npm.cmd ci
npm.cmd run build
npm.cmd test
npm.cmd run build:showcase
```

[Editor setup](docs/EDITOR_SETUP.md) explains yellow import underlines.
Production builds are bundled. Official experiment receipts skip completed
categories; do not repeat successful experiments. Datasets, private runtime
records and secrets are excluded from ZIPs. A separate benchmark-assets ZIP
preserves experimental banks. Earlier ZIPs, models and Git history are preserved.
Docker execution is unverified because the daemon was unavailable. A previous
mobile viewport override was ignored, leaving narrow-screen visual QA unverified.
The legacy Anomalib prototype is not the deployed model.

- [Development checkpoint](DEVELOPMENT_PROGRESS.md)
- [Upgrade verification](docs/UPGRADE_VERIFICATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Asset licenses and attribution](docs/THIRD_PARTY_NOTICES.md)

Application code: MIT. VisA: Zou et al., ECCV 2022, Amazon Science, CC BY 4.0.
Model and dataset licenses are separate from application code.
