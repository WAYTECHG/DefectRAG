# Use the public DefectRAG application

Open https://huggingface.co/spaces/Wizzas/DefectRAG.

1. Sign in to your Hugging Face account to use its available GPU allowance. The
   direct https://wizzas-defectrag.hf.space link also loads the app, but guest
   quota can be smaller; use the HF-hosted page for authenticated GPU access.
2. In Staff workspace, sign in with an existing approved Supabase staff account.
   This is separate from HF sign-in. An unapproved account is not staff. The
   embedded HF app and direct app link can have separate browser storage, so each
   may require staff sign-in. No password/token belongs in this conversation.
3. In Image inspection, select the correct VisA product, optionally label the
   batch, then upload an image or choose a supplied preview. Run inspection once.
   Review the score against its threshold and the heatmap. Score is a feature
   distance, not accuracy or defect probability; the model does not verify the
   selected product category or diagnose named defects/root causes.
4. Ask the Evidence Assistant about that result. Measurement answers use saved
   inspection values. LIVE LLM · CITED answers use Qwen with retrieved documents.
   Retrieval-only and scope refusal are explicitly labelled. The assistant gets
   saved measurements/history; it does not independently inspect image pixels.
5. Signed-in inspections and conversations save to Supabase automatically. Staff
   workspace shows shared records and review notes. Main history opens the same
   saved measurements; Report/Export CSV use short-lived private links. Reopen a
   record if an image/report link expires.
6. Review alerts can be acknowledged without changing a model verdict. Clear
   history archives matching permitted records; it does not delete original files.
   Developer recovery restores archived shared records. Ordinary staff cannot
   use developer recovery. Existing role policies still govern access.
7. Batch monitoring accepts up to20 images,10MB each,20MB combined. Choose one
   product category and a batch label. Results save per image. After a quota
   rejection, later images are not submitted; successful prior results remain.
   Retry only unfinished images when free quota is available.

Without staff sign-in, anonymous history is isolated to that browser session and
temporary on Space restart. Authenticated Supabase records survive deployment
restarts, as verified by the saved acceptance fixture. Static showcase and local
application remain available separately; no new paid service is required.

GPU capacity, daily quotas and cold starts apply. Your ChatGPT Work allowance is
separate from HF GPU quota. The project does not purchase quota or embed an owner
HF token for public visitors. See ZEROGPU_PHASE5_RESULTS.md for exact verified
features, account-test gaps, security hardening limits and free-hosting scope.

## Existing local backup

```powershell
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Port 8767
```

Open http://127.0.0.1:8767. Local generated answers use existing Ollama
qwen2.5:3b; cloud Qwen runs in the HF Space. The migration did not replace the
local environment or rebuild its preserved static showcase.
