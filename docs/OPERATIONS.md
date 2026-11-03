# Operations runbook

How to check, fix, release and roll back DefectRAG. Keep this page short and current:
when a fix teaches something new, add one row to **Common problems**.

## 1. What runs where

| Part | Where it runs | Health check | Where to look when it breaks |
|---|---|---|---|
| Online dashboard + API | Hugging Face Space `Wizzas/DefectRAG` (Gradio server mode + FastAPI, ZeroGPU) | `https://wizzas-defectrag.hf.space/api/health` returns `"status":"ok"` | Space page → **Logs** (build and container) |
| Local app | Windows, port 8765 (`deployment/run_local.ps1`) | `http://127.0.0.1:8765/api/health` | The terminal window that started it |
| Accounts, Team records, cases, private photos | Supabase (Auth, Postgres with RLS, Storage) | Supabase dashboard → project status | Supabase → **Logs** (API, Postgres, Auth). Saved checks: `deployment/*_check.sql` |
| Corrective Action emails | n8n on AWS Lightsail + Gmail SMTP, called by a Supabase Edge Function | Case details → **Email delivery** shows each send | n8n → **Executions**; Supabase → Edge Function logs |
| Developer sign-up emails | Supabase cron + Edge worker + Resend | `deployment/email_automation_status.sql` | Supabase Edge Function logs; Resend dashboard |
| Source code, CI and releases | GitHub `WAYTECHG/DefectRAG` | **Actions** tab is green | The failed job's log in GitHub Actions |

Pause all Corrective Action emails at once (the case itself is still saved). This is the app's
feature flag (kill switch): it takes effect immediately, with no release:

```sql
update public.corrective_action_settings set automation_enabled = false;
```

## 2. When someone reports a problem

1. Ask for **Help & references → Copy details for support**. It contains the app version
   (for example `v2.1.0 · 9fad426`), page, connection state, screen size and the last 15 error messages.
   It never contains passwords, emails, tokens or photos.
2. Compare the version with the latest release. An old version usually means a cached page:
   ask them to reload with **Ctrl + F5**.
3. Open the health check for the place they used (table above).
4. Try the same steps yourself on a laptop **and** at phone width (browser dev tools, 390 px).
5. Fix, add a test that would have caught it, release (section 4), then add a row below.

## 3. Common problems

| What people see | Likely cause | What to do |
|---|---|---|
| "The online app is starting or restarting" | Space waking from sleep, rebuilding or restarting | Wait about a minute, press **Retry refresh**. If it stays, check Space **Logs** and restart the Space |
| "The free inspection service has reached its usage limit" | ZeroGPU quota used up | Try later, or sign in to Hugging Face for a separate allowance |
| "Some information could not be updated: …" | One API section failed; the rest still works | The names say which part. Check `/api/health`, then the logs for that route |
| Staff cannot open Team work or Corrective Actions | Not approved yet, security code not entered, or access revoked | Staff workspace shows the exact state. A Developer approves or restores access |
| Case saved but no email arrived | Emails paused, n8n down, or mail in Spam | Case details → **Email delivery**. Then n8n Executions and the `automation_enabled` flag |
| "This page could not be shown" | A screen hit unexpected data. The rest of the app keeps working | Get **Copy details**: the first line under "Recent problems" names the error. Reproduce with the same record |
| Photo flashes or reloads every few seconds | Regression of the fixed evidence-image refresh bug | The 15-second refresh must not re-download photos. Run the browser checks in section 6 |
| Layout looks broken after an update | Old cached CSS or JS | Ctrl + F5. The footer version shows which build is loaded |
| Release run stops at "Refuse an old commit" | `main` moved after the run started | Start a new run |
| Release fails with "Live public configuration differs" | Supabase public settings on the Space changed | Check the Space `frontend/dist/config.js`. The workflow copies it on each run, so start a new run |
| Release fails asking for `HF_TOKEN` | Secret missing, or added to the repository instead of the `production` environment | Add it under Environments → production (one-time setup) |

## 4. Releasing

### Frontend only, from GitHub (one click)

1. Push your latest code to GitHub first (Updating GitHub, below). The release uses what is on
   GitHub `main`, so anything published only from the laptop would be replaced.
2. **Actions → Release dashboard → Run workflow** (branch `main`).
3. **Build and check** runs every dashboard test, builds with the live public config and writes
   a **Release plan** to the run page: the files that would change. Expect
   `frontend/dist/index.html` and files under `frontend/dist/assets/`. The first release from
   GitHub may also list `logo.svg` or `showcase/*.json` (line endings only).
