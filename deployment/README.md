# Deployment

The ready static ZIP is DefectRAG-static-upgrade.zip: 25 saved real examples,
recorded evidence and both 12-category evaluation reports. It runs on Vercel,
Render Static Site or Hugging Face Static Spaces without an AI server.
[Exact commands](RUN_AND_DEPLOY.md).

The Staff workspace optionally uses your own Supabase project for approved
sign-in, shared inspection snapshots, private images, notes and developer recovery.
No project has been created or connected. [Setup](SUPABASE_SETUP.md).
The supplied SQL is a single-organisation design; hosted access-control tests are
pending. Never put service-role or secret keys in frontend configuration.

New image inspection and generated answers need the separate Python backend and
local Ollama. Static hosting and Supabase do not run the GPU model. The ordinary
frontend build uses the live localhost API; its default single-user API must not
be exposed publicly without authentication, scoped storage, TLS and rate limits.
Browser inference and n8n are not implemented. No public deployment was created.
