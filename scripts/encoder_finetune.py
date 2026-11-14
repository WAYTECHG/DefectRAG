"""Fine-tune the last blocks of DINOv2 with synthetic structural defects (round 4 of the detector study; needs the GPU).

    python -m scripts.encoder_finetune --cache      # step 1: resize all training normals once (CPU, about 10 minutes)
    python -m scripts.encoder_finetune --train      # step 2: train (GPU, about 30 minutes)

Why: round 1 found that the weak spots are structural defects (chipped edges, missing parts), where each small patch
can still look normal. This tests whether a DINOv2 whose last blocks have seen such defects separates them better.

Fixed before any result (one configuration, nothing tuned on the test images):
* One shared model for all 12 categories. Training images: only the fit normals per category that the deployed banks use
  (about 90% of the training normals: 810 for the larger categories, 405-487 for the others). The held-out normals and
  the test images are never read here.
* Synthetic defects made from normal images only: cut-and-paste of a patch from another image, an "erased" region
  filled with the local background (a missing part), and an edge region swapped with foreign content (a chip). One to
  three per image; 20% of the images stay clean.
* Trained: the last 4 transformer blocks, the final layer norm and a linear patch head that predicts which patches
  hold a synthetic defect. The first 8 blocks stay frozen. A consistency loss keeps the features of untouched patches
  close to the original frozen model, so the strong categories should not drift.
* 2,500 steps, batch 8, AdamW (1e-5 backbone, 1e-3 head), cosine schedule, bf16.

Evaluation (separate step): python -m scripts.encoder_candidates --weights experiments/dinov2_finetune/encoder_ft.pt
rebuilds every bank with the fine-tuned encoder and scores the same test images, compared with the frozen full bank.
"""

import argparse
import json
import math
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFilter
from transformers import AutoModel

from backend.config import CATEGORIES, ROOT

RUNS = ROOT / "experiments" / "dinov2_highres_v1"
VISA = ROOT / "VisA_20220922"
SOURCE = ROOT / "models" / "encoder_dinov2"
OUT = ROOT / "experiments" / "dinov2_finetune"
OUT_REALISTIC = ROOT / "experiments" / "dinov2_finetune_realistic"
SIZE = 448
GRID = SIZE // 14
STEPS = 2500
BATCH = 8
TRAINABLE_BLOCKS = 4
CONSISTENCY = 2.0
CLEAN_SHARE = 0.2


def fit_names(category):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    held = {
        p["image"] for p in json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))["predictions"]
    }
    return [r["image"] for r in split["train"] if r["image"] not in held]


def build_cache():
    """Resize every fit normal to short edge 448, centre-crop 448 x 448 and store it as raw bytes on disk."""
    OUT.mkdir(parents=True, exist_ok=True)
    entries = [(c, n) for c in CATEGORIES for n in fit_names(c)]
    cache = np.lib.format.open_memmap(
        OUT / "train_448.npy", mode="w+", dtype=np.uint8, shape=(len(entries), SIZE, SIZE, 3)
    )
    for i, (_, name) in enumerate(entries):
        with Image.open(VISA / name) as image:
            image = image.convert("RGB")
            factor = SIZE / min(image.size)
            image = image.resize(
                (max(SIZE, round(image.width * factor)), max(SIZE, round(image.height * factor))),
                Image.Resampling.BICUBIC,
            )
            left, top = (image.width - SIZE) // 2, (image.height - SIZE) // 2
            cache[i] = np.asarray(image.crop((left, top, left + SIZE, top + SIZE)))
        if i % 1000 == 0:
            print(f"cached {i}/{len(entries)}", flush=True)
    cache.flush()
    (OUT / "train_index.json").write_text(json.dumps(entries), encoding="utf-8")
    print(f"cached {len(entries)} images", flush=True)


