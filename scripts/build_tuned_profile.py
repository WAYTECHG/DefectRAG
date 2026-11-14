"""Build the fine-tuned-encoder profile "dinov2_tuned_v1" next to the current one (needs the GPU, about 30 minutes).

    python -m scripts.build_tuned_profile                       # all 12 categories (resumes finished ones)
    python -m scripts.build_tuned_profile --categories pcb1     # one category

What it writes (nothing existing is changed or overwritten):
* models/encoder_dinov2_tuned/  the round-4b fine-tuned DINOv2 as a normal Hugging Face folder (same keys as the
  original; fp16 weights), licence copied, receipt with the hashes of the base and tuned weights.
* models/highres_tuned/<category>.npz  the deployed memory bank: a 32,768-patch greedy farthest-point coreset of all
  patches of the fit normals (the held-out normals are never used), exactly the round-5 recipe.
* experiments/dinov2_tuned_v1/<category>/  held-out normal scores, test scores and image/pixel metrics, all computed
  with the same code path the application uses (backend.highres), from the saved bank files.

Thresholds, cards and the activation marker are written by scripts.activate_tuned (CPU). The test images
(150-201 per category) were already seen during development, so every number here is descriptive.
"""

import argparse
import json
import shutil
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from safetensors.torch import save_file

from backend.config import CATEGORIES, ROOT
from backend.highres import HighResolutionEncoder, foreground_mask, restore_map, score_tokens
from backend.vision import sha256
from scripts.benchmark_official import pixel_metrics, rank_metrics, write
from scripts.encoder_banks import greedy_coreset

VISA = ROOT / "VisA_20220922"
BASE = ROOT / "models" / "encoder_dinov2"
TUNED = ROOT / "models" / "encoder_dinov2_tuned"
BANKS = ROOT / "models" / "highres_tuned"
EXPERIMENT = ROOT / "experiments" / "dinov2_tuned_v1"
RUNS = ROOT / "experiments" / "dinov2_highres_v1"
WEIGHTS = ROOT / "experiments" / "dinov2_finetune_realistic" / "encoder_ft.pt"
BANK_SIZE = 32768


def export_encoder():
    """Write the tuned weights as a Hugging Face folder; verify it loads and differs from the base."""
    TUNED.mkdir(parents=True, exist_ok=True)
    target = TUNED / "model.safetensors"
    if not target.exists():
        state = {k: v.contiguous() for k, v in torch.load(WEIGHTS, map_location="cpu").items()}
        save_file(state, target, metadata={"format": "pt"})
        for name in ("config.json", "preprocessor_config.json", "LICENSE"):
            shutil.copyfile(BASE / name, TUNED / name)
        base = json.loads((BASE / "ASSET_RECEIPT.json").read_text(encoding="utf-8"))
        receipt = {
            "derived_from": base["repo"],
            "base_revision": base["revision"],
            "base_model_sha256": base["model_sha256"],
            "tuned_model_sha256": sha256(target),
            "license": "Apache-2.0 (derivative of facebook/dinov2-small; modified)",
            "modification": (
                "Last 4 transformer blocks and the final layer norm fine-tuned for 2,500 steps on synthetic "
                "structural defects made from the official VisA fit-normal images (405-814 per category), with a "
                "consistency loss to the original features (scripts.encoder_finetune --train --realistic). "
                "Weights stored in fp16."
            ),
            "training_weights_file": str(WEIGHTS.relative_to(ROOT)),
            "training_weights_sha256": sha256(WEIGHTS),
            "remote_code": False,
        }
        (TUNED / "ASSET_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        (TUNED / "README.md").write_text(
            "# DINOv2 ViT-S/14 fine-tuned for DefectRAG\n\nModified copy of facebook/dinov2-small (Apache-2.0). See "
            "ASSET_RECEIPT.json for the base revision, hashes and the exact modification. Not an official Meta "
            "release.\n",
            encoding="utf-8",
        )
    return target


def normal_names(category):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    calibration = json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))
    held = [p["image"] for p in calibration["predictions"]]
    fit = [r["image"] for r in split["train"] if r["image"] not in set(held)]
    return fit, calibration["predictions"], split["test"]


