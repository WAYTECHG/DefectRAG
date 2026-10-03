---
title: DefectRAG Visual Inspector
emoji: 🔎
colorFrom: green
colorTo: gray
sdk: gradio
python_version: 3.12.12
app_file: cloud/space/app.py
fullWidth: true
models:
  - facebook/dinov3-vits16-pretrain-lvd1689m
  - Qwen/Qwen2.5-VL-3B-Instruct
  - Qwen/Qwen3-Embedding-0.6B
tags:
  - anomaly-detection
  - visual-inspection
  - rag
  - zero-gpu
---

# DefectRAG

**v7 project update:** visitor document uploads are disabled in both APIs and removed from the website. Knowledge changes go through developer-reviewed, source-linked offline preparation. The cloud page shows evidence coverage, elapsed timing, and a three-method image AUROC comparison. See [`docs/CURATED_REBUILD_AND_BENCHMARK.md`](docs/CURATED_REBUILD_AND_BENCHMARK.md) before deployment. Local Docker inspection is still baseline-only; the cloud Space handles method selection.

DefectRAG is an industrial visual inspection application for MVTec LOCO AD. A user uploads a product image and chooses its category. The system compares DINOv3 image patches with normal training features, produces a location overlay and anomaly heatmap, asks a vision language model to describe the suspicious area, retrieves relevant inspection knowledge through FAISS + BM25 reciprocal rank fusion, and produces a final evidence-grounded explanation.

## End-to-end workflow

```text
Uploaded product image
        ↓
DINOv3 patch features
        ↓
Nearest-normal patch comparison
        ↓
Anomaly score + strongest patch + heatmap
        ↓
Full image + small/medium/large crops → Qwen2.5-VL
        ↓
Visual observation → hybrid FAISS/BM25 retrieval
        ↓
Qwen2.5 grounded report with retrieved evidence
        ↓
FastAPI web result: verdict, location, reason, sources
```

The operating thresholds bundled in `app/inspection_service.py` were calculated from `results/all_categories/all_categories_scores.csv` using Youden's J statistic. They are benchmark operating points rather than probabilities or factory acceptance specifications.

## Required folder layout

Place the MVTec LOCO AD dataset at the project root. Normal feature files are generated into `features/`.

```text
DefectRAG/
├── mvtec_loco_ad/
│   ├── breakfast_box/
│   ├── juice_bottle/
│   ├── pushpins/
│   ├── screw_bag/
│   └── splicing_connectors/
├── features/
├── app/
├── data/
├── retrieval/
└── docker-compose.yml
```

## Local Docker setup

Prerequisites: Docker Desktop and its Compose plugin. From the folder containing `docker-compose.yml`:

```powershell
docker compose up --build -d
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama pull qwen2.5vl:3b
```

Generate the normal reference features required by the image inspector:

```powershell
docker compose exec api python -m scripts.extract_loco_features `
  --dataset /app/mvtec_loco_ad `
  --output /app/features `
  --normal-only
```

PowerShell uses the backtick above for line continuation. The same command on one line is:

```powershell
docker compose exec api python -m scripts.extract_loco_features --dataset /app/mvtec_loco_ad --output /app/features --normal-only
```

Open <http://localhost:8000>. The first inspection downloads and loads the DINOv3 and Qwen embedding models, so it takes longer than later requests.

### NVIDIA GPU on Docker Desktop

The included GPU override passes the available NVIDIA GPU to the API and Ollama containers:

```powershell
docker compose down
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

