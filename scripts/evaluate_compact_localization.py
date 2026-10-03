"""Evaluate cloud-style patch maps and single connected boxes on LOCO anomaly masks.

This is a project localization benchmark, NOT official LOCO sPRO or detector mAP50.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import roc_auc_score
from torch.nn import functional as F

from rag.anomaly_crop import anomaly_map_to_bounding_box
from vision.box_metrics import box_iou, mask_box
from vision.dinov3_encoder import DINOv3Encoder
from vision.normal_autoencoder import NormalPatchAutoencoder, reconstruction_distances

CATEGORIES = ("breakfast_box", "juice_bottle", "pushpins", "screw_bag", "splicing_connectors")
GROUPS = ("logical_anomalies", "structural_anomalies")
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def find_masks(root: Path, category: str, group: str, image: Path) -> list[Path]:
    folder = root / category / "ground_truth" / group / image.stem
    candidates = sorted(path for path in folder.glob("*") if path.suffix.lower() in EXTENSIONS)
    if not candidates:
        raise FileNotFoundError(f"No ground-truth mask for {image} in {folder}")
    return candidates


def load_head(path: Path, category: str, dimension: int, device: torch.device):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    if saved["category"] != category or saved["dimension"] != dimension:
        raise ValueError(f"Checkpoint/category mismatch: {path}")
    head = NormalPatchAutoencoder(dimension, saved["bottleneck"])
    head.load_state_dict(saved["state_dict"])
    return head.eval().to(device)


def evaluate(args: argparse.Namespace) -> list[dict]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    encoder = DINOv3Encoder(device=str(device))
    rows = []
    for category in CATEGORIES:
        memory = torch.load(args.memory / f"{category}.pt", map_location="cpu", weights_only=True)["patches"].float().to(device)
        head = load_head(args.heads / f"{category}_head.pt", category, memory.shape[1], device)
        for group in GROUPS:
            images = sorted(path for path in (args.dataset / category / "test" / group).glob("*") if path.suffix.lower() in EXTENSIONS)
            if not images:
                raise FileNotFoundError(f"No images in {category}/{group}")
            for image_path in images[:args.max_images] if args.max_images else images:
                with Image.open(image_path) as original:
                    width, height = original.size
                mask = np.zeros((height, width), dtype=bool)
                for mask_path in find_masks(args.dataset, category, group, image_path):
                    with Image.open(mask_path) as source:
                        mask |= np.asarray(source.convert("L").resize((width, height), Image.Resampling.NEAREST)) > 0
                gt_box = mask_box(mask)
                if gt_box is None:
                    raise ValueError(f"Anomaly mask contains no positive pixels: {image_path}")
                with torch.inference_mode():
                    patches = F.normalize(encoder.encode(image_path)["patches"].squeeze(0).float().to(device), dim=1)
                    nearest = torch.cat([1 - (chunk @ memory.T).max(dim=1).values for chunk in patches.split(64)])
                    reconstructed = reconstruction_distances(head, patches)
                    maps = {"baseline": nearest, "trained": reconstructed, "fusion": (nearest + reconstructed) / 2}
                    for method, patch_distances in maps.items():
                        grid = int(patch_distances.numel() ** .5)
                        patch_map = patch_distances.reshape(grid, grid).cpu().numpy()
                        low, high = float(patch_map.min()), float(patch_map.max())
                        display_map = (patch_map - low) / (high - low) if high > low else np.zeros_like(patch_map)
                        predicted = anomaly_map_to_bounding_box(display_map, (width, height))["pixel"]
                        pixel_map = F.interpolate(torch.as_tensor(patch_map)[None,None], size=(height,width), mode="bilinear", align_corners=False).reshape(-1).numpy()
                        iou = box_iou(predicted, gt_box)
                        rows.append({"category": category, "group": group, "image_path": str(image_path),
                                     "method": method, "pixel_auroc": float(roc_auc_score(mask.reshape(-1), pixel_map)),
                                     "single_box_iou": iou, "single_box_recall_at_50": float(iou >= .5)})
                        if args.save_maps:
                            map_dir = args.output / "patch_maps" / category / group
                            map_dir.mkdir(parents=True, exist_ok=True)
                            np.savez_compressed(map_dir / f"{image_path.stem}_{method}.npz",
                                                patch_map=patch_map, image_size=np.array([width, height]))
                print(f"{category}/{group}: {image_path.name}", flush=True)
        del memory, head
        if device.type == "cuda":
            torch.cuda.empty_cache()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--memory", type=Path, default=Path("cloud/space/assets"))
    parser.add_argument("--heads", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/runtime/localization/seed42"))
    parser.add_argument("--max-images", type=int, default=0, help="Quick pipeline check only; omit for complete report")
    parser.add_argument("--save-maps", action="store_true", help="Also retain raw 14x14 maps for later official-protocol formatting")
    args = parser.parse_args()
    if args.max_images < 0:
        parser.error("--max-images cannot be negative")
    rows = evaluate(args)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "per_image.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {"protocol": "Cloud compact bank and one chosen head seed; all anomalous test images and masks; mean per-image pixel AUROC and single enclosing-mask-box IoU. Not official LOCO sPRO or object-detection mAP50.", "heads": str(args.heads),
              "complete": args.max_images == 0, "results": {}}
    for category in CATEGORIES:
        report["results"][category] = {}
        for method in ("baseline", "trained", "fusion"):
            subset = [r for r in rows if r["category"] == category and r["method"] == method]
            report["results"][category][method] = {"images": len(subset), **{
                key: mean(r[key] for r in subset)
                for key in ("pixel_auroc", "single_box_iou", "single_box_recall_at_50")}}
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {len(rows)} method/image rows to {args.output}")


if __name__ == "__main__":
    main()
