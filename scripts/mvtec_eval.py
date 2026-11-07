"""One-shot MVTec AD evaluation of three detector arms (needs the GPU). Protocol: docs/MVTEC_EVALUATION.md.

    python -m scripts.mvtec_eval --smoke --categories bottle   # code check on a tiny subset; scores are discarded
    python -m scripts.mvtec_eval                                # all 15 categories, one run, resumes finished ones

Arms (fixed in the protocol before any MVTec score existed):
  A  original DINOv2 + random-sample bank (up to 48 foreground + 16 other patches per fit image, cap 32,768)
  B  original DINOv2 + 32,768-patch farthest-point coreset
  C  VisA-fine-tuned DINOv2 (models/encoder_dinov2_tuned) + the same coreset

Nothing is trained or tuned here. Test images are used only for scoring.
"""

import argparse
import hashlib
import json
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from backend.config import ROOT
from backend.highres import HighResolutionEncoder, foreground_mask, restore_map, score_tokens
from scripts.benchmark_official import pixel_metrics, rank_metrics
from scripts.encoder_banks import greedy_coreset

DATA = ROOT / "MVTec_AD"
OUT = ROOT / "experiments" / "mvtec_eval"
PROTOCOL = ROOT / "docs" / "MVTEC_EVALUATION.md"
CATEGORIES = (
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper",
)
ARMS = ("A_random_frozen", "B_coreset_frozen", "C_coreset_tuned")
BANK_SIZE = 32768
SEED = 42


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def listing(category):
    base = DATA / category
    train = sorted((base / "train" / "good").glob("*.png"))
    rows = [
        {"image": p, "label": 0, "mask": None, "type": "good"} for p in sorted((base / "test" / "good").glob("*.png"))
    ]
    for p in sorted(base.glob("test/*/*.png")):
        if p.parent.name != "good":
            rows.append(
                {
                    "image": p,
                    "label": 1,
                    "mask": base / "ground_truth" / p.parent.name / (p.stem + "_mask.png"),
                    "type": p.parent.name,
                }
            )
    return train, rows


def split_train(paths):
    """The VisA rule: sort by content hash and hold out every tenth distinct hash for thresholds."""
    keyed = sorted(((sha256_file(p), p.name, p) for p in paths), key=lambda item: item[:2])
    held_hashes = set(sorted({k[0] for k in keyed})[::10])
    held = [k[2] for k in keyed if k[0] in held_hashes]
    fit = sorted((k[2] for k in keyed if k[0] not in held_hashes), key=lambda p: p.name)
    return fit, held


def encode(encoder, path):
    with Image.open(path) as image:
        tokens, geometry = encoder.encode(image)
    return tokens, foreground_mask(tokens, geometry["grid"]), geometry


def random_bank(frozen, fit, rng):
    """Arm A: up to 48 foreground + 16 other patches per fit image; subsample to the cap."""
    parts = []
    for path in fit:
        tokens, mask, _ = encode(frozen, path)
        features = F.normalize(tokens, dim=-1).half()
        foreground, other = np.flatnonzero(mask), np.flatnonzero(~mask)
        chosen = np.r_[
            rng.choice(foreground, min(48, len(foreground)), replace=False),
            rng.choice(other, min(16, len(other)), replace=False),
        ].astype(int)
        parts.append(features[torch.as_tensor(chosen, device=features.device)])
    bank = torch.cat(parts)
    if len(bank) > BANK_SIZE:
        bank = bank[torch.as_tensor(rng.choice(len(bank), BANK_SIZE, replace=False), device=bank.device)]
    return bank


def coreset_bank(encoder, fit):
    """Arms B and C: greedy farthest-point coreset of every patch of every fit image."""
    parts = [F.normalize(encode(encoder, path)[0], dim=-1).half() for path in fit]
    everything = torch.cat(parts)
    del parts
    chosen = greedy_coreset(everything, min(BANK_SIZE, len(everything)), seed=SEED)
    bank = everything[chosen].clone()
    del everything
    torch.cuda.empty_cache()
    return bank


def prepared(bank, device):
    return F.normalize(bank.float().to(device), dim=-1)


