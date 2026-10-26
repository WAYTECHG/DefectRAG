# Phase 3 — verified 18 October 2026

Live cloud RAG passed on `Wizzas/DefectRAG` commit
`a31f52b64c91b7d6dab34113bc17a5bfac37ff72`. Phase4 persistence and full Phase5
acceptance remain pending. No claim that all phases are complete.

| Verified item | Evidence |
|---|---|
| Real provider | In-Space Transformers Qwen/Qwen3-4B-Instruct-2507, revision cdbee75f17c01a7cc42f958dc650907174af0554 |
| Hardware | ZeroGPU RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb |
| First generated explanation | 1323 input tokens, 85 output tokens, 2464.80 ms measured generation; peak tracked PyTorch memory8601.55 MB |
| Contextual follow-up | 1551 input tokens,90 output tokens,2695.63 ms; peak8649.42 MB |
| Retrieval | Original BGE-small-en-v1.5 weights, CPU CLS pooling + L2 normalization, existing LangChain index/retriever |
| Evidence | Existing LangGraph routes/retrieval/evidence/answer validation; generated quote IDs must match retrieved passages and exact supporting sentences |
| Inspection link | Actual new cloud DINOv2 PCB1 inspection527791824aea4124b9f60ec9d173b048; saved score0.3130060434, Anomalous |
| Conversation | Measurement answer, generated heatmap explanation, generated contextual segmentation follow-up, and scope refusals; ten saved turns |
| Offline/local fallback | Existing local Ollama Qwen2.5:3b retained; targeted local RAG checks passed without a new model download |
| Software regression/security |44 existing focused tests +6 new isolation/access tests passed; real inference/generation evidence is separate from software fixtures |

These are individual observations, not latency/availability/load guarantees.
Generation time excludes CPU retrieval, GPU acquisition/transfer and network time.
Peak PyTorch allocation is not complete host/GPU memory. CPU and GPU resources are
shared; quotas/cold starts still apply. The default GPU allocation successfully
held both models; no quantization, larger/paid hardware or training was needed.

## Diagnosed compatibility problem and targeted correction

The first Qwen-enabled deployment packed8.65GB of immutable GPU tensors but its
worker failed at spaces.zero.torch.patching.init with `No CUDA GPUs are available`.
An unchanged retry failed before inference. Deferring startup BGE warm-up restored
vision; after the first CPU embedding request, generation showed the same worker
initialization error. This narrowed the problem to parent CPU embedding runtime
initialization interacting with the forked/emulated CUDA environment. The precise
internal CUDA probe was not isolated; it is not claimed to be a model OOM.

The fix runs existing CPU BGE loading and embedding in one bounded subprocess
within the same Space, with CUDA hidden and spaces/LLM initialization disabled.
It uses the same saved model, tokenization512, CLS/L2 pooling and query prefix.
No separate host/service or frontend architecture was introduced. IPC carries text
and vectors only; questions are not logged. A45-second wait bounds a stalled child.
The parent keeps the eagerly registered DINO/Qwen GPU tensors. Subsequent real
vision, retrieval and both generated answers passed. Startup/dependency versions
and model methodology remain unchanged.

Qwen's8,044,982,000 weight bytes download/cache in the Space, not on the laptop or
inside a new release ZIP. Original local environments and model assets remain.
Cloud requests disable Gradio run-history recording so upload bytes, browser
workspace secrets and staff JWT inputs are not copied into its generic history.

## Truthful answer behavior

Direct score/verdict questions use saved measurements and are labelled measurement
answers, without calling the LLM. General explanations call Qwen and are labelled
live generation only when the output passes validation. Unavailable/invalid
generation is labelled retrieval-only; retrieved excerpts are never presented as
generated answers. Named defects, root causes and repairs remain outside scope.
Citation/quote/numeric checks are narrow guards, not a complete entailment proof.

Public/sanitized records: docs/zerogpu_phase3/rag-summary.json. Private resumable
reports, signed capabilities and raw diagnostic logs remain under Git-ignored
development-support/space. No full benchmark, model fitting or experiment rerun.

## Phase4 gate and hardening notes

The user approved the reviewed deployment/supabase_additive_conversations.sql for
their MANUAL execution only. The agent must not execute migrations, create staff
accounts, weaken RLS or directly alter Supabase. Wait for their successful-execution
confirmation, then test staff success and anonymous/nonstaff RPC denial. A live
nonstaff test requires a real existing nonstaff account; software tests do not
substitute for that acceptance evidence.

Prepared code reuses existing tables/storage, staff JWTs and RLS, without a service
key. Staff persistence stays disabled until the manual-execution gate is met.
Future hardening explicitly requested by the user: staff-submitted answers lack
model provenance attestation; alert acknowledgements lack actor/timestamp.

Next: preserve this checkpoint, verify browser flows and staff sign-in, then enable
and test durable history/reports/conversations/notes/archive/recovery after the
manual migration confirmation. Continue authorized work without a phase approval
pause; respect this specific database gate.
