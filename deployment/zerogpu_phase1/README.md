# Phase 1 compatibility proof

This directory is isolated from the working local application. Phase 2 is not
authorized. Do not use this fixture-only proof as a production migration.

## What changes

`app.py` hosts the existing React build with `gradio.Server`, reuses CPU read
routes, and schedules the existing DINOv2 PCB1 scoring with `spaces.GPU`.
`transport.js` sends the inspection through `@gradio/client`. `build_ui.mjs`
injects that transport at build time without editing React sources, CSS, package
files, or existing dist/static builds. A single caption identifies the public test.

Only the exact bytes of `samples/pcb1_anomalous.jpg` are accepted. This is a real
model call, not a cached prediction. Other categories/arbitrary uploads, batch
execution, RAG generation and public staff collaboration are outside Phase 1.
Read-only history, evaluation, CSV and reports use an isolated temporary SQLite
workspace. No private local history, Supabase settings or credentials are published.

## Resume the existing local proof without reinstalling

Use the source checkout, not the Desktop production environment:

```powershell
cd C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2
$env:GRADIO_ANALYTICS_ENABLED='False'
$env:USE_TF='0'
$env:DEFECTRAG_PHASE1_CONFIG='C:\Users\User\Desktop\DefectRAG-v2\frontend\public\config.js'
& '.\development-support\zerogpu-phase1\.venv\Scripts\python.exe' -u -m deployment.zerogpu_phase1.app
```

Open http://127.0.0.1:8783, select Image inspection / PCB 1, upload the supplied
JPEG, and run once only if a new inspection is needed. Saved verification already
exists; do not repeat the successful run merely to resume development.

The small isolated virtual environment references the existing Desktop PyTorch
installation through a `.pth` file. The production environment was not upgraded.
Gradio 6.30.0 requires Hugging Face Hub >=1.16, while original Transformers 4.57.6
requires Hub <1. The isolated proof uses Transformers 5.20.1 and Hub 2.2.0.

## Rebuild or redeploy only if relevant files change

The build and JS dependencies are already installed. Rebuilding is unnecessary
on resume. For a future intentional adapter change:

```powershell
node deployment/zerogpu_phase1/build_ui.mjs
```

`client/package-lock.json` pins the separate JS dependency tree. Cloud requirements
pin Python-compatible packages; the CUDA 12.8 wheel index is specified, but the
Torch version must be `torch==2.8.0` without a CUDA suffix for HF's preflight parser.
Do not install the Linux cloud requirements into the Windows production venv.

The initial publisher intentionally refuses to overwrite an existing Space or
staging directory. **Do not rerun `publish_minimal --publish` after the initial
upload.** Use a reviewed narrow commit with an expected parent revision for any
necessary Phase 1 correction. Never modify `Wizzas/defectrag-inference`.

Read-only cloud status (no model execution):

```powershell
& 'C:\Users\User\Desktop\DefectRAG-v2\.venv\Scripts\python.exe' -m deployment.zerogpu_phase1.check_space
```

Add `--logs build` or `--logs run` for a bounded log capture. Saved evidence lives
in `development-support/zerogpu-phase1`; this directory is Git-ignored because it
contains dependencies, the compiled test build and staging model copies.
Code-only results and precise limitations are in `docs/ZEROGPU_PHASE1_RESULTS.md`.
