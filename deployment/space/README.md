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

## Compatible batch validation and reports

The cloud host mounts `backend.inspection_routes.mount_inspection_experience`
explicitly before its copied CPU routes and catch-all. It retains the existing
request identity/workspace middleware. The two read-only routes are batch-name
availability and the printable inspection report; neither grants access or writes.
Health advertises `batch-name-v1` and `inspection-report-v2`.

For an audited release that requires these routes, use the verified publisher
with `--frontend-only --inspection-compatibility --dry-run`, review its exact file
list, then repeat without `--dry-run` after deployment authorization. This mode
patches only known host statements and adds the three reviewed route/rendering
modules. It refuses unrelated host drift, preserves configuration and stores
previous server/HTML bytes for rollback. It does not upload `backend/main.py`,
models, secrets or database state. Reverting the previous host and HTML makes the
new modules unused; leave database records and migrations intact.
