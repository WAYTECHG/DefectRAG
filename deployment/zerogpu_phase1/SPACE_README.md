---
title: DefectRAG - Phase 1 compatibility test
emoji: 🔬
colorFrom: purple
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12.12"
app_file: app.py
license: mit
pinned: false
short_description: Existing React UI plus one genuine DINOv2 ZeroGPU inspection
---

# Phase 1 only — not the production DefectRAG migration

This isolated proof preserves the existing React dashboard. Only one public VisA
PCB1 fixture is accepted for real DINOv2 scoring and heatmap generation.
Use **Image inspection**, choose **PCB 1**, select the **PCB 1 anomalous sample**,
then **Run inspection**. Alternatively upload the same supplied JPEG file.

No arbitrary private images are accepted. History here is temporary test data.
RAG/batch execution and cloud staff collaboration are not migrated or enabled.
The normal local application and its configured Supabase workspace remain intact.
Some local-runtime labels remain historical UI text; this test runs in the Space.

The test uses frozen DINOv2 ViT-S/14, its existing normal-reference bank and
unchanged operational threshold. No training or new accuracy evaluation occurs.
The Space requires configured ZeroGPU hardware; a CPU-only run is not proof of
ZeroGPU compatibility. Inspect the returned phase1 and device metadata.

VisA sample: Amazon Science, CC BY 4.0; Yang Zou, Jongheon Jeong, Latha Pemula,
Dongqing Zhang and Onkar Dabeer, SPot-the-Difference, ECCV 2022.
https://github.com/amazon-science/spot-diff
DINOv2: Meta, Apache-2.0. https://huggingface.co/facebook/dinov2-small
See docs/THIRD_PARTY_NOTICES.md and the bundled model license.
