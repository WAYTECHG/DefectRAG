# Qwen fine-tuning: results, decisions and how to repeat them

Written 2026-11-06. Everything here was measured on the owner's laptop (RTX 4060 Laptop, 8 GB). The raw files live in
`experiments/qwen_lora_v1/` (git-ignored, so **this page is the permanent copy of the numbers**).
How to run the training yourself step by step: [QWEN_FINETUNING_GUIDE.md](QWEN_FINETUNING_GUIDE.md).

## One-paragraph summary

QLoRA fine-tuning of Qwen2.5-3B-Instruct (4-bit base, 1% of weights trained, about 50 minutes) made the evidence assistant
pick the right quoted sentence far more often and stop answering questions the documents cannot answer. On 100 test
questions the strict score rose from 42% (same base model, same server) to 89%, and from 61% for the deployed Ollama
`qwen2.5:3b` to 86-92%. On 33 newcomer-style questions it rose from 30% (Ollama) to 56-65%, but those confidence
intervals overlap. The fine-tuned model runs in Ollama at about 1-2 seconds per answer. Plain Qwen3-4B (the cloud model)
finds the right sentence about as often as the fine-tuned 3B but adds extra sentences, so it scores low under the strict
rule.

## What was trained

| | Version 1 | Version 2 (the one used) |
|---|---|---|
| Base model | Qwen2.5-3B-Instruct, local copy `experiments/qwen_lora_v1/base_model` (checksums verified) | same |
| Method | QLoRA: 4-bit NF4 base, LoRA rank 16 on q,k,v,o,gate,up,down; 29.9 M of 3.1 B weights trained (0.96%) | same |
| Training examples | 168 | 400 (360 train, 40 validation) = the 168 plus 232 conversational questions covering every knowledge sentence |
| Settings | 3 epochs, learning rate 2e-4, 8 examples per step, max 2048 tokens, loss only on the answer | same, 135 steps |
| Time / memory | 37.9 min | 50.5 min, peak 5.9 GiB GPU |
| Validation loss | ended 0.0179 | 0.6163 before, 0.0547, 0.0395, 0.0423 after epochs 1-3 |
| Output folder | `adapter/` | `adapter_v2/` (120 MB) |

Each example is the production prompt (retrieved, numbered sentences) plus the wanted answer: the id of the sentence that
answers the question and a short restatement, or `{"claims": []}` when the documents cannot answer.
Test questions were never used for training (near-copies are refused: Jaccard similarity 0.7).

## The models that were compared (tags in `experiments/qwen_lora_v1/runs/`)