4. **Publish to Hugging Face** then waits. Read the plan, press **Review deployments →
   production → Approve and deploy**. Anything unexpected: **Reject**.
5. Wait about a minute for the Space to rebuild, press Ctrl + F5 on the site and check the
   footer: `v<version> · <GitHub commit>`.

A run started for an older commit stops itself. Server code, models and Space settings are never
changed by this workflow.

**One-time setup** (repository **Settings**):

1. Hugging Face → **Settings → Access Tokens → Create new token → Fine-grained**. Name
   `github-release`. In the repository permissions, add the Space `Wizzas/DefectRAG` and give
   it **write** access. Leave everything else off. Copy the token.
2. GitHub → **Settings → Environments → New environment** `production`. Tick **Required
   reviewers**, add yourself, leave **Prevent self-review** off (you are the only reviewer), save. Under **Deployment branches and tags** choose **Selected
   branches and tags** and add `main`.
3. Same page → **Environment secrets → Add secret**: name `HF_TOKEN`, paste the token.

If the token leaks: delete it on Hugging Face and create a new one. Replace it every few months.

### Frontend only, from the project folder

Run from the project folder, in this order. Any change to `frontend/src` or `frontend/tests`
means running the whole chain again; the publisher refuses stale builds.

```powershell
npm.cmd test --prefix frontend
$env:DEFECTRAG_PUBLIC_CONFIG_FILE='development-support/space/ui-dist/config.js'
$env:DEFECTRAG_SPACE_BUILD_OUT='runtime/auth-build/cloud'
node deployment/space/build_ui.mjs
node deployment/space/frontend_release.mjs verify runtime/auth-build/cloud
node deployment/space/frontend_release.mjs stage runtime/auth-build/cloud
python -m deployment.space.publish --check-frontend
python -m deployment.space.publish --frontend-only
```

`--frontend-only` keeps the server code and the Space settings unchanged.

### Backend changes

**A few existing server files** (for example a fix in `backend/rag.py`): review the change with
`git diff <file>`, run
`python -m pytest tests -q`, then:

```powershell
python -m deployment.space.publish --server-files backend/rag.py --dry-run
python -m deployment.space.publish --server-files backend/rag.py
```

The dry run lists what would change and uploads nothing. The publisher refuses any file whose
live copy differs from the last Git commit (unreviewed drift), new files, and anything outside
`backend/*.py` or `deployment/space/*.py`. The replaced live files are saved in
`development-support/space/server-rollback-<previous Space commit>`. The Space restarts (about
2–4 minutes): guest history in open browsers is temporary, staff records in Supabase are safe.
Afterwards check `/api/health` and ask the assistant about one inspection.

**New server files, new packages or model changes** need a full phase publish with the Space
adapter (`deployment/space/README.md`).

### Rolling back

- **Released from GitHub:** `git revert <commit>` locally, update GitHub, run **Release
  dashboard** again. The run's **rollback** artifact (kept 90 days) also holds the replaced
  `index.html`.
- **Server file (`--server-files`):** upload the saved file from `server-rollback-<commit>` back
  to the same path on the Space (Files → Upload), or `git revert` and publish it again.
- **Online screens:** each frontend publish saves the replaced live `index.html` in
  `development-support/space/frontend-rollback-<previous Space commit>`. Older asset files stay on
  the Space, so uploading that saved `index.html` back to `frontend/dist/index.html` in the Space
  (Files → Upload) brings the previous screens back. Or rebuild from the previous Git commit and
  run the frontend release chain again.
- **GitHub:** `git revert <commit>` and push. Never force-push `main`.

### Updating GitHub

```powershell
.\deployment\Update-GitHub.ps1 -ListFile docs\GITHUB_UPDATE_<date>.txt
cd development-support\github-ready\DefectRAG
git diff --cached --stat
git commit -m "Short description"
git push origin main
```

The script copies only the listed files, refuses unexpected paths (models, `.env`, runtime data)
and never commits or pushes. GitHub Actions then runs the tests (section 6).

## 5. Where to look in the code

