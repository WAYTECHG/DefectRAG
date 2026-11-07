"""Round 5: a deployable 32,768-patch coreset built from the fine-tuned (realistic-defect) encoder. Needs the GPU.

    python -m scripts.encoder_tuned_coreset                     # all 12 categories, about 40 minutes
    python -m scripts.encoder_tuned_coreset --smoke --categories macaroni2

Fixed before any result: the encoder is experiments/dinov2_finetune_realistic/encoder_ft.pt (round 4b, the only
variant carried forward), the bank is a greedy farthest-point coreset of 32,768 patches taken from every patch of the
810 fit normals, exactly as in round 3 (scripts.encoder_banks), and scores use the same top-1% foreground rule.
Held-out normals and test images are only scored, never used to build anything. Compare with
scripts.encoder_tuned_coreset_report. Results go to experiments/dinov2_tuned_coreset/<category>.json.
"""

import argparse
import json
import time

import torch
import torch.nn.functional as F

from backend.config import CATEGORIES, ROOT
from backend.highres import HighResolutionEncoder, foreground_mask
from scripts.diagnose_encoder import auroc
from scripts.encoder_banks import greedy_coreset
from scripts.encoder_candidates import RUNS, SOURCE, encode, knn_distance, open_image, top_mean

WEIGHTS = ROOT / "experiments" / "dinov2_finetune_realistic" / "encoder_ft.pt"
OUT = ROOT / "experiments" / "dinov2_tuned_coreset"
SIZE = 32768


def run_category(category, encoder, smoke):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    calibration = json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))
    held_names = [p["image"] for p in calibration["predictions"]]
    fit_names = [r["image"] for r in split["train"] if r["image"] not in set(held_names)]
    test_rows = split["test"]
    if smoke:
        fit_names, held_names = fit_names[:100], held_names[:20]
        test_rows = test_rows[:: max(1, len(test_rows) // 40)]
    device = encoder.device
    started = time.perf_counter()
    parts = []
    for name in fit_names:
        tokens, _, _ = encode(encoder, open_image(name), 448)
        parts.append(F.normalize(tokens, dim=-1).half())
    everything = torch.cat(parts)
    del parts
    chosen = greedy_coreset(everything, SIZE, seed=42)
    bank = everything[chosen].clone()
    total = len(everything)
    del everything
    torch.cuda.empty_cache()
    fit_seconds = time.perf_counter() - started

    def score(name):
        tokens, _, grid = encode(encoder, open_image(name), 448)
        mask = torch.as_tensor(foreground_mask(tokens, grid), device=device)
        return top_mean(knn_distance(F.normalize(tokens, dim=-1), bank), mask)

    held = {n: {"core32k": score(n)} for n in held_names}
    test = {r["image"]: {"core32k": score(r["image"])} for r in test_rows}
    return {
        "category": category,
        "smoke": smoke,
        "weights": str(WEIGHTS.relative_to(ROOT)),
        "n_fit": len(fit_names),
        "all_patches": total,
        "bank_patches": len(bank),
        "seconds_fit": round(fit_seconds, 1),
        "seconds_total": round(time.perf_counter() - started, 1),
        "heldout": held,
        "test": test,
        "labels": {r["image"]: 0 if r["label"] == "normal" else 1 for r in test_rows},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    encoder = HighResolutionEncoder(SOURCE)
    encoder.model.load_state_dict(torch.load(WEIGHTS, map_location=encoder.device))
    for category in args.categories:
        target = OUT / (f"{category}.smoke.json" if args.smoke else f"{category}.json")
        if target.exists() and not args.force:
            print(f"{category}: already done", flush=True)
            continue
        record = run_category(category, encoder, args.smoke)
        torch.cuda.empty_cache()
        target.write_text(json.dumps(record), encoding="utf-8")
        labels = record["labels"]
        pos = [record["test"][n]["core32k"] for n, v in labels.items() if v == 1]
        neg = [record["test"][n]["core32k"] for n, v in labels.items() if v == 0]
        print(
            f"{category}: {record['seconds_total']} s (fit {record['seconds_fit']} s) | tuned coreset 32k AUROC "
            f"{auroc(pos, neg):.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
