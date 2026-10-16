# Run locally or publish the free static showcase

The local application provides live inspection and local RAG. The public static
showcase provides seven saved real inspections, original/heatmap toggles,
recorded cited conversations, history filters, reports, CSV and evaluation pages.
Static hosting does not execute Python, accept uploads or answer new questions.
Browser model conversion and live browser RAG have not been implemented.

## Local application — Windows PowerShell

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Setup
```

Setup needs Python 3.11 or 3.12 and internet to install dependencies. For later starts:

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd
```

Open http://127.0.0.1:8765. If another application already owns that port, use:

```powershell
.\Start-DefectRAG.cmd -Port 8766
```

Qwen answers additionally need Ollama running with `qwen2.5:3b` installed.
The inspected image and retrieval still work without it; the assistant explicitly
falls back to retrieved passages. The existing model assets need no retraining.
See the main README for CUDA and existing-environment options.

## Static preview — no AI server needed

The new full release includes `frontend/dist-static`. Preview it with:

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
python -m http.server 8771 --bind 127.0.0.1 --directory frontend/dist-static
```

Open http://127.0.0.1:8771. Stop with Ctrl+C. Do not double-click index.html;
the browser must load the example JSON over HTTP. The separate static ZIP has
index.html at its root, so serve its extracted folder directly instead.

## Vercel — static deployment

From the source project, with Node installed:

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2\frontend
npm.cmd ci
npx.cmd vercel --prod
```

Sign in when prompted and use a personal Hobby project if eligible. The included
`frontend/vercel.json` sets build command `npm run build:showcase` and output
directory `dist-static`. Do not choose the ordinary `dist` build: it expects the
local backend. No VITE_API_URL, secrets, database or model service is required.
The command returns your public URL. Deployment has not been performed here.

Official command reference: https://vercel.com/docs/cli/deploy

## Render — Static Site

Push the source to your Git provider, excluding ignored model/runtime files.
Create **Static Site**, connect that repository, and set:

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm ci && npm run build:showcase` |
| Publish directory | `dist-static` |

The included root `render.yaml` declares the same static configuration. No paid
web service, Python runtime or persistent disk is needed for this showcase.
Hash routes work without rewrites. Free hosting is subject to provider quotas.
Official instructions: https://render.com/docs/static-sites

## Hugging Face — Static Space

1. Create a Space and select **Static** SDK.
2. Extract `DefectRAG-v2-static.zip`.
3. Upload its contents (index.html, assets/, showcase/, README.md and notices)
   to the Space repository root. Do not upload the enclosing folder or full AI ZIP.
4. Commit the files. The included README metadata sets `sdk: static`.

No build step, API key or paid compute is needed. Keep the supplied VisA
attribution and notices. Official instructions:
https://huggingface.co/docs/hub/spaces-sdks-static

## Rebuild only after source changes

The saved snapshot is versioned in `frontend/public/showcase`; deployment builds
do not read the private runtime database and never repeat model experiments.

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2\frontend
npm.cmd ci
npm.cmd run build:showcase
node --test tests/showcase.test.mjs
```

An intentional snapshot refresh uses `python -m scripts.export_showcase` from
the application root and requires the original saved verification database.
It reads only allowlisted VisA records and does not generate predictions.
