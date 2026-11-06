"""Dry run of switching the Hugging Face Space to the fine-tuned model.

    python -m scripts.space_dry_run

It copies deployment/space/generation.py into a temporary folder, applies the proposed change there, checks that the
result is valid Python and prints what would change. It never writes to deployment/ and uploads nothing.
"""

import ast
import difflib
import tempfile
from pathlib import Path

from backend.config import ROOT

LIVE = ROOT / "deployment" / "space" / "generation.py"

OLD = """MODEL_ID='Qwen/Qwen3-4B-Instruct-2507'
REVISION='cdbee75f17c01a7cc42f958dc650907174af0554'
TOKENIZER=None
MODEL=None
if os.getenv('SPACES_ZERO_GPU')=='1' and os.getenv('DEFECTRAG_LIVE_RAG')=='1':
    # Download/cache in the Space only. Never place another 8 GB on the laptop.
    TOKENIZER=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    MODEL=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,
        dtype=torch.bfloat16,attn_implementation='sdpa').eval().to('cuda')"""

NEW = """# Fine-tuned Qwen2.5-3B-Instruct (QLoRA adapter merged into the base weights, bf16, about 6 GB).
# Results: docs/QWEN_FINETUNING_RESULTS.md. Improved using Qwen (Qwen Research License, non-commercial).
MODEL_ID=os.getenv('DEFECTRAG_MODEL_ID','Wizzas/defectrag-qwen2.5-3b-evidence')
REVISION=os.getenv('DEFECTRAG_MODEL_REVISION','')  # pin to the uploaded commit hash before going live
HF_TOKEN=os.getenv('HF_TOKEN')  # Space secret; needed while the model repo is private
TOKENIZER=None
MODEL=None
if os.getenv('SPACES_ZERO_GPU')=='1' and os.getenv('DEFECTRAG_LIVE_RAG')=='1':
    if not REVISION:
        raise RuntimeError('Set DEFECTRAG_MODEL_REVISION to the pinned commit of the fine-tuned model')
    # Download/cache in the Space only. Never place another 6 GB on the laptop.
    TOKENIZER=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION,token=HF_TOKEN)
    MODEL=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,token=HF_TOKEN,
        dtype=torch.bfloat16,attn_implementation='sdpa').eval().to('cuda')"""


def main():
    original = LIVE.read_text(encoding="utf-8")
    if OLD not in original:
        raise SystemExit("The live file no longer contains the expected block, so the proposal needs updating.")
    proposed = original.replace(OLD, NEW)
    ast.parse(proposed)  # raises if the result is not valid Python
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder) / "generation.py"
        copy.write_text(proposed, encoding="utf-8")
        print(f"1. proposal written to a temporary copy ({copy.name}) and checked: valid Python")
    print("2. live file left unchanged:", LIVE)
    print("3. what would change:\n")
    diff = difflib.unified_diff(original.splitlines(), proposed.splitlines(), "live", "proposed", lineterm="", n=1)
    print("\n".join(diff))
    print("\nNothing was uploaded and nothing in deployment/ was modified.")


if __name__ == "__main__":
    main()
