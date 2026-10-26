# DefectRAG local operating edition — 26 October 2026

Owner selected finishing the current application with local n8n. Oracle/Azure
signup is not a prerequisite for this milestone. Multimodal RAG is a separate,
deferred upgrade. This is a local operating release, not activation of unattended
production Corrective Action notifications.

## Start the existing Desktop application

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2'
& '.\deployment\run_local.ps1'
```

Open **http://127.0.0.1:8765**. Keep that terminal open. Stop with Ctrl+C.
The launcher preserves an old dashboard before rebuilding it, verifies the
source/output receipt, serves frontend and backend together and enables local
private synchronization. If the same healthy server is already running, it prints
the address rather than launching a second server. It never kills an unrelated
process to obtain the port. A fresh clone still needs the documented dependencies,
public config and downloaded assets; this command targets the existing installation.

For private records, use the same approved account as on Hugging Face and complete
its TOTP verification. Browser origins have separate sessions. Personal inspections
save privately and synchronize through Supabase while connected. Offline pending
operations are not yet cloud-saved; check synchronization status before shutting
down. Explicit sharing is required for Team access. Gallery publication is separate.
Do not automatically import legacy history; retain its existing backup/import gate.

Anonymous visitors can use the existing isolated demo path. Guest storage is not
an authenticated Personal cloud account. Local n8n does not give guests staff access.
An unsubmitted single-image selection/category/label resets on a full browser
reload. This is not a lost saved inspection. Keep the tab open until Run Inspection
finishes; saved history and the batch checkpoint have separate persistence paths.
For Evidence Assistant generation, the existing Ollama qwen2.5:3b service must be
available. Saved-measurement answers and document retrieval remain the current
vision-assisted text RAG architecture. No image-language upgrade is included.

## Use the existing local n8n editor

Open **http://localhost:5678** with Docker Desktop running. Keep the existing
`n8n` container and `n8n_data` volume. Do not run `docker compose down -v`, delete
the volume, recreate credentials or replace another workflow to start this demo.
The app's root compose.yaml is a separate legacy app container; it does not start
the existing n8n installation or replace the synchronized Windows launcher.

Verified draft: **DefectRAG CA - LIVE QA SINK ONLY - INACTIVE**, workflow ID
`yx3NG0Ac1kIv8L37`. It is a completed, unpublished test workflow. All nine nodes
succeeded against real Supabase and a one-message local no-relay sink. The sink
has been stopped; the grant was consumed and the same QA case is Closed/version 7.
Inspect the saved screenshot/evidence instead of executing that spent event again.
No key or QA-grant procedure needs repeating for an ordinary demonstration.

The separate simulated practice workflow demonstrates duplicate suppression and
receipt-loss handling without real data. Its restart instructions are in
`deployment/n8n/LOCAL_PRACTICE.md`; those simulations are not production delivery.
Leave unrelated workflows, including Smart Task Prioritize, unchanged.

## Current capability and verification boundaries

| Area | Current status |
| --- | --- |
| React dashboard / inspection / batch / reports | Existing functionality preserved; current local builds must pass the source/output receipt check. |
| DINOv2/DINOv3 and 12 categories | Existing models/banks preserved; benchmark experiments are not repeated by this release. |
| Evidence Assistant | Existing BGE/LangChain/LangGraph/Qwen path preserved; Multimodal RAG deferred. |
| Private local ↔ cloud synchronization | Prior real-Supabase tests passed; approved MFA account required; no automatic Team sharing or legacy import. |
| Staff registration / Developer approval / MFA | Existing live controls preserved; local startup does not change permissions or approve anyone. |
| Community Gallery | Existing storage and publication flow preserved; no automatic publishing. |
| Developer access-request emails | Existing independent cloud Cron/Edge/Resend implementation stays in its current active state. It does not depend on local n8n. |
| Corrective Action permissions | Native Supabase owner/supervisor/Developer and denial tests passed within the recorded scope on 24 October. |
| Local n8n integration | Real one-event cloud→local n8n→SMTP sink→cloud receipt/finalization passed on 26 October; one message, zero real emails. |
| Case lifecycle | Same synthetic case advanced Open→Assigned→In Progress→Resolved→Closed with audit actors and timestamps. |
| Reminder / overdue logic | Existing SQL deadline/dedup contracts passed isolated PostgreSQL tests. Live unattended scheduling is inactive. |
| Automatic real Corrective Action mail | OFF. Keeping n8n local is not permission to turn on production delivery or replay queued QA events. |

The current local server has no publishing-gallery adapter configured. Its Gallery
page explains that state and offers **Open hosted community gallery** for public
browsing. That link does not transfer or publish local images. The existing hosted
Gallery and its records remain unchanged; local publishing would require its own
explicit setup. No gallery key is copied into the frontend or from production.

## What stops when the laptop is off?

The local dashboard, local Ollama and local n8n stop when their processes/Docker
stop. Local n8n cannot then deliver reminders. Supabase-saved records, the existing
Hugging Face application and the independent cloud Developer notifications do not
depend on this Windows process. Free Hugging Face GPU quota and sleep limitations
remain as previously documented; this milestone does not guarantee availability.

The existing local n8n container has a persistent `n8n_data` volume and restart
policy `unless-stopped`. Inspection of public Docker metadata found its port 5678
published on all host interfaces, not restricted to loopback. This does not prove
Internet reachability; host firewall/router rules were not audited. Keep editor
authentication and avoid port-forwarding. Rebinding would require reviewing and
recreating the existing container safely; it was not silently changed because it
also holds an unrelated workflow. The FastAPI launcher binds only 127.0.0.1.

## Deferred activation work

Always-on hosting, production SMTP and live deadline/recovery/restart tests remain
separate. Before any production activation, review/quarantine retained QA events,
including the latest Closed-case update, without deleting history. An outbound
local dispatcher could be a separate design if automatic real mail while the
laptop is on is later requested; no such dispatcher is claimed by the manual test.
No migrations, production secrets, staff permissions, live mail or scheduler flags
are changed by this release. See `CA_N8N_COMPLETION_20261025.md` for live evidence.

## Final local acceptance checks

Completed 26 October on the existing Work and Desktop installations:

- Final frontend regression suite: **194 passed, zero failed**. This includes the
  new local-Gallery rendering/privacy check. Startup/receipt tests: **3 passed**.
  The initial restricted startup-test run stalled and was stopped without a result;
  the normal host-permission run passed in 0.53s. It was not counted as a passing run.
- Both copies build successfully. Their normalized UI source hashes and compiled
  artifact hashes match. Served entry is **index-BoTkraXn.js**; stylesheet remains
  **index-Bn4HF2vD.css**, unchanged. HTML uses `Cache-Control: no-store`.
- Preserved Desktop config.js and RUN_AND_DEPLOY.md hashes match the guarded-sync
  baseline. Models, datasets, secrets and inspection databases were not copied or
  replaced. Original builds are retained under runtime/frontend-backups/.
- Local HTTP 200 and healthy sync/auth flags; 12/12 model cards available, 24 samples;
  Ollama reachable with the configured qwen2.5:3b installed. These are readiness
  checks, not a new DINO/Qwen inference benchmark.
- Native browser: clean Overview and reload without a red refresh/rebuild warning;
  guest demo entry available; missing-image Run reason visible; choosing a Capsules
  sample enables Run; Staff registration/sign-in/reset controls present; local
  Gallery explanation/link readable. No inspection was submitted or published.
- Calling the launcher again reuses the healthy server and does not create another
  process or port error. The Desktop server was left running at 127.0.0.1:8765.
- Existing non-blocking Vite warnings remain for the intentionally separate classic
  config.js and mixed static/dynamic auth imports. No dependency upgrades or new
  packages were needed.

Evidence: results/local-completion-20261026/. Current native cloud authorization,
sync and model conclusions rely on their earlier dated live results; no fresh
authenticated cloud suite, HF deployment or expensive model experiment was repeated.
