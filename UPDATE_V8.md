# DefectRAG v8: local inspection fix and Aurora interface

This is a small source patch for an existing DefectRAG v7 project. The logs showed `NameError: name 'UPLOAD_DIR' is not defined` in `app/main.py` on `POST /api/inspect`. The patch imports the configured upload directory. No Ollama model, DINOv3 feature, checkpoint, dataset, or retrieval index is replaced.

The interface now uses a dark translucent instrument-panel palette, decorative scanning/orbit animations, responsive glass surfaces, interactive glow, scroll reveals, and clearer error feedback. Animation is suppressed for visitors who request reduced motion. Its animation is decorative: only the elapsed timer is measured live, and the four pipeline stages are not server events.

From your Windows PowerShell project directory, merge the `DefectRAG/` folder from this ZIP into the existing project without deleting your existing files. Rebuild the API container:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build api
docker compose -f docker-compose.yml -f docker-compose.gpu.yml logs --tail=60 api
```

Hard-refresh `http://localhost:8000` with **Ctrl+Shift+R**, select breakfast box, and inspect an image. The Ollama named volume remains intact; no `ollama pull` is necessary. If a later inference step fails, the UI shows the HTTP status and the API log shows the cause. A successful inspection after this fix still depends on your existing gated DINOv3 cache/access, features, index, and Ollama availability.

For the Render website, commit and push `app/main.py`, `app/static/app.js`, `app/static/index.html`, `app/static/aurora.css`, and `app/static/aurora.js` to the GitHub repository linked to Render. Render rebuilds its gateway and serves the same refreshed interface. The Hugging Face Space does not need an update for this patch; its code is not changed. Do not upload local `.env`, training files, features, or the dataset to Render.
