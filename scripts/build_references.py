"""Build the nearest-normal-photo index for the fine-tuned detector (needs the GPU, a few minutes).

    python -m scripts.build_references                      # all 12 products
    python -m scripts.build_references --categories pcb1    # one product

For each product: 400 randomly sampled normal training photos (never the held-out ones) are encoded with the same
encoder as the detector; 48 diverse ones are kept by greedy farthest-point selection on their descriptors. Written:
* models/highres_tuned/references/<product>.npz   ids and half-precision descriptors (read by backend.references)
* frontend/public/assets/references/<product>.json   the same ids with small JPEG thumbnails for the result page
The photos are VisA training images (CC BY 4.0). Nothing about the detector's score or threshold changes.
"""

import argparse
import base64
import io
import json

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from backend.config import CATEGORIES, ROOT
from backend.highres import HighResolutionEncoder, foreground_mask
from backend.references import descriptor

RUNS = ROOT / "experiments" / "dinov2_highres_v1"
VISA = ROOT / "VisA_20220922"
ENCODER = ROOT / "models" / "encoder_dinov2_tuned"
NPZ = ROOT / "models" / "highres_tuned" / "references"
JSON_OUT = ROOT / "frontend" / "public" / "assets" / "references"
POOL, KEEP, THUMB, SEED = 400, 48, 240, 42


def fit_names(category):
    run = RUNS / category
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    held = {
        p["image"] for p in json.loads((run / "normal_calibration.json").read_text(encoding="utf-8"))["predictions"]
    }
    return [r["image"] for r in split["train"] if r["image"] not in held]


def diverse(vectors, count):
    """Start at the photo closest to the average, then repeatedly add the one farthest from those chosen."""
    centre = F.normalize(vectors.mean(0), dim=0)
    chosen = [int((vectors @ centre).argmax())]
    nearest = vectors @ vectors[chosen[0]]
    while len(chosen) < min(count, len(vectors)):
        index = int(nearest.argmin())
        chosen.append(index)
        nearest = torch.maximum(nearest, vectors @ vectors[index])
    return chosen


def thumbnail(path):
    with Image.open(VISA / path) as image:
        image = image.convert("RGB")
        image.thumbnail((THUMB, THUMB), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def build(category, encoder):
    names = fit_names(category)
    rng = np.random.default_rng(SEED)
    sample = [names[i] for i in sorted(rng.choice(len(names), min(POOL, len(names)), replace=False))]
    vectors = []
    for name in sample:
        with Image.open(VISA / name) as image:
            tokens, geometry = encoder.encode(image)
        vectors.append(descriptor(tokens, foreground_mask(tokens, geometry["grid"])))
    vectors = torch.stack(vectors)
    chosen = diverse(vectors, KEEP)
    ids = [f"{category}/{n:02d}" for n in range(len(chosen))]
    NPZ.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        NPZ / f"{category}.npz", ids=np.array(ids), descriptors=vectors[chosen].cpu().numpy().astype("float16")
    )
    JSON_OUT.mkdir(parents=True, exist_ok=True)
    items = [{"id": i, "thumb": thumbnail(sample[c])} for i, c in zip(ids, chosen)]
    payload = {
        "category": category,
        "attribution": "VisA training photos, Zou et al., ECCV 2022, CC BY 4.0, resized",
        "items": items,
    }
    (JSON_OUT / f"{category}.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return len(items), (JSON_OUT / f"{category}.json").stat().st_size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    args = parser.parse_args()
    encoder = HighResolutionEncoder(ENCODER)
    for category in args.categories:
        count, size = build(category, encoder)
        torch.cuda.empty_cache()
        print(f"{category}: {count} references, {size / 1e3:.0f} kB of thumbnails", flush=True)


if __name__ == "__main__":
    main()
