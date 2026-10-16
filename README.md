# DefectRAG

Local visual anomaly screening with an inspection-linked evidence assistant.
React/Vite dashboard, FastAPI, frozen DINOv3, LangChain/LangGraph, SQLite and
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

## Official-split benchmark

The new report follows official VisA one-class train/test assignments: all
training normals and all test images. Masks are used only for localization
metrics. Three fixed bank seeds (42,43,44), no best-seed selection.
Image AU-PR is trapezoidal area; AP is separately reported.

| Product | Image AUROC | Image AU-PR |
|---|---:|---:|
| Candle | 0.917 | 0.913 |
| Capsules | 0.816 | 0.895 |
| Cashew | 0.969 | 0.986 |
| Chewing gum | 0.961 | 0.985 |
| Fryum | 0.899 | 0.951 |
| Macaroni 1 | 0.821 | 0.796 |
| Macaroni 2 | **0.483** | **0.478** |
| PCB 1 | 0.880 | 0.854 |
| PCB 2 | 0.795 | 0.789 |
| PCB 3 | 0.798 | 0.811 |
| PCB 4 | 0.937 | 0.933 |
| Pipe fryum | 0.970 | 0.986 |
| Equal-weight macro mean | **0.854** | **0.865** |

Means over three seeds; the Benchmark page includes standard deviations, counts
and pixel metrics. This custom frozen-feature method is **not Dinomaly** and
**does not fine-tune neural weights**. Learning rate and epochs do not apply.
See [training settings and commands](docs/TRAINING_AND_EVALUATION.md) and
[measured report](results/official_evaluation.json).

This is retrospective: earlier development already exposed test identities and
results. It is not an untouched external test or published-method reproduction.
Pixel evaluation uses 224×224 maps from a coarse 14×14 grid. Macaroni 2 separation
is weak; macaroni localization is particularly poor. No factory diagnosis or
product-safety guarantee is established. The operator-selected product is not
verified automatically.

Original application banks and modified-split evaluations remain unchanged in
`models/` and `results/evaluation.json`. Performance describes those deployed
banks; Benchmark describes the separate official experiment. Its normal-only
calibration variant is also saved separately, not substituted into the app.
The serving profile measured roughly 54–66 ms median inference on the original
three categories on RTX 4060; this is not an all-category latency guarantee.

## Free public dashboard and shared staff history

`DefectRAG-static-upgrade.zip` contains **25 measured examples**, heatmaps,
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
