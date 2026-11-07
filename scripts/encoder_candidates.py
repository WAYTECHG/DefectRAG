"""Score extra detector candidates on the frozen DINOv2 features (step 1 of 2: needs the GPU).

    python -m scripts.encoder_candidates --smoke --categories macaroni2     # quick check, about a minute
    python -m scripts.encoder_candidates                                      # all 12 categories

Nothing is trained and nothing in the app is changed. For each category it encodes the official VisA training normals
(the 810 used to fit the deployed bank), the 90 held-out normals and the 200 official test images, and records one
score per image for each candidate. Step 2 (scripts.encoder_candidates_report, CPU only) compares them.

Candidates (all fixed before looking at any result; the same top-1% foreground rule as the app):
  base      the deployed bank (32,768 sampled patches), recomputed here to prove the harness matches the app
  full      every patch of every fit normal as the bank (no sampling)
  fullfg    only the foreground patches of every fit normal
  pos       position-aware: nearest normal patch at the same place, within one patch of shift (aligned objects)
  cls       image-level distance between class tokens (global view)
  meanpool  image-level distance between mean foreground patch features
  coarse    the same idea at half the resolution (short edge 224) with a full bank (wider context)

Masks and defect labels are never read here. Test images were already seen during development, so results are
descriptive, not a fresh validation.
"""

import argparse
import json
import math
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from backend.config import CATEGORIES, ROOT
from backend.highres import HighResolutionEncoder, foreground_mask
from backend.vision import distances
from scripts.diagnose_encoder import auroc

RUNS = ROOT / "experiments" / "dinov2_highres_v1"
OUT = ROOT / "experiments" / "dinov2_candidates"
VISA = ROOT / "VisA_20220922"
SOURCE = ROOT / "models" / "encoder_dinov2"
OFFSETS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
CANDIDATES = ("base", "full", "fullfg", "pos", "cls", "meanpool", "coarse")


