# Deployment options

- **Local FastAPI application:** follow [Setup](../docs/SETUP.md). The synchronized
  existing-installation launcher uses port8765; standalone mode can use8767.
- **Live Hugging Face Space:** the React frontend and Gradio Server/FastAPI adapter
  share queued DINO/Qwen inference. See [Space adapter](space/README.md).
- **Saved static showcase:** optional read-only examples, not a live inference
  service. Build with the frontend showcase mode and use STATIC_SPACE.md.
- **Optional Supabase/n8n services:** review schemas, feature flags and security
  boundaries before enabling them. See [Security](../docs/SECURITY.md).

Model assets and private environment configuration are separate from source.
Never expose privileged database, worker, callback or SMTP secrets in React.
Do not repeat migrations against an existing project without inspecting its schema.
