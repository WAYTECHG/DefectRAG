# DefectRAG free-cloud deployment

This deployment uses one lightweight Render web service, one Hugging Face ZeroGPU Space, Neo4j AuraDB, and Cloudinary. It keeps the public website small enough for Render's free 512 MB service while the GPU models run outside Render.

## Architecture

```text
Browser
  -> Render FastAPI gateway (UI, validation, API)
       -> Hugging Face ZeroGPU Space (DINOv3 + Qwen-VL + retrieval)
       -> Cloudinary (bounding-box and heatmap images)
       -> Neo4j AuraDB (inspection, evidence, and support-message graph)
```

The Render filesystem is intentionally treated as temporary. Model assets and the retrieval index are immutable deployment files. Durable inspection records are written to AuraDB, and generated images are uploaded to Cloudinary.

## Important free-tier behavior

- Render provides 750 free instance hours per workspace per calendar month. The allowance resets monthly, not daily.
- A free Render web service spins down after 15 minutes without incoming traffic and can take about one minute to start again. Free Render is therefore publicly accessible but not guaranteed to stay warm 24/7.
- Render free web services have 512 MB RAM and 0.1 CPU, so the full local Docker stack must not run there.
- Render's filesystem is ephemeral. Do not rely on local uploads, SQLite, or generated artifacts surviving a restart.
- Hugging Face ZeroGPU is quota- and queue-limited. It is suitable for a thesis demonstration, not an unlimited production inspection service.
- AuraDB Free and Cloudinary Free have their own usage limits. Monitor their dashboards.

Official references:

- https://render.com/docs/free
- https://render.com/docs/compute-plans
- https://render.com/docs/disks
- https://neo4j.com/docs/aura/getting-started/create-instance/
- https://neo4j.com/docs/python-manual/current/connect/
- https://cloudinary.com/documentation/developer_onboarding_faq_free_plan

## 1. Prepare the compact inference assets

Generate complete normal features locally first. Then build compact cloud memory banks and normal-reference images:

```powershell
docker compose exec api python -m scripts.build_cloud_memory --features /app/features --output /app/cloud/space/assets
docker compose exec api python -m scripts.build_reference_gallery --dataset /app/mvtec_loco_ad --output /app/cloud/references --per-category 3
```

Confirm that every category has one `.pt` file under `cloud/space/assets/` and reference images under `cloud/references/<category>/`.

## 2. Deploy the Hugging Face Space

1. Obtain access to the gated DINOv3 model and create a Hugging Face read token.
2. Create a Gradio Space and upload the complete repository.
3. Configure `cloud/space/app.py` as the app entry point (the root README already declares it).
4. Enable ZeroGPU hardware.
5. Add `HF_TOKEN` as a Space secret so the gated DINOv3 files can be downloaded.
6. Wait for the Space to build, then test one inspection directly in its Gradio interface.

The Render gateway expects the Space endpoints named `/inspect` and `/ask`, which are already defined in the included Space application.

## 3. Create Neo4j AuraDB Free

1. Create one AuraDB Free instance.
2. Save the generated connection URI, username, and password immediately.
3. Open Neo4j Query and execute `docs/neo4j_setup.cypher` once.
4. Keep the credentials private. Never commit them to Git.

The resulting graph is:

```text
(Inspection)-[:INSPECTED_AS]->(ProductCategory)
(Inspection)-[:SUPPORTED_BY {rank, score}]->(Evidence)
(SupportMessage)
```

The application stores scores, bounding-box coordinates, visual reasoning, final explanation, evidence links, and cloud media URLs. Image binaries are not stored in Neo4j.

## 4. Create Cloudinary Free

1. Create a Cloudinary account.
2. Copy its `CLOUDINARY_URL` secret.
3. Leave `STORE_ORIGINAL_UPLOADS=false` unless users have explicitly consented to retaining their original images.

With the default privacy setting, only the generated localization overlay and heatmap are retained. Those derived images still contain the underlying uploaded product image. The exact original upload is used for inference and then discarded by the gateway. The website requires the user to acknowledge this before inspection.

## 5. Push the project to GitHub

Git LFS is required for compact `.pt` memory banks:

```powershell
git lfs install
git add .
git commit -m "Deploy DefectRAG cloud architecture"
git push
```

Do not commit `.env`, the raw `mvtec_loco_ad/` folder, the complete `features/` folder, downloaded model caches, or secret credentials.

## 6. Deploy to Render

1. In Render, create a new Blueprint from the GitHub repository.
2. Render reads `render.yaml` and builds `Dockerfile.render`.
3. Enter these secret values when prompted:

| Variable | Value |
| --- | --- |
| `HF_SPACE_ID` | `username/space-name` |
| `HF_TOKEN` | Read token; optional only when the Space is fully public and needs no authentication |
| `NEO4J_URI` | `neo4j+s://...databases.neo4j.io` |
| `NEO4J_PASSWORD` | AuraDB password |
| `CLOUDINARY_URL` | `cloudinary://...` secret |

4. Wait for `/api/health` to return successfully.
5. Open the provided `onrender.com` URL and test inspection, knowledge query, and contact submission.

## 7. Verify persistence

After one inspection, run this in Neo4j Query:

```cypher
MATCH (inspection:Inspection)-[:INSPECTED_AS]->(category:ProductCategory)
RETURN inspection.id, category.id, inspection.verdict,
       inspection.anomaly_score, inspection.created_at
ORDER BY inspection.created_at DESC
LIMIT 10;
```

Verify the generated `location` and `heatmap` assets in Cloudinary. Submit one contact form and verify it with:

```cypher
MATCH (message:SupportMessage)
RETURN message.id, message.topic, message.status, message.created_at
ORDER BY message.created_at DESC;
```

## Ground-truth terminology

The website shows a **dataset-verified normal reference**, not ground truth for an arbitrary user upload. True upload ground truth is unknowable unless a qualified reviewer or a labeled benchmark supplies it. The UI states this explicitly to avoid presenting a model prediction as fact.

MVTec LOCO AD is released under CC BY-NC-SA 4.0 and is explicitly non-commercial. Keep the visible attribution, retain the applicable license, and do not deploy dataset-derived reference images or memory banks as part of a commercial service without obtaining permission from MVTec. See https://www.mvtec.com/research-teaching/datasets/mvtec-loco-ad.

## Production upgrade path

For an always-warm service, predictable response time, private inference, or frequent usage, move Render to a paid instance and use a dedicated GPU inference service. Validate category thresholds on representative production data before using the system for acceptance decisions.