@torch.inference_mode()
def encode(encoder, image, resolution):
    """Same preprocessing as HighResolutionEncoder.encode, but also returns the class token."""
    width, height = image.size
    factor = resolution / min(width, height)
    resized = (int(width * factor), int(height * factor))
    cropped = tuple(v - v % encoder.patch_size for v in resized)
    pixels = np.array(image.resize(resized, Image.Resampling.BICUBIC).crop((0, 0, *cropped)), copy=True)
    values = torch.from_numpy(pixels).permute(2, 0, 1).to(encoder.device, dtype=encoder.dtype) / 255
    out = encoder.model(pixel_values=((values - encoder.mean) / encoder.std)[None]).last_hidden_state[0].float()
    grid = (cropped[1] // encoder.patch_size, cropped[0] // encoder.patch_size)
    return out[1:], out[0], grid


def top_mean(distance, mask):
    """Mean of the largest 1% of foreground patch distances (the app's image score)."""
    selected = distance[mask]
    return float(selected.topk(max(1, math.ceil(len(selected) * 0.01))).values.mean())


def knn_distance(patches, bank, chunk=32768):
    """1 - highest cosine similarity to any bank patch; the bank is stored in half precision."""
    best = torch.full((len(patches),), -1.0, device=patches.device)
    for part in bank.split(chunk):
        best = torch.maximum(best, (patches @ part.float().T).amax(dim=1))
    return (1 - best).clamp_min(0)


def positional_distance(patches, stack, grid):
    """Nearest normal patch at the same grid position or one step away; stack is [positions, images, features]."""
    height, width = grid
    device = patches.device
    ys = torch.arange(height, device=device).repeat_interleave(width)
    xs = torch.arange(width, device=device).repeat(height)
    query = patches.half()[:, :, None]
    best = torch.full((len(patches),), -1.0, device=device)
    for dy, dx in OFFSETS:
        y2, x2 = ys + dy, xs + dx
        valid = (y2 >= 0) & (y2 < height) & (x2 >= 0) & (x2 < width)
        index = y2.clamp(0, height - 1) * width + x2.clamp(0, width - 1)
        similarity = torch.bmm(stack[index], query).squeeze(-1).amax(dim=1).float()
        best = torch.where(valid, torch.maximum(best, similarity), best)
    return (1 - best).clamp_min(0)


def open_image(relative):
    return Image.open(VISA / relative).convert("RGB")


def run_category(category, encoder, smoke):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    calibration = json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))
    cached = {r["image"]: r["scores"][3] for r in json.loads((run / "test_progress.json").read_text(encoding="utf-8"))}
    held_names = [p["image"] for p in calibration["predictions"]]
    held_saved = {p["image"]: p["score"] for p in calibration["predictions"]}
    skip = set(held_names)
    fit_names = [r["image"] for r in split["train"] if r["image"] not in skip]
    test_rows = split["test"]
    if smoke:
        fit_names = fit_names[:100]
        held_names = held_names[:20]
        test_rows = test_rows[:: max(1, len(test_rows) // 40)]
    device = encoder.device
    started = time.perf_counter()

    # Fit: encode every training normal at both scales and keep the features on the GPU.
    fine, fine_fg, coarse, cls_rows, mean_rows, same_grid = [], [], [], [], [], []
    pos_grid = None
    for name in fit_names:
        image = open_image(name)
        tokens, cls_token, grid = encode(encoder, image, 448)
        mask = torch.as_tensor(foreground_mask(tokens, grid), device=device)
        normal = F.normalize(tokens, dim=-1)
        pos_grid = pos_grid or grid
        fine.append(normal.half())
        fine_fg.append(normal[mask].half())
        cls_rows.append(F.normalize(cls_token, dim=-1))
        mean_rows.append(F.normalize(normal[mask].mean(0) if mask.any() else normal.mean(0), dim=-1))
        if grid == pos_grid:
            same_grid.append(len(fine) - 1)
        small, _, _ = encode(encoder, image, 224)
        coarse.append(F.normalize(small, dim=-1).half())
    full_bank = torch.cat(fine)
    fullfg_bank = torch.cat(fine_fg)
    coarse_bank = torch.cat(coarse)
    stack = torch.stack([fine[i] for i in same_grid]).permute(1, 0, 2).contiguous()
    cls_bank, mean_bank = torch.stack(cls_rows), torch.stack(mean_rows)
    del fine, fine_fg, coarse
    with np.load(run / "bank_3.npz") as saved:
        base_bank = F.normalize(torch.from_numpy(saved["patches"].astype("float32")).to(device), dim=-1)
    fit_seconds = time.perf_counter() - started

    def score(name):
        image = open_image(name)
        tokens, cls_token, grid = encode(encoder, image, 448)
        mask_np = foreground_mask(tokens, grid)
        mask = torch.as_tensor(mask_np, device=device)
        normal = F.normalize(tokens, dim=-1)
        out = {
            "base": top_mean(distances(normal, base_bank), mask),
            "full": top_mean(knn_distance(normal, full_bank), mask),
            "fullfg": top_mean(knn_distance(normal, fullfg_bank), mask),
            "pos": top_mean(positional_distance(normal, stack, grid), mask) if grid == pos_grid else None,
            "cls": float(1 - (cls_bank @ F.normalize(cls_token, dim=-1)).max()),
            "meanpool": float(1 - (mean_bank @ F.normalize(normal[mask].mean(0), dim=-1)).max())
            if mask.any()
            else None,
        }
        small, _, small_grid = encode(encoder, image, 224)
        small_mask = torch.as_tensor(foreground_mask(small, small_grid), device=device)
        out["coarse"] = top_mean(knn_distance(F.normalize(small, dim=-1), coarse_bank), small_mask)
        return out

    held = {name: score(name) for name in held_names}
    test = {row["image"]: score(row["image"]) for row in test_rows}
    labels = {row["image"]: 0 if row["label"] == "normal" else 1 for row in test_rows}
    differences = [abs(test[n]["base"] - cached[n]) for n in test]
    held_differences = [abs(held[n]["base"] - held_saved[n]) for n in held]
    record = {
        "category": category,
        "smoke": smoke,
        "n_fit": len(fit_names),
        "n_position_images": len(same_grid),
        "grid": list(pos_grid),
        "bank_patches": {
            "base": len(base_bank),
            "full": len(full_bank),
            "fullfg": len(fullfg_bank),
            "coarse": len(coarse_bank),
        },
        "reproduction": {
            "test_max_abs_difference": max(differences),
            "test_mean_abs_difference": float(np.mean(differences)),
            "heldout_max_abs_difference": max(held_differences),
        },
        "seconds_fit": round(fit_seconds, 1),
        "seconds_total": round(time.perf_counter() - started, 1),
        "heldout": held,
        "test": test,
        "labels": labels,
    }
    return record


def summarise(record):
    labels = record["labels"]
    positive = [n for n, v in labels.items() if v == 1]
    negative = [n for n, v in labels.items() if v == 0]
    parts = []
    for name in CANDIDATES:
        if any(record["test"][n][name] is None for n in labels):
            parts.append(f"{name} n/a")
            continue
        value = auroc([record["test"][n][name] for n in positive], [record["test"][n][name] for n in negative])
        parts.append(f"{name} {value:.3f}")
    return "  ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    parser.add_argument("--smoke", action="store_true", help="100 fit images, 20 held-out, about 40 test images")
    parser.add_argument("--force", action="store_true", help="recompute categories that already have a result file")
    parser.add_argument(
        "--weights", help="round 4: a fine-tuned encoder state dict; results go to dinov2_candidates_ft"
    )
    parser.add_argument("--tag", default="ft", help="with --weights: results go to dinov2_candidates_<tag>")
    args = parser.parse_args()
    out = OUT.with_name(f"dinov2_candidates_{args.tag}") if args.weights else OUT
    out.mkdir(parents=True, exist_ok=True)
    encoder = HighResolutionEncoder(SOURCE)
    if args.weights:
        # The deployed "base" bank was built with the original encoder, so its score (and the reproduction check) no
        # longer match the app with these weights; every other candidate is rebuilt from the fine-tuned features.
        encoder.model.load_state_dict(torch.load(args.weights, map_location=encoder.device))
    for category in args.categories:
        target = out / (f"{category}.smoke.json" if args.smoke else f"{category}.json")
        if target.exists() and not args.force:
            print(f"{category}: already done ({target.name})", flush=True)
            continue
        record = run_category(category, encoder, args.smoke)
        torch.cuda.empty_cache()  # the category's banks are freed when run_category returns
        target.write_text(json.dumps(record), encoding="utf-8")
        rep = record["reproduction"]
        print(
            f"{category}: {record['seconds_total']} s | reproduces the app: test max diff {rep['test_max_abs_difference']:.4f}, "
            f"mean {rep['test_mean_abs_difference']:.4f}",
            flush=True,
        )
        print("   AUROC " + summarise(record), flush=True)


if __name__ == "__main__":
    main()