Check GPU visibility:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec api python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"
```

Docker Desktop must have WSL 2 GPU support available. If GPU passthrough is unavailable, use the standard Compose command; the workflow still runs on CPU but will be much slower.

## Website result

`POST /api/inspect?category=<category>` accepts an image in the `file` multipart field and returns:

- dataset-derived anomaly verdict, score, and threshold;
- strongest DINOv3 patch coordinates;
- full-image location overlay and patch-distance heatmap;
- visual model observation and uncertainty;
- final reasoned report grounded in retrieved documents;
- exact knowledge passages used by the report.

Other endpoints:

- `GET /api/health` — retrieval, Ollama, and category readiness;
- `GET /api/categories` — supported categories and feature availability;
- `POST /api/ask` — direct knowledge-base question;
- `POST /api/documents` — disabled (403); reviewed knowledge is indexed offline by the developer;
- `GET /docs` — interactive OpenAPI documentation.

## Document RAG workflow

Developer-reviewed documents are prepared offline, embedded with `Qwen/Qwen3-Embedding-0.6B`, stored in a normalized FAISS inner-product index, and combined with BM25 through reciprocal rank fusion. The public website does not accept document uploads.

The bundled index has 13 general or category-overview records and **no approved product-specific inspection rules**. Add verified, reviewed rules before treating product specifications or root-cause claims as supported. The report states this limit when a rule is missing.

## Free public cloud deployment

The project includes a Hugging Face Gradio ZeroGPU entry point at `cloud/space/app.py`. The public version uses Transformers directly and does not run Ollama in the Space.

### 1. Build compact cloud memory banks

After local normal features have been generated, run:

```powershell
docker compose exec api python -m scripts.build_cloud_memory --features /app/features --output /app/cloud/space/assets
```

This creates one compact `.pt` memory bank per ready category. These files are necessary for cloud inference; the raw dataset and complete `features/` directory are not uploaded.

### 2. Create the Space

Create a public Hugging Face Space using the **Gradio** SDK, upload the complete repository, and select **ZeroGPU** in the Space hardware settings. A free personal account must be in good standing, have a verified email, and be older than 30 days to host ZeroGPU. The project root `README.md` already points Spaces to `cloud/space/app.py`.

Large `.pt` memory-bank files are configured for Git LFS through `.gitattributes`.

### 3. Free-tier limits

ZeroGPU has no hourly hosting charge, but it uses a shared queue and daily GPU quotas. Public unauthenticated visitors currently receive less daily GPU time than signed-in free users. The Space may also sleep while unused. This supports a public portfolio or thesis demonstration; it does not provide unlimited always-on inference.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-0.6B` | Dense retrieval model |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Final text report model for local Docker |
| `OLLAMA_VISION_MODEL` | `qwen2.5vl:3b` | Local visual reasoning model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `FEATURES_DIR` | `features` | Normal DINOv3 feature root |
| `RESULTS_DIR` | `results/runtime` | Generated overlays, heatmaps, and crops |
| `MAX_UPLOAD_MB` | `20` | Upload size limit |

## Verification

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app knowledge retrieval rag vision scripts cloud
```

The archive does not contain the MVTec LOCO AD dataset, complete feature directory, downloaded Hugging Face models, or Ollama model files.

The cloud website can select the compact baseline, trained head, or fixed fusion per inspection. Trained/fusion scores remain uncalibrated research outputs without a binary verdict. See [`docs/TRAINING_AND_EVALUATION.md`](docs/TRAINING_AND_EVALUATION.md) for checkpoint deployment and [`docs/RAG_EVALUATION.md`](docs/RAG_EVALUATION.md) for a labeled retrieval benchmark; image AUROC is not a RAG quality metric.

## Train a one-class head and measure it

The original DINOv3 encoder is pretrained and frozen; building normal-memory banks is not model training. To run a genuine, reproducible 30-epoch training experiment on normal image patches and evaluate it against the deployed compact baseline, follow [`docs/TRAINING_AND_EVALUATION.md`](docs/TRAINING_AND_EVALUATION.md). The experiment reports image-level AUROC and average precision for normal, logical, and structural test images. Training does not guarantee better anomaly detection. The website stays in baseline mode until you independently calibrate thresholds for a trained detector.

## Render + AuraDB cloud architecture

Version 3 adds a lightweight public-cloud path designed around free-tier constraints:

- Render serves the professional FastAPI website and validates requests through `app/render_main.py`.
- Hugging Face ZeroGPU performs DINOv3 anomaly detection and Qwen-VL reasoning.
- Neo4j AuraDB stores inspection records, evidence relationships, and contact/support messages.
- Cloudinary stores generated bounding-box overlays and heatmaps; original-upload retention is disabled by default.
- The result page shows one connected anomaly-region bounding box, exact coordinates, a heatmap, a known-normal reference, grounded reasoning, sources, and uncertainty.

Deploy with the included `render.yaml` and `Dockerfile.render`. Follow the complete step-by-step guide in [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md).

Render's 750 free instance hours reset each calendar month, not daily. A free web service still sleeps after 15 minutes without traffic, so it is publicly reachable but not guaranteed to remain warm continuously. The full AI stack cannot fit Render's free 512 MB instance; this is why GPU inference is delegated to the Space.
