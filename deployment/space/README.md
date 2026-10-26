# Hugging Face Space adapter

The cloud adapter hosts the same React dashboard with Gradio Server/FastAPI and
queued ZeroGPU inference. BGE retrieval runs in a CPU subprocess; Qwen generation
uses the configured GPU queue. Model/package requirements and public asset pins
are separate from frontend source. [Architecture](../../docs/ARCHITECTURE.md).

## Frontend builds

Install the frontend and the transport client dependencies from their lockfiles.
Prepare a separate public configuration file containing only the intended
Supabase URL/publishable key and reviewed public feature switches. Preserve the
installed configuration when updating an existing Space.

```powershell
$env:DEFECTRAG_SPACE_BUILD_OUT='C:/path/to/separate/cloud-build'
$env:DEFECTRAG_PUBLIC_CONFIG_FILE='C:/path/to/public-config.js'
node deployment/space/build_ui.mjs
node deployment/space/frontend_release.mjs verify 'C:/path/to/separate/cloud-build'
node deployment/space/frontend_release.mjs stage 'C:/path/to/separate/cloud-build'
python -m deployment.space.publish --frontend-only --dry-run
```

Review the allowlisted changed-file plan and source/output receipt. Publication
requires an authenticated write-capable Hugging Face account and explicit project
approval; remove --dry-run only for an approved release. This frontend-only path
preserves the existing backend, private records, configuration and models. A new
Space also needs the separately reviewed backend/model bootstrap; uploading only
React assets cannot create a complete inference service.

In the installed Space, root app.py sets DEFECTRAG_SPACE_UI to frontend/dist before
importing deployment.space.app. That directory is the deployed dashboard, not the
local staging folder. HTML/public configuration use no-store response headers;
hashed JS/CSS/images are served under /assets. Import teaching assets through Vite;
there is no cloud /showcase image route. Existing open tabs may need a reload.

Keep rollback HTML and previous hashed assets until verification completes. Test
the actual application URL, loaded asset versions, private-access boundaries and
public demo/gallery separately. A successful upload is not proof of a working app.
No inference benchmark or email send is needed for a documentation-only release.
