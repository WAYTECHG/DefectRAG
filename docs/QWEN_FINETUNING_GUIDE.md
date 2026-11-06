# Fine-tuning Qwen for the evidence assistant: run it yourself

Everything below runs in the VS Code terminal (PowerShell), from the project folder.
**Nothing here has been trained yet.** You run the training.

## What you are doing, in one paragraph

The assistant retrieves numbered sentences from the knowledge documents. Qwen's only jobs are to
pick the sentence that answers the question and restate it, or to return **no claim** if nothing
fits. On held-out questions the untouched model picked a wrong sentence in 35% of answers and
answered 8 of 20 unanswerable questions (all 8 "near-miss" questions). You will teach it the right
behaviour with **QLoRA**: the 3-billion-parameter model stays frozen and compressed to 4 bits, and
only small extra matrices (about 1% of the size) are trained. The result is a small adapter file.

## Where things stand before you start

| Measured on the 100 held-out test questions | Result |
|---|---|
| Right sentence retrieved | 80/80 (after the retrieval fixes) |
| Fully correct answers | 49/80 = 61% |
| Wrong sentence chosen | 28/80 = 35% |
| Answered an unanswerable question | 8/20 = 40% |

Your job is to see whether fine-tuning moves the last two numbers, and to report honestly what happens.

## One-time setup (every new terminal)

```powershell
cd C:\Users\User\desktop\defectrag-v2
$APP = "C:\Users\User\anaconda3\envs\defectrag\python.exe"      # the app environment
$FT  = $APP    # one environment: the training libraries are installed in "defectrag" too
$env:PYTHONUTF8 = "1"
$env:USE_TF = "0"
```

One environment is enough. The training libraries (peft 0.21.2, bitsandbytes 0.50.2, accelerate,
lm-format-enforcer) were added to `defectrag` and checked: nothing already installed changed
(transformers is still 4.57.6) and the app's lint, mypy, API check and tests still pass.
The older `defectrag-ft` environment is no longer needed; remove it any time with
`conda env remove -n defectrag-ft`. `$FT` is kept as an alias so every command below still works.

## The base model is stored in the project

The base model (Qwen2.5-3B-Instruct, about 6 GB) was downloaded to `experiments\qwen_lora_v1ase_model`
with `curl`, because Hugging Face's Python downloader kept stalling on this machine. That folder is not
copied into Docker or GitHub. Every command below passes it explicitly with `--model` or `--base`.
Check the two big files are intact (sizes and SHA-256 from Hugging Face are in `base_model_expected.json`):

```powershell
Get-ChildItem experiments\qwen_lora_v1ase_model\*.safetensors | Select-Object Name, @{n="GB";e={[math]::Round($_.Length/1GB,2)}}
(Get-FileHash experiments\qwen_lora_v1ase_model\model-00001-of-00002.safetensors -Algorithm SHA256).Hash
```

The hash must start with `67347b23fb4165b6` for file 1 and `a40d941d0e7e0b96` for file 2.

## Step 1: look at the baseline

```powershell
& $APP -m scripts.qwen_compare base retrievalfix gate50
```

## Step 2: look at what the model will learn from

The 168 training examples are already built (`& $APP -m scripts.qwen_build_training_data` rebuilds them;
it needs Ollama running). Read the answers the model should produce:

```powershell
Get-Content experiments\qwen_lora_v1\data\train.jsonl | ForEach-Object { ($_ | ConvertFrom-Json) } |
  Select-Object -First 12 topic, kind, completion | Format-List
```

Look for the `unanswerable` rows: their completion is `{"claims": []}`. That is the lesson "say nothing
when the evidence does not answer the question".

## Step 3: dry run (2 steps, checks that everything works)

The first run downloads the base model (about 6 GB, once).

```powershell
& $FT -m scripts.qwen_finetune --model experiments\qwen_lora_v1\base_model --limit 24 --max-steps 2 --epochs 1 --accum 4 --out experiments\qwen_lora_v1\adapter_smoke
```

You should see: the GPU name, "examples: ... train, ... validation", the trainable-parameter line
(about 1%), a validation loss, two steps, and "saved adapter". If a line says `out of memory`, add
`--max-len 1536` or `--rank 8`.

## Step 4: the real training

Close anything else using the GPU first (browser video, other models). Then:

```powershell
& $FT -m scripts.qwen_finetune --model experiments\qwen_lora_v1\base_model
```

Read the output as it runs:
- `validation loss BEFORE training` is the starting point. After each epoch you get a new validation loss.
  It should go **down**. If training loss keeps falling but validation loss goes **up**, the model is
  memorising (overfitting): lower `--epochs` to 2.
- `peak GPU` must stay under 8 GiB.
- The adapter is saved to `experiments\qwen_lora_v1\adapter`, and the curve to `training_log.json`.

## Step 5: serve the fine-tuned model

Leave this terminal open (it needs the GPU; stop Ollama's model first if it is loaded: `ollama stop qwen2.5:3b`):

```powershell
& $FT -m scripts.qwen_serve --base experiments\qwen_lora_v1\base_model
```

Wait for `ready: fine-tuned model at http://127.0.0.1:11500`.

## Step 6: measure it (open a second terminal, repeat the one-time setup)

```powershell
& $APP -m scripts.qwen_eval --split test --tag lora --url http://127.0.0.1:11500
```

## Step 7: the fair comparison

The earlier baseline used Ollama's quantised model and decoder; the fine-tuned model runs in a
different decoder. To compare like with like, measure the **untouched** model through the same server.
Stop the server (Ctrl+C), then:

```powershell
& $FT -m scripts.qwen_serve --adapter none --base experiments\qwen_lora_v1\base_model
# in the other terminal:
& $APP -m scripts.qwen_eval --split test --tag basehf --url http://127.0.0.1:11500
& $APP -m scripts.qwen_compare gate50 basehf lora
```

The honest comparison is **basehf vs lora**. `gate50` is the Ollama reference.

## How to read the result

- A difference smaller than the confidence intervals ([..] in the table) may be noise. The test has 80
  answerable and 20 unanswerable items, so intervals are wide.
- **What it can and cannot show:** the test wordings are new, but the topics and the five documents are
  the same as in training. A gain shows the model learned *this assistant's* task, not that it
  handles new documents.
- If there is no gain, that is a valid result. Write it down.

## If something fails

Copy the last 20 lines of the terminal output. The scripts were checked for syntax and lint, but the
training loop and the server have **not yet been run end to end** (the first dry run was stopped
before it finished). A first-run error is expected and quick to fix.

## Files

| File | Job |
|---|---|
| `scripts/qwen_eval.py` | Labelled question set and the scoring (uses the project's own validator). |
| `scripts/qwen_build_training_data.py` | Builds `data/train.jsonl` from the training wordings only. |
| `scripts/qwen_finetune.py` | The QLoRA training loop. |
| `scripts/qwen_serve.py` | Local Ollama-compatible server for base or fine-tuned model. |
| `scripts/qwen_compare.py` | Side-by-side table of runs. |
| `experiments/qwen_lora_v1/` | Data, runs, summaries, adapter, training log. |