def rectangle(rng, height, width):
    area = rng.uniform(0.004, 0.04) * height * width
    ratio = rng.uniform(0.5, 2.0)
    rh, rw = int(math.sqrt(area * ratio)), int(math.sqrt(area / ratio))
    rh, rw = max(8, min(rh, height // 3)), max(8, min(rw, width // 3))
    return rng.integers(0, height - rh), rng.integers(0, width - rw), rh, rw


def synthesise(image, other, rng):
    """Return a copy of the image with 1-3 synthetic structural defects and the boolean mask of the changed pixels."""
    height, width, _ = image.shape
    out, mask = image.copy(), np.zeros((height, width), bool)
    gradient = np.hypot(*np.gradient(image.mean(2)))
    edge_points = np.argwhere(gradient > np.quantile(gradient, 0.97))
    for _ in range(rng.integers(1, 4)):
        kind = rng.choice(("cutpaste", "erase", "chip"))
        if kind == "cutpaste":
            y, x, rh, rw = rectangle(rng, height, width)
            sy, sx = rng.integers(0, height - rh), rng.integers(0, width - rw)
            piece = other[sy : sy + rh, sx : sx + rw].astype(np.float32) * rng.uniform(0.9, 1.1)
            out[y : y + rh, x : x + rw] = np.clip(piece, 0, 255).astype(np.uint8)
            mask[y : y + rh, x : x + rw] = True
        elif kind == "erase":
            y, x, rh, rw = rectangle(rng, height, width)
            ring = np.concatenate(
                [
                    image[max(0, y - 6) : y, x : x + rw].reshape(-1, 3),
                    image[y + rh : y + rh + 6, x : x + rw].reshape(-1, 3),
                ]
            )
            fill = ring.mean(0) if len(ring) else image.reshape(-1, 3).mean(0)
            out[y : y + rh, x : x + rw] = fill.astype(np.uint8)
            mask[y : y + rh, x : x + rw] = True
        elif len(edge_points):
            cy, cx = edge_points[rng.integers(len(edge_points))]
            radius = int(rng.integers(8, 28))
            yy, xx = np.ogrid[:height, :width]
            disk = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius**2
            sy, sx = rng.integers(0, height), rng.integers(0, width)
            foreign = np.roll(other, (sy - cy, sx - cx), axis=(0, 1))
            out[disk] = foreign[disk]
            mask |= disk
    return out, mask


def smooth_noise(rng, scales=(3, 6, 12)):
    """Low-frequency random field in [-1, 1] at SIZE x SIZE: a few octaves of coarse noise, upsampled."""
    total = np.zeros((SIZE, SIZE), np.float32)
    for scale in scales:
        grid = Image.fromarray(rng.random((scale, scale)).astype(np.float32))
        total += np.asarray(grid.resize((SIZE, SIZE), Image.Resampling.BICUBIC)) / len(scales)
    total -= total.mean()
    return total / (np.abs(total).max() + 1e-6)


def blob(rng, centre, radius, roughness=0.5):
    """Irregular blob: a disk whose edge is pushed in and out by smooth noise."""
    yy, xx = np.ogrid[:SIZE, :SIZE]
    distance = np.hypot(yy - centre[0], xx - centre[1]) / radius
    return distance + roughness * smooth_noise(rng, (4, 8)) < 1


def foreground_guess(image):
    """Object pixels = colour far from the median of the image border (None if that does not separate anything)."""
    border = np.concatenate([image[:12].reshape(-1, 3), image[-12:].reshape(-1, 3)])
    background = np.median(border, axis=0)
    difference = np.linalg.norm(image.astype(np.float32) - background, axis=2)
    mask = Image.fromarray(((difference > 28) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))
    mask = np.asarray(mask.filter(ImageFilter.MaxFilter(5))) > 0
    return (mask, background) if 0.04 < mask.mean() < 0.9 else (None, background)


def boundary_points(mask):
    inner = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    return np.argwhere(mask & ~inner)


def scratch_mask(rng):
    canvas = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(canvas)
    y, x = rng.integers(40, SIZE - 40, 2).astype(float)
    angle = rng.uniform(0, 2 * math.pi)
    points = [(x, y)]
    for _ in range(int(rng.integers(8, 20))):
        angle += rng.normal(0, 0.35)
        x, y = x + 9 * math.cos(angle), y + 9 * math.sin(angle)
        points.append((x, y))
    draw.line(points, fill=255, width=int(rng.integers(2, 6)))
    return np.asarray(canvas) > 0


def synthesise_realistic(image, other, rng):
    """1-3 more realistic defects: irregular chips that bite the object's edge, missing pieces, textured blotches
    blended from another image, stains and scratches. Returns the edited copy and the mask of changed pixels."""
    out, mask = image.astype(np.float32), np.zeros((SIZE, SIZE), bool)
    foreground, background = foreground_guess(image)
    edge = boundary_points(foreground) if foreground is not None else np.empty((0, 2), int)
    for _ in range(rng.integers(1, 4)):
        kind = rng.choice(("chip", "chip", "missing", "texture", "stain", "scratch"))
        if kind in ("chip", "missing") and len(edge):
            centre = edge[rng.integers(len(edge))]
            radius = rng.uniform(8, 26) if kind == "chip" else rng.uniform(18, 48)
            region = blob(rng, centre, radius) & foreground
            if region.sum() < 30:
                continue
            fill = background + rng.normal(0, 3, 3)
            out[region] = fill
            ring = np.asarray(Image.fromarray((region * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
            out[ring & ~region & foreground] *= rng.uniform(0.75, 0.95)  # darker fracture rim, as on a real break
            mask |= ring
        elif kind == "texture" or (kind in ("chip", "missing") and not len(edge)):
            region = blob(rng, rng.integers(40, SIZE - 40, 2), rng.uniform(15, 50), roughness=0.7)
            shift = (int(rng.integers(0, SIZE)), int(rng.integers(0, SIZE)))
            alpha = rng.uniform(0.6, 1.0)
            out[region] = (1 - alpha) * out[region] + alpha * np.roll(other, shift, axis=(0, 1))[region]
            mask |= region
        elif kind == "stain":
            region = blob(rng, rng.integers(40, SIZE - 40, 2), rng.uniform(15, 45), roughness=0.7)
            tint = rng.uniform(0.45, 0.85) if rng.random() < 0.6 else rng.uniform(1.15, 1.5)
            out[region] = out[region] * tint + rng.normal(0, 10, 3)
            mask |= region
        else:
            region = scratch_mask(rng)
            out[region] = out[region] * (rng.uniform(0.4, 0.7) if rng.random() < 0.5 else rng.uniform(1.3, 1.7))
            mask |= region
    return np.clip(out, 0, 255).astype(np.uint8), mask


def batch(cache, index, ranges, rng, synth=synthesise):
    images, targets, clean = [], [], []
    for _ in range(BATCH):
        i = int(rng.integers(len(cache)))
        low, high = next(r for r in ranges if r[0] <= i < r[1])
        j = int(rng.integers(low, high))
        image, other = np.array(cache[i]), np.array(cache[j])
        if rng.random() < CLEAN_SHARE:
            mask, keep = np.zeros((SIZE, SIZE), bool), True
        else:
            image, mask = synth(image, other, rng)
            keep = False
        if rng.random() < 0.5:
            image, mask = image[:, ::-1], mask[:, ::-1]
        if rng.random() < 0.5:
            image, mask = image[::-1], mask[::-1]
        images.append(np.ascontiguousarray(image))
        targets.append(mask.reshape(GRID, 14, GRID, 14).mean((1, 3)))
        clean.append(keep)
    return np.stack(images), np.stack(targets).astype(np.float32), clean


def train(realistic=False):
    device = torch.device("cuda")
    cache = np.load(OUT / "train_448.npy", mmap_mode="r")
    entries = json.loads((OUT / "train_index.json").read_text(encoding="utf-8"))
    ranges, start = [], 0
    for category in CATEGORIES:
        count = sum(1 for c, _ in entries if c == category)
        ranges.append((start, start + count))
        start += count
    student = AutoModel.from_pretrained(str(SOURCE), local_files_only=True).to(device)
    teacher = AutoModel.from_pretrained(str(SOURCE), local_files_only=True).to(device).eval()
    teacher.requires_grad_(False)
    student.requires_grad_(False)
    parameters = []
    for block in student.encoder.layer[-TRAINABLE_BLOCKS:]:
        block.requires_grad_(True)
        parameters += list(block.parameters())
    student.layernorm.requires_grad_(True)
    parameters += list(student.layernorm.parameters())
    head = torch.nn.Linear(student.config.hidden_size, 1).to(device)
    optimiser = torch.optim.AdamW(
        [{"params": parameters, "lr": 1e-5}, {"params": head.parameters(), "lr": 1e-3}], weight_decay=0.01
    )
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, STEPS)
    mean = torch.tensor([0.485, 0.456, 0.406], device=device)[None, :, None, None]
    std = torch.tensor([0.229, 0.224, 0.225], device=device)[None, :, None, None]
    rng = np.random.default_rng(2026)
    started = time.perf_counter()
    for step in range(1, STEPS + 1):
        images, targets, _ = batch(cache, entries, ranges, rng, synthesise_realistic if realistic else synthesise)
        pixels = (torch.from_numpy(images).to(device).permute(0, 3, 1, 2).float() / 255 - mean) / std
        target = torch.from_numpy(targets).to(device).reshape(BATCH, -1)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            tokens = student(pixel_values=pixels).last_hidden_state[:, 1:]
            with torch.no_grad():
                original = teacher(pixel_values=pixels).last_hidden_state[:, 1:]
            logits = head(tokens).squeeze(-1)
        untouched = (target == 0).float()
        similarity = F.cosine_similarity(tokens.float(), original.float(), dim=-1)
        consistency = ((1 - similarity) * untouched).sum() / untouched.sum().clamp_min(1)
        detection = F.binary_cross_entropy_with_logits(logits.float(), target.clamp(0, 1))
        loss = detection + CONSISTENCY * consistency
        optimiser.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters + list(head.parameters()), 1.0)
        optimiser.step()
        schedule.step()
        if step % 100 == 0 or step == 1:
            hit = ((logits > 0).float() == (target > 0.2).float()).float().mean().item()
            print(
                f"step {step:4d}/{STEPS} loss {loss.item():.4f} detection {detection.item():.4f} "
                f"consistency {consistency.item():.4f} patch accuracy {hit:.3f} {time.perf_counter() - started:.0f}s",
                flush=True,
            )
    state = {k: v.detach().half().cpu() for k, v in student.state_dict().items()}
    target = OUT_REALISTIC if realistic else OUT
    target.mkdir(parents=True, exist_ok=True)
    torch.save(state, target / "encoder_ft.pt")
    torch.save({k: v.detach().cpu() for k, v in head.state_dict().items()}, target / "head_ft.pt")
    print(f"saved {target / 'encoder_ft.pt'} in {time.perf_counter() - started:.0f}s", flush=True)


def preview():
    """Write 12 images (one category each, original above, synthetic defects below) to check the defects look plausible."""
    cache = np.load(OUT / "train_448.npy", mmap_mode="r")
    entries = json.loads((OUT / "train_index.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(7)
    tiles = []
    for category in CATEGORIES:
        rows = [i for i, (c, _) in enumerate(entries) if c == category]
        i, j = int(rng.choice(rows)), int(rng.choice(rows))
        original, other = np.array(cache[i]), np.array(cache[j])
        edited, mask = synthesise_realistic(original, other, rng)
        outline = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)) > 0
        marked = edited.copy()
        marked[outline] = (255, 0, 0)
        tiles.append(np.concatenate([original, edited, marked], axis=0))
    sheet = np.concatenate([np.concatenate(tiles[r * 6 : r * 6 + 6], axis=1) for r in range(2)], axis=0)
    target = OUT_REALISTIC
    target.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet).resize((sheet.shape[1] // 4, sheet.shape[0] // 4)).save(target / "preview.jpg", quality=90)
    print(f"wrote {target / 'preview.jpg'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", action="store_true")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--realistic", action="store_true", help="round 4b: more realistic synthetic defects")
    parser.add_argument("--preview", action="store_true", help="save a picture of synthetic defects (CPU)")
    args = parser.parse_args()
    if args.preview:
        preview()
        return
    if args.cache:
        build_cache()
    if args.train:
        train(args.realistic)
    if not (args.cache or args.train):
        parser.error("choose --cache and/or --train")


if __name__ == "__main__":
    main()
