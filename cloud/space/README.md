---
title: DefectRAG Visual Inspector
emoji: 🔎
colorFrom: green
colorTo: gray
sdk: gradio
python_version: 3.12.12
app_file: app.py
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

# DefectRAG Visual Inspector

Public research demonstration for MVTec LOCO AD anomaly localization and grounded visual reasoning. Configure the Space to use **ZeroGPU** after creation. The compact normal-memory files under `assets/` must be generated with `python -m scripts.build_cloud_memory` before this folder is uploaded.