def build_bank(category, encoder, fit):
    parts = []
    for name in fit:
        with Image.open(VISA / name) as image:
            tokens, _ = encoder.encode(image)
        parts.append(F.normalize(tokens, dim=-1).half())
    everything = torch.cat(parts)
    del parts
    chosen = greedy_coreset(everything, BANK_SIZE, seed=42)
    bank = everything[chosen].cpu().numpy().astype("float16")
    del everything
    torch.cuda.empty_cache()
    BANKS.mkdir(parents=True, exist_ok=True)
    temporary = BANKS / f"{category}.npz.partial"
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, patches=bank)
    temporary.replace(BANKS / f"{category}.npz")


def run_category(category, encoder):
    fit, held_saved, test_rows = normal_names(category)
    directory = EXPERIMENT / category
    directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    build_bank(category, encoder, fit)
    with np.load(BANKS / f"{category}.npz", allow_pickle=False) as saved:  # exactly what the application loads
        bank = F.normalize(torch.from_numpy(saved["patches"].astype("float32")).to(encoder.device), dim=-1)
    fit_seconds = time.perf_counter() - started

    held, scales = [], []
    for entry in held_saved:
        with Image.open(VISA / entry["image"]) as image:
            tokens, geometry = encoder.encode(image)
        mask = foreground_mask(tokens, geometry["grid"])
        raw, score = score_tokens(tokens, bank, mask)
        scales.extend(raw[raw > 0].tolist())
        held.append({"image": entry["image"], "sha256": entry["sha256"], "score": score})
    heatmap_scale = float(np.quantile(scales, 0.995))

    rows, maps = [], []
    for row in test_rows:
        with Image.open(VISA / row["image"]) as image:
            tokens, geometry = encoder.encode(image)
        mask = foreground_mask(tokens, geometry["grid"])
        raw, score = score_tokens(tokens, bank, mask)
        maps.append(restore_map(raw, geometry, (224, 224)).ravel().astype("float32"))
        rows.append(
            {
                "image": row["image"],
                "label": int(row["label"] != "normal"),
                "score": score,
                "foreground_fraction": float(mask.mean()),
            }
        )
    truth = []
    for row in test_rows:
        if row["label"] == "normal":
            truth.append(np.zeros(224 * 224, dtype=bool))
        else:
            with Image.open(VISA / row["mask"]) as image:
                truth.append((np.asarray(image.convert("L").resize((224, 224), Image.Resampling.NEAREST)) > 0).ravel())
    labels, scores = [r["label"] for r in rows], [r["score"] for r in rows]
    metrics = {
        **rank_metrics(labels, scores),
        **pixel_metrics(np.concatenate(truth), np.concatenate(maps)),
        "official_test_images": len(rows),
        "seconds": round(time.perf_counter() - started, 1),
    }
    write(
        directory / "normal_calibration.json",
        {
            "heatmap_scale": heatmap_scale,
            "fit_normals": len(fit),
            "heldout_normals": len(held),
            "predictions": held,
            "bank_patches": BANK_SIZE,
        },
    )
    write(directory / "test_progress.json", rows)
    write(directory / "metrics.json", metrics)
    return metrics, fit_seconds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    args = parser.parse_args()
    weights = export_encoder()
    print(f"tuned encoder folder ready: {weights} sha256 {sha256(weights)[:16]}...", flush=True)
    encoder = HighResolutionEncoder(TUNED)
    for category in args.categories:
        receipt = EXPERIMENT / category / "complete.json"
        if receipt.exists():
            print(f"{category}: already done", flush=True)
            continue
        metrics, fit_seconds = run_category(category, encoder)
        torch.cuda.empty_cache()
        directory = EXPERIMENT / category
        write(
            receipt,
            {
                "status": "passed",
                "files": {p.name: sha256(p) for p in directory.iterdir() if p.is_file() and p.name != "complete.json"},
                "bank_sha256": sha256(BANKS / f"{category}.npz"),
            },
        )
        print(
            f"{category}: {metrics['seconds']} s (fit {fit_seconds:.0f} s) | image AUROC {metrics['auroc']:.3f} "
            f"AP {metrics['average_precision']:.3f} | pixel AUROC {metrics['pixel_auroc']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
