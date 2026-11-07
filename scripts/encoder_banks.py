"""Smaller banks, rotated banks and a DINOv3 bank (round 3 of the detector study; needs the GPU).

    python -m scripts.encoder_banks --smoke --categories macaroni2     # quick check
    python -m scripts.encoder_banks                                     # all 12 categories

Round 2 (scripts.encoder_candidates) showed that using every normal patch as the memory bank beats the deployed
32,768-patch sample in all 12 categories, but the full banks total 8.2 GB. This round asks how small a bank can be
and still keep the gain, and tests two more ideas. Nothing is trained and nothing in the app is changed. Candidates,
fixed before any result:

  cap128/256/512   random patches per training image (3/4 foreground, 1/4 other, the deployed recipe scaled up)
  core32k/64k/96k  greedy farthest-point coreset of all patches (random 128-d projection, the PatchCore idea)
  rot              four rotations (0/90/180/270 degrees) of every training image, 256 random patches each; about
                   as many patches as the full bank, so the full bank is its control
  dinov3full       the retained DINOv3 ViT-S/16 with a full bank, scored over all patches (no foreground mask)
  base             the deployed bank, recomputed to prove the harness matches the app

Scores are written to experiments/dinov2_banks/<category>.json; scripts.encoder_candidates_report merges them with the
round-2 scores. Test images were already seen during development, so results are descriptive.
"""

import argparse
import json
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoModel

from backend.config import CATEGORIES, ROOT
from backend.highres import HighResolutionEncoder, foreground_mask
from backend.vision import distances
from scripts.diagnose_encoder import auroc
from scripts.encoder_candidates import RUNS, SOURCE, encode, knn_distance, open_image, top_mean

OUT = ROOT / "experiments" / "dinov2_banks"
DINOV3 = ROOT / "models" / "encoder"
CAPS = (128, 256, 512)
CORESETS = {"core32k": 32768, "core64k": 65536, "core96k": 98304}
ROTATION_CAP = 256
PROJECTION = 128
ROTATIONS = (None, Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_180, Image.Transpose.ROTATE_270)
CANDIDATES = ("base", *(f"cap{c}" for c in CAPS), *CORESETS, "rot", "dinov3full")


class Dinov3:
    """The retained DINOv3 ViT-S/16, frozen, with the same short-edge-448 preprocessing as the DINOv2 detector."""

    def __init__(self, device):
        self.device = device
        self.model = AutoModel.from_pretrained(str(DINOV3), local_files_only=True).eval().to(device).half()
        self.model.requires_grad_(False)
        self.patch = int(self.model.config.patch_size)
        self.skip = 1 + int(self.model.config.num_register_tokens)
        self.mean = torch.tensor([0.485, 0.456, 0.406], device=device, dtype=torch.half)[:, None, None]
        self.std = torch.tensor([0.229, 0.224, 0.225], device=device, dtype=torch.half)[:, None, None]

    @torch.inference_mode()
    def patches(self, image, resolution=448):
        width, height = image.size
        factor = resolution / min(width, height)
        resized = (int(width * factor), int(height * factor))
        cropped = tuple(v - v % self.patch for v in resized)
        pixels = np.array(image.resize(resized, Image.Resampling.BICUBIC).crop((0, 0, *cropped)), copy=True)
        values = torch.from_numpy(pixels).permute(2, 0, 1).to(self.device, dtype=torch.half) / 255
        out = self.model(pixel_values=((values - self.mean) / self.std)[None]).last_hidden_state[0, self.skip :]
        return F.normalize(out.float(), dim=-1)


