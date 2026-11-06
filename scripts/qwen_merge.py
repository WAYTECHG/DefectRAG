"""Merge a trained LoRA adapter into the base model and save a plain model folder.

    python -m scripts.qwen_merge --adapter experiments/qwen_lora_v1/adapter_v2 --out experiments/qwen_lora_v1/merged_v2

The result is an ordinary Hugging Face model folder (no adapter needed), which Ollama can import.
The merge runs on the GPU so it needs very little system memory. Nothing in the app is touched.
"""

import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from backend.config import ROOT

BASE = ROOT / "experiments" / "qwen_lora_v1" / "base_model"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--base", default=str(BASE))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} already has files; choose an empty folder so nothing is overwritten.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # bf16 is the dtype the base model was published in; the adapter was trained on its 4-bit form.
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16, device_map=device)
    model = PeftModel.from_pretrained(model, args.adapter)
    merged = model.merge_and_unload()
    out.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(out, safe_serialization=True, max_shard_size="1GB")
    AutoTokenizer.from_pretrained(args.base).save_pretrained(out)
    print(f"saved merged model to {out}")


if __name__ == "__main__":
    main()
