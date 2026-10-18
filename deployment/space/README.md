# DefectRAG Space migration checkpoint

Public application: https://wizzas-defectrag.hf.space

Phases2/3 verified; Phase4 staff persistence is now enabled and live-tested after
the user's manual SQL success confirmation. Final Phase5 deployment is hosted;
read DEVELOPMENT_PROGRESS.md for quota/account acceptance limitations.
Original UI, local application,
static showcase, environments, models and benchmark results remain preserved.

## Existing local application (PowerShell)

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Port 8767
```

Open http://127.0.0.1:8767. Existing local generated answers use Ollama with
qwen2.5:3b; cloud generation uses in-Space Qwen3-4B and needs no local Ollama.

## Isolated migration developer server

Use the existing isolated environment; do not reinstall dependencies or copy
models. Run from the source checkout, not the Desktop production environment:

```powershell
cd C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2
$env:DEFECTRAG_PUBLIC_CONFIG_FILE='C:\Users\User\Desktop\DefectRAG-v2\frontend\public\config.js'
node deployment/space/build_ui.mjs
$env:DEFECTRAG_LIVE_RAG='1'
$env:DEFECTRAG_STAFF_BACKEND='0'
$env:PORT='8784'
& '.\development-support\zerogpu-phase1\.venv\Scripts\python.exe' -m deployment.space.app
```

Open http://127.0.0.1:8784. Local generation retains the existing Ollama path;
the actual Qwen3-4B/ZeroGPU execution was verified in the cloud. The adapter stores
development history separately under runtime/space-development. The reviewed
migration gate has been satisfied for this existing project; do not bypass it for
a different project or execute SQL on the user's behalf. Do not put secrets in
public config; only existing project URL and publishable key belong there.

Latest build/software-only checks do not consume GPU or modify Supabase:

```powershell
& '.\development-support\zerogpu-phase1\.venv\Scripts\python.exe' -m pytest tests/test_space_security.py -q
```

Do not repeat successful inference suites. Their private JSON reports resume
unfinished cases but contain capabilities and must not be committed/published.
Use sanitized docs evidence for sharing. Sync completed source checkpoints to
Desktop with deployment/space/sync_code.ps1; ff-only Git and config/guide hashes
preserve existing user edits. No datasets/models/large ZIPs are copied by it.