| Area | File |
|---|---|
| Pages, navigation, inspection, alerts, history | `frontend/src/main.jsx` |
| Reading server replies (clear messages for HTML, empty or failed replies) | `frontend/src/http.mjs` |
| Support details and recent-problem log | `frontend/src/diagnostics.mjs` |
| "This page could not be shown" card | `frontend/src/ErrorBoundary.jsx` |
| 15-second background refresh | `frontend/src/workspace.mjs` (`startPolling`) |
| Supabase client and sign-in state | `frontend/src/cloud.js`, `frontend/src/account.mjs` |
| Staff workspace and Team review | `frontend/src/TeamWorkspace.jsx` |
| Corrective Actions | `frontend/src/CorrectiveActions.jsx`, rules in `correctiveActions.mjs` |
| Image viewer (zoom, drag, compare) | `frontend/src/InspectionViewer.jsx`, maths in `viewerMath.mjs` |
| Wording shown to people | `frontend/src/userLanguage.mjs` (`friendlyError`) |
| Styles | Loaded in order `tokens.css → style.css → theme.css → design.css → comfort.css`. Put new rules in `comfort.css`, in a labelled section |
| API routes | `backend/main.py`; assistant answers in `backend/rag.py` |
| CI and one-click release | `.github/workflows/ci.yml`, `.github/workflows/release.yml` |
| Cloud transport (queue, GPU jobs) | `deployment/space/transport.js`, `deployment/space/build_ui.mjs` |

## 6. Tests

| What | Command | Count on 2 Nov 2026 |
|---|---|---|
| Dashboard unit and screen tests | `npm.cmd test --prefix frontend` | 274 passed |
| Backend, API and security tests (full installation) | `python -m pytest tests -q` | 207 passed, 2 skipped |
| Same on a fresh clone / CI (no model files) | `python -m pytest tests -q` | 121 passed, 5 skipped |
| Batch queue | `node tests/test_space_batch.mjs` | passes |

GitHub Actions (`.github/workflows/ci.yml`) runs the dashboard tests, both builds, the batch test
and the backend tests on every push to `main` and on every pull request. Tests that need the
model files skip themselves on GitHub (`tests/conftest.py`) and run in full on a local
installation.

**Dependabot** (`.github/dependabot.yml`) proposes grouped minor and patch updates once a month.
Major versions are skipped (they need a planned upgrade). PyTorch, torchvision, Transformers,
anomalib, Pillow and sentence-transformers are held completely because new versions can shift
model scores, benchmark results or the assistant's search (Pillow decodes and resizes every photo;
sentence-transformers makes the search embeddings). Python ranges in `requirements.txt` are only
raised when a new version falls outside them; CI already tests the newest allowed version. Such a
pull request can still be a new major version: test it as a planned upgrade or close it with a reason.

Handling its pull requests: **do not press Merge on GitHub.** The GitHub repo is a copy of the
local folder, so the next `Update-GitHub.ps1` run would undo a GitHub-only merge. Instead:

1. Apply the same version change locally (`npm install <pkg>@<version> --save-exact` in
   `frontend/`, or edit `requirements.txt` and `pip install` it in the `defectrag` conda environment).
2. Run the tests in section 6 and try the app in the browser.
3. Add the changed files to the next GitHub update list and push. Dependabot then sees the
   update is already on `main` and closes its own pull request.
4. Close any pull request you decide not to take, with a short comment saying why.

Browser checks on the real app (laptop, tablet and phone sizes) should cover: inspect a photo,
compare and zoom, ask the assistant, save a review, run a batch, export CSV, mark all alerts as
seen, archive and restore, the phone menu, being offline and the server being down.

## 7. Tools considered

| Tool | Decision | Why |
|---|---|---|
| GitHub Actions | **Used** | Free for public repositories. CI tests and builds every push; **Release dashboard** is one-click CD with an approval step |
| GitHub Environments | **Used** | `production` holds the Hugging Face token and needs your approval before each release |
| Dependabot | **Used** | Monthly, grouped minor/patch updates with no extra service. Applied locally, not merged on GitHub (section 6) |
| GitHub issue forms | **Used** | Bug reports arrive with the page, steps and the app's support details |
| Jira | Not used | One maintainer. GitHub Issues with labels covers tracking without a second system |
| GitLab | Not used | Would duplicate GitHub. Mirroring adds work and no benefit here |
| Kubernetes | Not used | One container on a managed Space. Kubernetes would add cost and maintenance with no scaling need |
| Vector database (Pinecone, Qdrant, …) | Not used | The knowledge base is small (a few dozen attributed documents). The local BGE index is fast and free. Reconsider above roughly 100,000 passages or when several services must share the index |
| LangSmith | Optional, off | Could trace each LangGraph step of an assistant answer. It sends questions and inspection facts to a third party, so turn it on only on a private test copy (`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`), never with real Staff data |
| Uptime monitoring | Optional | A free monitor (or the AWS CloudWatch lab in `deployment/aws/README.md`) can call `/api/health` and email when it fails. Note that a sleeping Space wakes when checked |
