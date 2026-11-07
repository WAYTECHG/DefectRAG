# Model card: DefectRAG evidence generator (fine-tuned Qwen2.5-3B-Instruct)

Version of 2026-11-07. The numbers come from `docs/QWEN_FINETUNING_RESULTS.md`, which holds the permanent copy of the
measurements (the raw run files are not in the repository).

**Improved using Qwen.** Built from Qwen2.5-3B-Instruct under the Qwen Research License: the fine-tuned model is for
non-commercial use and is not covered by this repository's MIT licence.

## Model details

* **What it is:** Qwen2.5-3B-Instruct (Alibaba Cloud) fine-tuned with QLoRA to do one narrow job in the DefectRAG
  assistant: given a question and a few numbered sentences retrieved from the project's attributed documents, choose the
  sentence that answers it and restate it briefly, or return no claim when the documents cannot answer. The system then
  checks every quoted sentence against the retrieved text before showing an answer.
* **Method:** QLoRA. The base model is loaded in 4-bit (NF4) only to save memory while training and is kept frozen. Small
  low-rank adapters (rank 16) on the attention (q, k, v, o) and feed-forward (gate, up, down) layers are the only trained
  weights: 29.9 M of 3.1 B parameters (0.96%), in 16-bit. After training the adapter was merged back into normal 16-bit
  weights (about 6 GB), which is what the hosted Space serves; a Q8_0 GGUF copy runs in Ollama for the local app
  (`qwen-defectrag-v2`).
* **Where it runs:** the Hugging Face Space (ZeroGPU, bf16, greedy decoding) loads the private repository
  `Wizzas/defectrag-qwen2.5-3b-evidence` at a pinned commit with a read-only token. The local app uses Ollama.
* **Code:** `scripts/qwen_build_training_data.py`, `qwen_finetune.py`, `qwen_merge.py`, `qwen_eval.py`,
  `qwen_compare.py`; walk-through in `docs/QWEN_FINETUNING_GUIDE.md`.
* **Author:** the project owner. **Licence:** Qwen Research License (non-commercial); the licence text and the
  "Improved using Qwen" notice are shipped with the model and the notices.

## Intended use

* Explaining DefectRAG inspection results and its own documentation with quoted, cited evidence, inside the dashboard,
  next to the saved measurements (score, threshold, model ID), which are shown separately and are not generated.
* Demonstrating retrieval-grounded answering that refuses when the documents are silent.

**Out of scope:** general chat or open-ended questions; any question whose answer is not in the retrieved documents
(it should return no claim); safety, medical, legal or quality-release decisions; commercial use (licence); use as a
source of facts about industrial standards, which the documents do not provide.

## Training data

* 400 examples (360 train, 40 validation), each a production-style prompt (the question plus the retrieved, numbered
  sentences) and the wanted JSON answer: the id of the answering sentence and a short restatement, or `{"claims": []}`
  for questions the documents cannot answer. They cover every sentence of the 67-sentence knowledge base, in
  question wordings written for the project with AI help.
* Test questions were never used for training; near-copies were refused (Jaccard similarity 0.7).
* Training: 3 epochs, 135 steps, learning rate 2e-4, 8 examples per step, loss on the answer only. 50.5 minutes and
  5.9 GiB peak on one 8 GB laptop GPU.

## Evaluation

Scoring is strict: an answer counts only if every quoted sentence is the expected one. Retrieval found the right text
in 80 of 80 test questions, so the figures measure the generator, not retrieval.

The same Qwen2.5-3B was measured before and after fine-tuning in each runtime (100 held-out questions, 80 answerable,
20 that the documents cannot answer):

| Runtime | Before: fully correct | Before: unanswerable answered | After: fully correct | After: unanswerable answered | Seconds per answer (after) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Python test server, 4-bit | 34/80 (42%) | 6/20 | 71/80 (89%) | 0/20 | 11.6 |
| Ollama, output format enforced (the laptop app) | 49/80 (61%) | 8/20 | 69/80 (86%) | 0/20 | 1.1 |
| Hugging Face Space, bf16, no enforced format | not measured | | 74/80 (92%) | 2/20 | 2.6–2.9 |
| For reference: Qwen3-4B-Instruct-2507 in Ollama (the earlier cloud model) | 38/80 (48%) | 0/20 | | | 1.5 |

The "before" figures differ between runtimes because Ollama forces the answer into the expected JSON shape; the model
weights are the same. Compare along a row.

On 33 newcomer-style questions (23 answerable) the fine-tuned model scored 56–65% against 30% for the previous model;
those intervals overlap (about ±18 points), so treat that as a trend. The lenient view ("is the right sentence among
those quoted?") shows that Qwen3-4B finds the right sentence about as often as the fine-tuned model but adds
extra sentences, which the strict rule marks wrong. **The fine-tune's contribution is focus and refusing
out-of-scope questions, not better recall.**

## Limitations and known failures

* **Weak evidence base:** the training questions, the 100 test wordings and the 33 newcomer questions were all written
  with AI help by the same author and cover the same 67 sentences. Real users may do worse. Strict scoring also undercounts
  reasonable alternative sentences, so it is fair between models but not an absolute accuracy.
* **Retrieval limits it:** for 4 of 23 newcomer questions the right text is never retrieved, whatever the model does.
* **Known failure:** "Who paid for the VisA benchmark?" (not in the documents) was answered with the related sentence about
  the dataset licence, twice. In a live check of five questions on the Space, one answerable question ("The result says
  Good. Can I stop checking this product?") got the wrong sentence; this is a smoke test, not an evaluation.
* **It does not add knowledge.** It selects and restates retrieved sentences; it cannot answer from outside them.
* **Speed** comes from the runtime, not the fine-tune: the same model took 10–17 s on a test server and 1–3 s in Ollama
  or plain Transformers.
* **Not evaluated:** other languages, long conversations, adversarial prompts and sustained load.

## How to use

Locally: install Ollama, create the model from the merged weights as described in `docs/QWEN_FINETUNING_RESULTS.md`
("Commands"), and set `OLLAMA_MODEL=qwen-defectrag-v2` in `.env`. Without it the app falls back to `qwen2.5:3b`.
On the Space the model is loaded automatically from the private repository.

## Citations and licences

* Qwen Team, *Qwen2.5 Technical Report*, 2024. Qwen Research License (non-commercial).
* Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs*, NeurIPS 2023.
* Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models*, ICLR 2022.
* Third-party notices: `docs/THIRD_PARTY_NOTICES.md`.
