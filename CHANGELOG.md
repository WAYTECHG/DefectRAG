# Changelog

## 3.0.0 — Cloud persistence and explainable localization

- Added a lightweight Render gateway that delegates GPU inference to the Hugging Face ZeroGPU Space.
- Added optional Neo4j AuraDB storage for inspections, evidence relationships, and support messages.
- Added optional Cloudinary storage for durable generated media while keeping original-upload retention opt-in.
- Replaced multiscale rectangles with a connected anomaly-region bounding box and explicit pixel coordinates.
- Added dataset-verified normal reference comparisons with an honest ground-truth disclaimer.
- Added reasoning-assurance statements that separate detector evidence, visual hypotheses, and sourced rules.
- Added a responsive navigation sidebar plus About, FAQ, Support, and Contact experiences.
- Added Render Blueprint, dedicated lightweight container, cloud setup guide, and AuraDB schema constraints.

## 2.1.0 — Professional inspection interface

- Rebuilt the browser experience as a polished, responsive product-quality dashboard.
- Added drag-and-drop image selection, preview metadata, client-side validation, and accessible keyboard controls.
- Added a staged analysis indicator with elapsed time and clear model-processing feedback.
- Added stronger verdict hierarchy, threshold visualization, localized image panels, structured visual evidence, and expandable sources.
- Improved service-readiness, error, loading, document-ingestion, and mobile states without changing the API contract.

## 2.0.0 — Visual inspection web workflow

- Added `POST /api/inspect` for validated image upload and category selection.
- Connected the existing DINOv3 normal-feature scorer to the FastAPI application.
- Added benchmark-derived category thresholds, anomaly verdicts, patch coordinates, location overlays, and heatmaps.
- Added multiscale visual reasoning through `qwen2.5vl:3b` and final grounded reporting through `qwen2.5:3b`.
- Added retrieved evidence cards and uncertainty details to the browser result.
- Added normal-only feature extraction for web inference.
- Added NVIDIA Docker Compose override for local GPU use.
- Added Hugging Face Gradio ZeroGPU deployment entry point and compact memory-bank builder.
- Retained direct document ingestion and knowledge-base querying as secondary tools.

## 1.0.0 — Document RAG application

- Added document extraction, chunking, FAISS + BM25 retrieval, Ollama grounded answers, FastAPI, browser UI, and Docker Compose.
