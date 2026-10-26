# Setup and operation

This repository contains application source, tests and attributed demonstration
assets. Model weights, normal-reference banks, private records, environments and
secrets are deliberately excluded. Do not retrain a model merely to start the app.

## Existing Windows installation

From the installed project directory:

```powershell
& '.\deployment\run_local.ps1'
```

Open http://127.0.0.1:8765 and keep the terminal running. The launcher checks the
frontend build and rebuilds it when needed, preserving the previous build. It
reuses a healthy existing service rather than starting another on the same port.
For private synchronization, configure the intended Supabase project, sign in with
an approved account and complete its authenticator verification. Each browser
origin has its own session. Check the online save status before switching devices.

## Fresh source clone

Install Python 3.11, Node.js/npm and Git, then:

```powershell
git clone https://github.com/WAYTECHG/DefectRAG.git
Set-Location DefectRAG
py -3.11 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
npm.cmd ci --prefix frontend
& '.\.venv\Scripts\python.exe' -m scripts.fetch_public_assets --list
# Explicit optional download of the pinned public model/bank/sample assets:
& '.\.venv\Scripts\python.exe' -m scripts.fetch_public_assets
npm.cmd run build --prefix frontend
.\Start-DefectRAG.cmd -Port 8767
```

The last command starts the standalone local application at
http://127.0.0.1:8767. The synchronized launcher above uses port8765 and needs the
corresponding cloud setup. The asset downloader checks the 12 DINOv2 bank hashes;
it does not fit models or alter calibration. NVIDIA acceleration needs a compatible
CUDA/PyTorch installation. A complete fresh dependency/model installation was not
repeated during documentation cleanup.

For local generated answers, install/start Ollama and provision the configured
model separately (default `qwen2.5:3b`). Saved-measurement answers do not pretend to
be generated model responses. Cloud generation instead uses the hosted Qwen path.

## Optional Supabase services

Review migrations before applying them to a new project. Existing installations
must inspect their schema and applied changes first; do not rerun setup SQL simply
because it is present in this repository. Back up and test recovery before changing
an established database. Native Auth settings and storage policies are project
configuration, not automatically created by cloning source.

| Area | Main schema source |
| --- | --- |
| Staff/team records and private image storage | `deployment/supabase.sql` |
| Conversations and alert acknowledgments | `deployment/supabase_additive_conversations.sql` |
| Private account workspaces | `deployment/supabase_personal_workspace.sql` |
| Public copies in the Community Gallery | `deployment/supabase_public_gallery.sql` |
| Registration, Developer decisions and native MFA guards | `deployment/supabase_auth_mfa.sql` |
| Versioned local/cloud synchronization | `deployment/supabase_personal_sync.sql` |
| Assigned, human-confirmed corrective-action cases | `deployment/supabase_corrective_actions.sql` |
| Developer email outbox and scheduling | `deployment/supabase_direct_notifications.sql` and the developer-notification migration files |

Read the dependency checks in each migration. Keep new feature switches inactive
until its schema, account recovery and native authorization tests pass. See
[Security](SECURITY.md) before mandatory MFA or notification activation.

Only the Supabase URL and publishable key belong in `frontend/public/config.js`.
Use the public configuration example under deployment for feature-field names.
Never place service-role keys, worker/webhook secrets, SMTP credentials or account
tokens in React configuration. Configure protected server/Edge Function secrets
privately. New installations need email confirmation/recovery redirects for their
actual local and hosted URLs and a working Auth email delivery setup.

The same approved account can use Personal history on both local and hosted
clients. Queued offline changes are not yet cloud-saved. Team sharing and public
Gallery publication remain separate choices. Legacy local-history import is an
explicit action, not an automatic bulk upload. Local gallery publishing needs its
own configured adapter; browsing the hosted gallery does not upload local photos.

## n8n and notification scope

Developer registration emails use an independent cloud Cron/Edge/Resend path.
Local n8n is for the separately verified Corrective Action integration. Its templates
and tests are under `deployment/n8n`; keep real delivery and schedules disabled
until authenticated callbacks, durable retries, deduplication, SMTP and reliable
hosting have been tested. The restricted Developer test sender is not a general
applicant-email service. Review provider restrictions before expanding recipients.

Local n8n, local inference and Ollama stop when their machine/processes stop.
Already-synchronized Supabase records and independently hosted services do not
require that laptop to remain on. Do not delete existing Docker volumes to restart
an installed n8n editor; they contain credentials and workflows.

## Development checks

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests -q
npm.cmd test --prefix frontend
npm.cmd run build --prefix frontend
```

Tests that need real accounts, models, Docker or external integrations have their
own prerequisites. A unit-test pass alone does not establish live delivery or
scientific model performance. The cloud publisher checks source/output receipts
and preserves existing public configuration; see [Space deployment](../deployment/space/README.md).
