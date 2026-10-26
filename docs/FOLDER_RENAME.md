# Renaming the local folder to DefectRAG

The project and GitHub repository can be called **DefectRAG**. A repository name
does not require renaming the existing local folder. No folder was renamed by
this task. The prepared GitHub export already has the name DefectRAG.

The main launcher uses `$PSScriptRoot`; VS Code uses `${workspaceFolder}`; the
backend derives model/runtime defaults from its own location. Those paths follow
a folder rename. Git history and the hosted Hugging Face application are not
changed merely by renaming the Desktop checkout.

However, the current development arrangement has real absolute dependencies:

- `deployment/space/sync_code.ps1` explicitly targets
  `C:\Users\User\Desktop\DefectRAG-v2`.
- The separate development workspace's `.venv` and `experiments` junctions point
  to that Desktop folder. Renaming it alone breaks those links.
- `.venv/pyvenv.cfg` records the old absolute location. Some installed console
  launchers may also embed it; a virtual environment is not assumed portable.
- Saved terminal commands, shortcuts, optional absolute `.env` overrides and
  debugger/interpreter selections may need updating.

For now, keep the working folder name while development continues. A coordinated
rename should stop the local backend, preserve a checkpoint, verify that
`C:\Users\User\Desktop\DefectRAG` does not already exist, rename only the Desktop
checkout, update the sync target and repair the two development junctions. Reopen
the renamed folder in VS Code and select its Python interpreter. Verify the
environment before installing anything; if a console launcher fails, use
`python -m ...` or repair only the environment. No dataset/model refitting is
required. Existing artifacts and history must remain in the renamed checkout.

After a coordinated rename, the normal local command becomes:

```powershell
cd C:\Users\User\Desktop\DefectRAG
.\Start-DefectRAG.cmd -Port 8767
```

Until then, keep using `C:\Users\User\Desktop\DefectRAG-v2`. The public Space URL
and Supabase database remain the same in either case.
