# One application folder

The current installation is C:\Users\User\Desktop\DefectRAG-v2. Run:

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Port 8767
```

VS Code interpreter: .venv\Scripts\python.exe inside this folder. Select it
once with Python: Select Interpreter if VS Code remembers the previous path.
The launcher sets local dependency visibility automatically. No environment
variables, old application folders, downloads or retraining are needed to start.
The base Python installation (Anaconda) and Ollama remain system installations.
Do not remove Anaconda while this virtual environment uses its base interpreter.

| Folder | Contents |
|---|---|
| .venv | Existing CUDA/PyTorch environment, relocated and launcher paths repaired |
| .python-deps | Local auxiliary Python packages formerly loaded from Codex |
| models | Both original DINOv3 and active DINOv2 model assets |
| results | Saved application and benchmark reports/predictions |
| experiments | Both complete 12-category experiments, banks, splits, caches and metrics |
| runtime | Private inspection history, images and conversations |
| development-support/legacy-projects | Preserved Unified project and remaining Verified Git history |
| development-support/git | Code recovery bundles |

Legacy contents may include distinct datasets, results, credentials and research
environments. They are preserved privately, not merged into active settings or
included in release ZIPs. Moving them does not free disk space or duplicate them.
The original VisA dataset in Downloads is unchanged and is not needed for normal
app use; it remains necessary to repeat or extend experiments later.

After development-support/consolidation-verification.json says status=passed,
the Desktop DefectRAG-local-accuracy.zip and DefectRAG-highres-benchmark-assets.zip
are optional backups: their application models and experimental banks already
exist in this folder. Removing either ZIP does not affect running the app or its
saved results, but removes that independent recovery copy. The pre-consolidation
application ZIP has historical launch instructions. No replacement large ZIP is
created by consolidation. Keep a separate backup elsewhere if desired.

The Codex source mirror may retain junctions pointing to this installation's
experiments, so completed work is not repeated. Data physically lives here.
Exact consolidation moves and checks are in development-support receipts.
