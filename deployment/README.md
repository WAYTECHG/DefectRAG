---
title: DefectRAG v2
emoji: 🔎
colorFrom: green
colorTo: blue
sdk: static
pinned: false
---

The free static showcase is implemented. Follow [RUN_AND_DEPLOY.md](RUN_AND_DEPLOY.md)
for Windows, Vercel, Render and Hugging Face instructions.
Build with `npm run build:showcase` in `frontend` and publish `frontend/dist-static`.
This build uses seven saved real examples and recorded conversations; no API
is needed. `DefectRAG-v2-static.zip` contains the ready-to-upload static files.
Routes use hashes, so no server-side rewrite is required.

The separate ordinary frontend build (`npm run build`, output `frontend/dist`)
uses the live backend. Set `VITE_API_URL` only when intentionally connecting that
build to an approved HTTPS inference service. The local API is deliberately
single-user and must not be exposed as-is.

Future public API requirements: model assets and licensed weights, bounded inference
workers, CPU/GPU resource benchmarking, TLS, upload and rate limits, isolated
short-lived anonymous sessions, scoped artifact URLs and storage retention.
Never connect a public frontend directly to local SQLite or a service-role key.
Supabase integration belongs behind `InspectionRepository`, with tenant identity
and row-level policies before public use. n8n may consume authenticated review
events; it must not overwrite image measurements or invent decisions.

Browser inference is not exported or claimed. DINOv3 transformer export, cosine
bank search, ONNX operator/WebGPU compatibility, memory, asset download size and
numerical equivalence need a separate measured conversion project. Until then,
public inference requires a separate service that stays online independently of
the owner's laptop. No cloud services have been provisioned.