| Tag | What it is | How it was run |
|---|---|---|
| `ollama` / `gate50` | deployed `qwen2.5:3b` (same model, two runs: your questions / test questions) | Ollama, output format forced |
| `basehf` | untouched Qwen2.5-3B | test server (4-bit, `scripts/qwen_serve.py`) |
| `lora` | fine-tuned v1 | test server |
| `lora2` | fine-tuned v2 | test server |
| `lora2gguf` | fine-tuned v2 merged and converted (Q8_0) | Ollama model `qwen-defectrag-v2`, format forced |
| `qwen3` | plain Qwen3-4B-Instruct-2507 (the Space's model), 4-bit file | Ollama, format forced |
| `spacestyle` / `spacestyle_me` | fine-tuned v2 merged, bf16, **format not forced, Space's prompt wrapper** | in-process (`--local-model`) |
| `plainstyle` | same, but the plain training prompt | in-process |

## Results

"Mine" = 33 newcomer-style questions written for the project (23 answerable, 10 not). "Test" = 100 held-out wordings
(80 answerable, 20 not). Strict = the answer is correct only if every quoted sentence is the expected one.

### Strict score, 33 newcomer questions (23 answerable)

| Model | Fully correct | Wrong sentence | No answer though one exists | Answered an unanswerable (of 10) | Sec/answer |
|---|---|---|---|---|---|
| Ollama qwen2.5:3b | 7/23 (30%) | 16 | 0 | 3 | 1.5 |
| Base 3B, test server | 2/23 (9%) | 17 | 4 | 4 | 17.2 |
| Fine-tuned v1 | 5/23 (22%) | 15 | 3 | 0 | 12.1 |
| Fine-tuned v2, test server | 13/23 (56%) | 8 | 2 | 0 | 10.8 |
| **Fine-tuned v2, Ollama (Q8_0)** | **13/23 (56%)** | 6 | 4 | 0 | **1.8** |
| **Fine-tuned v2, Space-style** | **15/23 (65%)** | 8 | 0 | 0 | 2.2-2.6 |
| Fine-tuned v2, plain prompt | 14/23 (61%) | 3 | 6 | 0 | 2.1 |
| Plain Qwen3-4B (Ollama) | 1/23 (4%) | 22 | 0 | 0 | 3.2 |

The right chunk is retrieved for 19 of 23 questions in every case (83%); that limit is retrieval, not the model.

### Strict score, 100 test questions (80 answerable)

| Model | Fully correct | Wrong sentence | No answer though one exists | Answered an unanswerable (of 20) | Sec/answer |
|---|---|---|---|---|---|
| Ollama qwen2.5:3b | 49/80 (61%) | 28 | 3 | 8 | 0.9 |
| Base 3B, test server | 34/80 (42%) | 34 | 12 | 6 | 15.7 |
| Fine-tuned v1 | 65/80 (81%) | 8 | 7 | 0 | 12.6 |
| Fine-tuned v2, test server | 71/80 (89%) | 7 | 2 | 0 | 11.6 |
| **Fine-tuned v2, Ollama (Q8_0)** | **69/80 (86%)** | 9 | 2 | 0 | **1.1** |
| **Fine-tuned v2, Space-style** | **74/80 (92%)** | 6 | 0 | **2** | 2.6-2.9 |
| Plain Qwen3-4B (Ollama) | 38/80 (48%) | 41 | 1 | 0 | 1.5 |

Retrieval found the right chunk for 80/80 in every run. All runs had 0 unusable outputs. Confidence intervals are 95%
Wilson intervals; on 23 questions they are about +/-18 points wide, so a gap of 1-2 questions is noise.

### Lenient view: "is the right sentence among the quoted ones?"

| | 33 questions (of 23) | 100 questions (of 80) | Sentences per answer |
|---|---|---|---|
| Ollama qwen2.5:3b | 9 | 55 | 1.2-1.3 |
| Fine-tuned v2 (Ollama) | 15 | 72 | 1.0-1.25 |
| Plain Qwen3-4B | 16 | 75 | 1.8-2.0 |

Plain Qwen3-4B finds the right sentence as often as the fine-tuned 3B but returns about two sentences, so the strict
rule marks it wrong. The fine-tune's real contribution is **focus and refusing out-of-scope questions**, not better
recall. The extra Qwen3 sentences are real validated quotes; whether they are harmful was not judged by hand.

### Space-style details

The Space generates with plain Transformers: bf16, greedy decoding, **no forced output format**, its own prompt wrapper
(system message plus `JSON schema: ...`). Run in-process the fine-tuned model produced valid output every time.
The only failure to refuse was "Who paid for the VisA benchmark?" (asked twice); it answered with the related sentence
"The VisA dataset is released by Amazon Science under CC BY 4.0." The plain training prompt never did this on the 33
questions but gave no answer to 6 of 23 answerable ones (more cautious). Reproduced exactly by the owner in their own
terminal (tag `spacestyle_me`).

## What the numbers do and do not show

* Fine-tuning clearly beats the **same base model** (42% to 89% on test) and the deployed Ollama model on test (61% to
  86-92%) and on out-of-scope questions (Ollama answered 3/10 and 8/20; fine-tuned 0/10 and 0-2/20).
* It does **not** beat Qwen3-4B at finding the sentence; it matches it with fewer extra sentences.
* The fine-tune does not add knowledge or fix retrieval; 4 of the 23 newcomer questions never retrieve the right chunk.
* Speed comes from the runtime, not from fine-tuning: the same model took 10-17 s on my test server and 1-3 s in Ollama
  or plain Transformers.
* **Weak spot of the evidence:** the training questions, the 100 test wordings and the 33 questions were all written with
  AI help by the same author, and all cover the same 67 knowledge sentences. Real users may do worse. Adding 5-10 of the
  owner's own questions to the end of `my_questions.csv` is the best fix. Strict scoring also undercounts reasonable
  alternative sentences; it is fair between models, not an absolute accuracy.
* The first-ever scoring of `basehf` on the 33 questions showed 0/26 unusable; the corrected figure is 1/27 (a counting
  fix made later). It changes no conclusion.

## Other things that were learned or fixed

* Retrieval bug found and fixed in `backend/rag.py` (the question text sent to the retriever); similarity cutoff
  `MIN_SIMILARITY = 0.50` chosen from a sweep (`scripts/qwen_short_questions.py`). These edits are local and were not
  published unless later committed.
* An evaluation run with no server used to save junk rows; `scripts/qwen_eval.py` now refuses a dead server and stops
  after 3 failures in a row.
* Loading the 5 GB merged model file caused a memory spike that the system stopped; re-saving as 1 GB pieces
  (`merged_v2_small`) fixed it.
* Ollama 0.40.14 cannot import a raw Qwen2 model folder (its MLX importer rejects it) and offers no `q4_K_M`
  quantization for that route. What worked: merge, convert with llama.cpp's `convert_hf_to_gguf.py --outtype q8_0`
  (needed `sentencepiece`, installed into a scratch folder, not the environment), then `ollama create`.
* Qwen3-4B was smoke-tested for training: fits in 8 GB (peak 6.7 GiB) but takes about 51 s/step (about 1 h 55 min for 3
  epochs, about 77 min for 2). Not trained.

## Licences

* Qwen2.5-3B: **Qwen Research License** (non-commercial). Anyone distributing a model built from it must show
  "Improved using Qwen" and include the licence. Fine for a portfolio; not for commercial use.
* Qwen3-4B-Instruct-2507: Apache-2.0 (the licence file in the download was verified). No longer used by the app.
* `docs/THIRD_PARTY_NOTICES.md`, the README references and the in-app help text carry the "Improved using Qwen" notice.

## Decision (2026-11-06): plan A

Use the fine-tuned Qwen2.5-3B everywhere (local app and Space) because it is measured, almost as good as Qwen3-4B at
finding the sentence, and cheaper to run. Qwen3-4B fine-tuning (about 2 h) was not started.
Status (2026-11-06, done): **the Space and the local app both use the fine-tuned model.**
* The merged model was uploaded to a **private** Hugging Face repo, `Wizzas/defectrag-qwen2.5-3b-evidence`,
  commit `e6308fa8d6428895403d62e6ba77bcf6555a540d` (20 files, 6.19 GB; every weight file's SHA-256 matches the local
  copy; model card and Qwen licence included).
* The Space downloads it with a read-only token stored as the Space secret `HF_TOKEN` (token `defectrag-space-read`,
  allowed to read only that one repo). The commit is pinned in `deployment/space/generation.py`
  (`DEFECTRAG_MODEL_REVISION` overrides it). Published as Space commit `15fe847`; the previous files are in
  `development-support/space/server-rollback-2e6e467a4568` (publish those back to roll back).
* The local app reads `OLLAMA_MODEL=qwen-defectrag-v2` from the git-ignored `.env`. Delete that line to return to
  `qwen2.5:3b`. The code default stays `qwen2.5:3b` so a fresh clone works without the custom model.
* `scripts/space_dry_run.py` was the preview of the switch. It now stops with "no longer contains the expected block"
  because the change has been made; keep it only as a record or delete it.

### Live check on the Space (manual, 5 questions, one saved Candle inspection, 2026-11-06)

This is a smoke test, not an evaluation. The offline tables above are the measurement.

| Question | Live result |
|---|---|
| Who paid for the VisA benchmark? (not in the documents) | No claim, evidence-only fallback: correct |
| What does the number called anomaly score actually mean? | Correct sentence, `[screening-2]` |
| What should I do after I see a warning on a result? | Correct sentence, `[screening-5]` |
| My result says Uncertain. Does that mean the system is broken? | Answered from the saved result (no model call); the premise did not match the inspection, which was Anomalous |
| The result says Good. Can I stop checking this product? | **Wrong sentence** (`[screening-2]`, about "Anomalous"); offline, the same model quoted the right one |
| What does the AUROC measure? (my choice of test question) | No claim: the documents only say how the overall AUROC is averaged, so this is correct behaviour |

Likely reason for the miss (not verified): the live app adds the saved inspection to the prompt, which said Anomalous
while the question said Good; the offline runs had no saved inspection. One miss in four answerable questions is in line
with the measured strict rate (65% on the 33 newcomer questions), but is too few to compare with it.

## Where everything is

| What | Path |
|---|---|
| Trained adapters | `experiments/qwen_lora_v1/adapter/` (v1), `adapter_v2/` (v2) |
| Merged model, 1 GB pieces | `experiments/qwen_lora_v1/merged_v2_small/` (the folder uploaded to Hugging Face). The duplicate `merged_v2/` was deleted on 2026-11-06; `python -m scripts.qwen_merge` recreates it from `adapter_v2/` |
| GGUF for Ollama | `experiments/qwen_lora_v1/merged_v2_q8.gguf` (3.3 GB), `Modelfile_v2` |
| Ollama models | `qwen-defectrag-v2` (fine-tuned), `qwen2.5:3b` (original, untouched) |
| Plain Qwen3-4B | Deleted on 2026-11-06 (Ollama model `qwen3:4b-instruct-2507-q4_K_M` and the 8 GB `experiments/qwen3_4b_base/` download). Its results stay in `runs/*qwen3*` and `summary_qwen3_*.json`; to repeat them, download `Qwen/Qwen3-4B-Instruct-2507` (Apache-2.0) again |
| Training data | `experiments/qwen_lora_v1/data/train.jsonl` (v1), `train_v2.jsonl` (v2), `v2_questions.csv`, `my_questions.csv` |
| Per-question results | `experiments/qwen_lora_v1/runs/<tag>_<split>.jsonl`, summaries `summary_<tag>_<split>.json` |
| Scripts | `scripts/qwen_eval.py`, `qwen_compare.py`, `qwen_build_training_data.py`, `qwen_finetune.py`, `qwen_serve.py`, `qwen_merge.py`, `qwen_short_questions.py` |

## Commands

Set up a PowerShell once:

```powershell
cd C:\Users\User\desktop\defectrag-v2
$APP = "C:\Users\User\anaconda3\envs\defectrag\python.exe"
$env:PYTHONUTF8 = "1"; $env:USE_TF = "0"
```

Train v2 (about 50 minutes, close other GPU users first):

```powershell
& $APP -m scripts.qwen_finetune --model experiments\qwen_lora_v1\base_model --data experiments\qwen_lora_v1\data\train_v2.jsonl --out experiments\qwen_lora_v1\adapter_v2
```

Merge into a plain model (GPU, small RAM):

```powershell
& $APP -m scripts.qwen_merge --adapter experiments\qwen_lora_v1\adapter_v2 --out experiments\qwen_lora_v1\merged_v2_small
```

Measure it the way the Space runs it (new tag so old rows are not reused):

```powershell
$M = "experiments\qwen_lora_v1\merged_v2_small"
& $APP -m scripts.qwen_eval --local-model $M --style space --split mine --tag mytag
& $APP -m scripts.qwen_eval --local-model $M --style space --split test --tag mytag
& $APP -m scripts.qwen_compare --split mine lora2gguf mytag
```

Measure the Ollama version: `& $APP -m scripts.qwen_eval --split mine --model qwen-defectrag-v2 --tag mytag2`.

Use it in the local app: put `OLLAMA_MODEL=qwen-defectrag-v2` in `.env`. Switch back by removing the line (default
`qwen2.5:3b`). The Python tests pass with this setting (240 passed, 2 skipped).

Rebuild the Ollama model from the merged folder (needs a llama.cpp checkout for `convert_hf_to_gguf.py`):

```powershell
& $APP <llama.cpp>\convert_hf_to_gguf.py experiments\qwen_lora_v1\merged_v2_small --outfile experiments\qwen_lora_v1\merged_v2_q8.gguf --outtype q8_0
cd experiments\qwen_lora_v1; ollama create qwen-defectrag-v2 -f Modelfile_v2
```

## Resume wording that the numbers support

> Fine-tuned Qwen2.5-3B with QLoRA (4-bit, 8 GB laptop GPU) on 400 retrieval-grounded examples. On 100 held-out
> questions, strict correct-source answers rose from 42% (base model) to 89%, and answers to out-of-scope questions fell
> from 30-40% (deployed model) to 0-10%. Evaluated with confidence intervals and a separate set of newcomer-style
> questions; exported to GGUF and served in Ollama at 1-2 s per answer.

Do not claim: that it beats Qwen3-4B at finding the answer; that the gain holds for real users (the questions are
AI-written); or that the Space already uses it (until it does).
