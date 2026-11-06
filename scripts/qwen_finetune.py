"""QLoRA fine-tuning of Qwen2.5-3B-Instruct on the evidence-selection examples.

Run this in the SEPARATE training environment (defectrag-ft), not the app environment:

    python -m scripts.qwen_finetune

What happens, in order:
  1. Load the base model in 4-bit (QLoRA): the big weights are frozen and compressed.
  2. Attach small trainable LoRA matrices to the attention and MLP layers (about 1% of the size).
  3. Turn each example into tokens. Loss is computed only on the ANSWER part, never on the prompt.
  4. Train for a few epochs with gradient accumulation (several small steps act like one big batch).
  5. Report training and validation loss each epoch, then save only the small adapter (tens of MB).
"""

import argparse
import json
import math
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

OUT = Path(__file__).resolve().parents[1] / "experiments" / "qwen_lora_v1"
BASE = "Qwen/Qwen2.5-3B-Instruct"


def encode(tokenizer, example, max_len):
    """Tokens for one example; labels are -100 (ignored) for the prompt and real ids for the answer."""
    chat = [{"role": "user", "content": example["prompt"]}]
    prompt_text = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    answer_ids = tokenizer(example["completion"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
    ids = prompt_ids + answer_ids
    if len(ids) > max_len:
        return None
    return {"input_ids": ids, "labels": [-100] * len(prompt_ids) + answer_ids}


def batch_loss(model, row, device):
    ids = torch.tensor([row["input_ids"]], device=device)
    labels = torch.tensor([row["labels"]], device=device)
    return model(input_ids=ids, labels=labels).loss


@torch.no_grad()
def validation_loss(model, rows, device):
    model.eval()
    total = sum(batch_loss(model, r, device).item() for r in rows)
    model.train()
    return total / max(1, len(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=BASE)
    parser.add_argument("--data", default=str(OUT / "data" / "train.jsonl"))
    parser.add_argument("--out", default=str(OUT / "adapter"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--accum", type=int, default=8, help="examples per optimizer step")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--max-len", type=int, default=2048)
    parser.add_argument("--max-steps", type=int, default=0, help="stop early (smoke test)")
    parser.add_argument("--limit", type=int, default=0, help="use only the first N examples (smoke test)")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda"
    print(
        f"GPU: {torch.cuda.get_device_name(0)}  free memory before loading: "
        f"{torch.cuda.mem_get_info()[0] / 2**30:.1f} GiB",
        flush=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    examples = [json.loads(line) for line in Path(args.data).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        examples = examples[: args.limit]
    random.shuffle(examples)
    rows = [r for r in (encode(tokenizer, e, args.max_len) for e in examples) if r]
    cut = max(1, len(rows) // 10)
    val, train = rows[:cut], rows[cut:]
    print(
        f"examples: {len(train)} train, {len(val)} validation "
        f"({len(examples) - len(rows)} dropped as too long); "
        f"tokens per example: median {sorted(len(r['input_ids']) for r in rows)[len(rows) // 2]}",
        flush=True,
    )

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model, quantization_config=quant, device_map={"": 0}, dtype=torch.bfloat16
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    lora = LoraConfig(
        r=args.rank,
        lora_alpha=2 * args.rank,
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()
    model.train()

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    steps_per_epoch = math.ceil(len(train) / args.accum)
    total_steps = steps_per_epoch * args.epochs
    if args.max_steps:
        total_steps = min(total_steps, args.max_steps)
    warmup = max(1, int(0.05 * total_steps))

    def lr_at(step):  # linear warm-up, then cosine decay to 10%
        if step < warmup:
            return args.lr * (step + 1) / warmup
        progress = (step - warmup) / max(1, total_steps - warmup)
        return args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progress)))

    log = {"args": vars(args), "epochs": [], "steps": []}
    step, started = 0, time.time()
    val_before = validation_loss(model, val, device)
    print(f"validation loss BEFORE training: {val_before:.4f}", flush=True)
    log["validation_loss_before"] = val_before
    for epoch in range(args.epochs):
        random.shuffle(train)
        running = []
        for start in range(0, len(train), args.accum):
            group = train[start : start + args.accum]
            for g in optimizer.param_groups:
                g["lr"] = lr_at(step)
            total = 0.0
            for row in group:
                loss = batch_loss(model, row, device) / len(group)
                loss.backward()
                total += loss.item()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            running.append(total)
            log["steps"].append({"step": step, "loss": total, "lr": lr_at(step - 1)})
            print(
                f"epoch {epoch + 1}/{args.epochs}  step {step}/{total_steps}  loss {total:.4f}  "
                f"lr {lr_at(step - 1):.2e}  {time.time() - started:.0f}s  "
                f"peak GPU {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB",
                flush=True,
            )
            if args.max_steps and step >= args.max_steps:
                break
        val_loss = validation_loss(model, val, device)
        log["epochs"].append(
            {"epoch": epoch + 1, "train_loss": sum(running) / len(running), "validation_loss": val_loss}
        )
        print(
            f"== epoch {epoch + 1}: train loss {sum(running) / len(running):.4f}, validation loss {val_loss:.4f}",
            flush=True,
        )
        if args.max_steps and step >= args.max_steps:
            break

    Path(args.out).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    log["seconds"] = time.time() - started
    (Path(args.out) / "training_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"saved adapter to {args.out}  (total {log['seconds'] / 60:.1f} minutes)", flush=True)


if __name__ == "__main__":
    main()
