# DefectRAG v9: local method selection and bounded visual reasoning

Merge this patch into an **existing** DefectRAG project. It includes the v8 missing `UPLOAD_DIR` import and Aurora interface files, so it can be applied directly over v7 or v8. It does not include or delete your LOCO AD dataset, extracted features, compact memory banks, trained heads, index, `.env`, or Ollama volume.

## What changed

- Local `/api/health` advertises baseline/trained/fusion per category based on the assets actually present. The webpage enables only the methods supported by the selected product.
- Local `/api/inspect` now receives the selected method. With `cloud/space/assets/<category>.pt`, it uses the same 20,000-patch compact bank shape and score definitions as the cloud Space. It loads `<category>_head.pt` from `cloud/space/assets/` or `results/runtime/training/seed42/`. Without a compact bank, baseline retains its legacy feature-folder fallback. Trained and fusion scores have **no calibrated binary verdict**.
- Local visual reasoning now sends a resized complete view plus one resized focused view instead of four original-resolution images. Ollama output is capped at 320 tokens with a 120-second client timeout. This reduces work but can lose detail; review answer quality on fixed test examples before reporting a speed/quality result.
- The local retriever runs its embedding model on CPU so DINOv3 and Ollama can share an 8 GB GPU. API logs record scoring, visual observation, retrieval, and optional cloud persistence boundaries. The page shows an explanatory long-wait notice at 90 and 180 seconds without inventing live server progress.

## Windows PowerShell update

Merge `DefectRAG/` from this ZIP into your existing project. Do not use `/MIR` or `docker compose down -v`.

```powershell
cd 'C:\Users\User\Desktop\DefectRAG-Cloud-Professional-v4\DefectRAG'
Get-ChildItem .\cloud\space\assets\*.pt | Select-Object Name
Get-ChildItem .\results\runtime\training\seed42\*_head.pt | Select-Object Name
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build api
docker compose exec api python -m unittest discover -s tests -v
curl.exe http://localhost:8000/api/health
```

Expect five category banks and five seed 42 heads. The `/api/health` JSON should include `"scoring_methods":["baseline","trained","fusion"]` and category-specific `methods` arrays. Hard-refresh the page with **Ctrl+Shift+R**. Rebuilding stops the old in-flight request; no model pull, feature extraction, or training is needed.

If a fresh request remains slow, watch the exact stage:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml logs -f --tail=80 api ollama
```

The first request can still load DINOv3, the embedding model, and Ollama from cache. Subsequent warm requests should be measured separately. A configured Cloudinary/AuraDB service also runs before the response; the new log boundary makes that delay visible. The 120-second limit covers only the Ollama visual request, not every part of the pipeline.

The Hugging Face Space code is unchanged by this patch. For the public Render website, commit the refreshed shared `app/static/` files to the repository linked to Render after local validation. Render itself still proxies its Space for all three methods; this patch primarily fixes **local Docker** method selection and visual reasoning speed.