def score_all(frozen, tuned, banks, path, want_maps):
    """Scores (and 224x224 maps) of one image for the three arms."""
    out, maps = {}, {}
    tokens, mask, geometry = encode(frozen, path)
    for arm in ("A_random_frozen", "B_coreset_frozen"):
        raw, score = score_tokens(tokens, banks[arm], mask)
        out[arm] = score
        if want_maps:
            maps[arm] = restore_map(raw, geometry, (224, 224)).ravel().astype("float32")
    tokens, mask, geometry = encode(tuned, path)
    raw, score = score_tokens(tokens, banks["C_coreset_tuned"], mask)
    out["C_coreset_tuned"] = score
    if want_maps:
        maps["C_coreset_tuned"] = restore_map(raw, geometry, (224, 224)).ravel().astype("float32")
    return out, maps


def mask_array(row):
    if row["mask"] is None:
        return np.zeros(224 * 224, dtype=bool)
    with Image.open(row["mask"]) as image:
        return (np.asarray(image.convert("L").resize((224, 224), Image.Resampling.NEAREST)) > 0).ravel()


def run_category(category, frozen, tuned, smoke):
    train, rows = listing(category)
    fit, held = split_train(train)
    if smoke:
        fit, held, rows = fit[:20], held[:4], rows[:: max(1, len(rows) // 10)]
    started = time.perf_counter()
    rng = np.random.default_rng(SEED)
    banks = {
        "A_random_frozen": prepared(random_bank(frozen, fit, rng), frozen.device),
        "B_coreset_frozen": prepared(coreset_bank(frozen, fit), frozen.device),
        "C_coreset_tuned": prepared(coreset_bank(tuned, fit), frozen.device),
    }
    fit_seconds = time.perf_counter() - started
    held_scores = [score_all(frozen, tuned, banks, path, False)[0] for path in held]
    test_scores, pixel_maps = [], {arm: [] for arm in ARMS}
    for row in rows:
        scores, maps = score_all(frozen, tuned, banks, row["image"], True)
        test_scores.append(scores)
        for arm in ARMS:
            pixel_maps[arm].append(maps[arm])
    truth = np.concatenate([mask_array(r) for r in rows])
    labels = [r["label"] for r in rows]
    metrics = {}
    for arm in ARMS:
        values = [s[arm] for s in test_scores]
        metrics[arm] = {**rank_metrics(labels, values)}
        if truth.any():
            metrics[arm].update(pixel_metrics(truth, np.concatenate(pixel_maps[arm])))
    return {
        "category": category,
        "smoke": smoke,
        "protocol_sha256": sha256_file(PROTOCOL),
        "seed": SEED,
        "n_fit": len(fit),
        "n_heldout": len(held),
        "n_test": len(rows),
        "bank_patches": {arm: len(b) for arm, b in banks.items()},
        "seconds_fit": round(fit_seconds, 1),
        "seconds_total": round(time.perf_counter() - started, 1),
        "heldout": {p.name: s for p, s in zip(held, held_scores)},
        "test": {f"{r['type']}/{r['image'].name}": s for r, s in zip(rows, test_scores)},
        "labels": {f"{r['type']}/{r['image'].name}": r["label"] for r in rows},
        "metrics": None if smoke else metrics,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    parser.add_argument("--smoke", action="store_true", help="tiny subset to check the code; metrics are not stored")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = HighResolutionEncoder(ROOT / "models" / "encoder_dinov2")
    tuned = HighResolutionEncoder(ROOT / "models" / "encoder_dinov2_tuned")
    for category in args.categories:
        target = OUT / (f"{category}.smoke.json" if args.smoke else f"{category}.json")
        if target.exists() and not args.smoke:
            print(f"{category}: already done", flush=True)
            continue
        record = run_category(category, frozen, tuned, args.smoke)
        torch.cuda.empty_cache()
        target.write_text(json.dumps(record), encoding="utf-8")
        if args.smoke:
            finite = all(np.isfinite(v) for s in record["test"].values() for v in s.values())
            print(
                f"{category}: smoke run OK in {record['seconds_total']} s | {record['n_fit']} fit, {record['n_test']} test"
                f" | banks {record['bank_patches']} | all scores finite: {finite} (scores discarded)",
                flush=True,
            )
        else:
            m = record["metrics"]
            print(
                f"{category}: {record['seconds_total']} s | image AUROC "
                + "  ".join(f"{arm.split('_')[0]} {m[arm]['auroc']:.3f}" for arm in ARMS),
                flush=True,
            )


if __name__ == "__main__":
    main()