def pick(mask, cap, rng):
    """Random patch indices: 3/4 of the cap from the foreground, 1/4 from the rest (the deployed 48 + 16 recipe)."""
    foreground, other = np.flatnonzero(mask), np.flatnonzero(~mask)
    return np.r_[
        rng.choice(foreground, min(cap * 3 // 4, len(foreground)), replace=False),
        rng.choice(other, min(cap // 4, len(other)), replace=False),
    ].astype(int)


@torch.inference_mode()
def greedy_coreset(points, count, seed):
    """Farthest-point selection in a random 128-d projection. The first n picks form the n-patch coreset."""
    device = points.device
    generator = torch.Generator(device=device).manual_seed(seed)
    projection = torch.randn(points.shape[1], PROJECTION, device=device, generator=generator) / PROJECTION**0.5
    small = torch.cat([(part.float() @ projection).half() for part in points.split(65536)])
    norms = (small.float() ** 2).sum(1)
    first = torch.randint(len(small), (1,), device=device, generator=generator)[0]
    chosen = torch.empty(count, dtype=torch.long, device=device)
    chosen[0] = first
    nearest = (norms - 2 * (small @ small[first]).float() + norms[first]).clamp_min(0)
    for i in range(1, count):
        index = nearest.argmax()
        chosen[i] = index
        nearest = torch.minimum(nearest, (norms - 2 * (small @ small[index]).float() + norms[index]).clamp_min(0))
    return chosen


def run_category(category, encoder, smoke):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    calibration = json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))
    cached = {r["image"]: r["scores"][3] for r in json.loads((run / "test_progress.json").read_text(encoding="utf-8"))}
    held_names = [p["image"] for p in calibration["predictions"]]
    skip = set(held_names)
    fit_names = [r["image"] for r in split["train"] if r["image"] not in skip]
    test_rows = split["test"]
    if smoke:
        fit_names, held_names = fit_names[:100], held_names[:20]
        test_rows = test_rows[:: max(1, len(test_rows) // 40)]
    names = held_names + [r["image"] for r in test_rows]
    device = encoder.device
    started = time.perf_counter()
    scores = {name: {} for name in names}

    # DINOv2: encode every training normal and build the sampled, coreset and rotated banks.
    fine, capped, rotated = [], {c: [] for c in CAPS}, []
    for number, name in enumerate(fit_names):
        image = open_image(name)
        for turn, rotation in enumerate(ROTATIONS):
            view = image if rotation is None else image.transpose(rotation)
            tokens, _, grid = encode(encoder, view, 448)
            mask = foreground_mask(tokens, grid)
            normal = F.normalize(tokens, dim=-1).half()
            rng = np.random.default_rng(1000 * number + turn)
            rotated.append(normal[torch.as_tensor(pick(mask, ROTATION_CAP, rng), device=device)])
            if turn == 0:
                fine.append(normal)
                for cap in CAPS:
                    capped[cap].append(
                        normal[torch.as_tensor(pick(mask, cap, np.random.default_rng(number + cap)), device=device)]
                    )
    banks = {f"cap{c}": torch.cat(parts) for c, parts in capped.items()}
    banks["rot"] = torch.cat(rotated)
    everything = torch.cat(fine)
    del fine, capped, rotated
    coreset = greedy_coreset(everything, max(CORESETS.values()), seed=42)
    for label, size in CORESETS.items():
        banks[label] = everything[coreset[:size]].clone()
    sizes = {label: len(bank) for label, bank in banks.items()}
    sizes["all_patches"] = len(everything)
    del everything
    with np.load(run / "bank_3.npz") as saved:
        base_bank = F.normalize(torch.from_numpy(saved["patches"].astype("float32")).to(device), dim=-1)
    sizes["base"] = len(base_bank)
    fit_seconds = time.perf_counter() - started

    for name in names:
        tokens, _, grid = encode(encoder, open_image(name), 448)
        mask = torch.as_tensor(foreground_mask(tokens, grid), device=device)
        normal = F.normalize(tokens, dim=-1)
        scores[name]["base"] = top_mean(distances(normal, base_bank), mask)
        for label, bank in banks.items():
            scores[name][label] = top_mean(knn_distance(normal, bank), mask)
    del banks, base_bank
    torch.cuda.empty_cache()

    # DINOv3: a full bank, scored over all patches.
    third = Dinov3(device)
    bank = torch.cat([third.patches(open_image(n)).half() for n in fit_names])
    sizes["dinov3full"] = len(bank)
    for name in names:
        patches = third.patches(open_image(name))
        everywhere = torch.ones(len(patches), dtype=torch.bool, device=device)
        scores[name]["dinov3full"] = top_mean(knn_distance(patches, bank), everywhere)
    del bank, third
    torch.cuda.empty_cache()

    differences = [abs(scores[r["image"]]["base"] - cached[r["image"]]) for r in test_rows]
    return {
        "category": category,
        "smoke": smoke,
        "n_fit": len(fit_names),
        "bank_patches": sizes,
        "reproduction": {
            "test_max_abs_difference": max(differences),
            "test_mean_abs_difference": float(np.mean(differences)),
        },
        "seconds_fit": round(fit_seconds, 1),
        "seconds_total": round(time.perf_counter() - started, 1),
        "heldout": {n: scores[n] for n in held_names},
        "test": {r["image"]: scores[r["image"]] for r in test_rows},
        "labels": {r["image"]: 0 if r["label"] == "normal" else 1 for r in test_rows},
    }


def summarise(record):
    labels = record["labels"]
    positive = [n for n, v in labels.items() if v == 1]
    negative = [n for n, v in labels.items() if v == 0]
    return "  ".join(
        f"{c} {auroc([record['test'][n][c] for n in positive], [record['test'][n][c] for n in negative]):.3f}"
        for c in CANDIDATES
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    parser.add_argument("--smoke", action="store_true", help="100 fit images, 20 held-out, about 40 test images")
    parser.add_argument("--force", action="store_true", help="recompute categories that already have a result file")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    encoder = HighResolutionEncoder(SOURCE)
    for category in args.categories:
        target = OUT / (f"{category}.smoke.json" if args.smoke else f"{category}.json")
        if target.exists() and not args.force:
            print(f"{category}: already done ({target.name})", flush=True)
            continue
        record = run_category(category, encoder, args.smoke)
        torch.cuda.empty_cache()
        target.write_text(json.dumps(record), encoding="utf-8")
        rep = record["reproduction"]
        print(
            f"{category}: {record['seconds_total']} s (fit {record['seconds_fit']} s) | reproduces the app: "
            f"max diff {rep['test_max_abs_difference']:.4f}",
            flush=True,
        )
        print("   bank patches " + " ".join(f"{k}={v:,}" for k, v in record["bank_patches"].items()), flush=True)
        print("   AUROC " + summarise(record), flush=True)


if __name__ == "__main__":
    main()
