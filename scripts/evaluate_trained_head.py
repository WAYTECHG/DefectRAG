"""Evaluate the compact baseline and trained head on held-out LOCO test images."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from torch.nn import functional as F

from vision.dinov3_encoder import DINOv3Encoder
from vision.normal_autoencoder import (
    NormalPatchAutoencoder,
    reconstruction_distances,
    top_tenth_score,
)

CATEGORIES = (
    "breakfast_box",
    "juice_bottle",
    "pushpins",
    "screw_bag",
    "splicing_connectors",
)
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def image_paths(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Missing test directory: {folder}")
    return sorted(
        path
        for path in folder.rglob("*")
        if path.suffix.lower() in EXTENSIONS
    )


def load_head(
    path: Path,
    category: str,
    dimension: int,
    device: torch.device,
) -> NormalPatchAutoencoder:
    if not path.is_file():
        raise FileNotFoundError(
            f"Train the {category} head first: {path}"
        )

    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=True,
    )
    if (
        checkpoint["category"] != category
        or checkpoint["dimension"] != dimension
    ):
        raise ValueError(
            f"Checkpoint/category/dimension mismatch: {path}"
        )

    model = NormalPatchAutoencoder(
        dimension,
        int(checkpoint["bottleneck"]),
    )
    model.load_state_dict(checkpoint["state_dict"])
    return model.eval().to(device)


def summarize(rows: list[dict], key: str) -> dict:
    labels = np.asarray(
        [row["label"] for row in rows],
        dtype=int,
    )
    scores = np.asarray(
        [row[key] for row in rows],
        dtype=float,
    )

    if len(np.unique(labels)) != 2:
        raise ValueError(
            "Evaluation requires both normal and anomalous test images"
        )

    return {
        "num_images": len(rows),
        "num_normal": int((labels == 0).sum()),
        "num_anomalous": int((labels == 1).sum()),
        "auroc": float(roc_auc_score(labels, scores)),
        "average_precision": float(
            average_precision_score(labels, scores)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--memory",
        type=Path,
        default=Path("cloud/space/assets"),
    )
    parser.add_argument(
        "--heads",
        type=Path,
        default=Path("cloud/space/assets"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/trained_head"),
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    encoder = DINOv3Encoder(device=str(device))
    rows: list[dict] = []

    for category in CATEGORIES:
        memory_path = args.memory / f"{category}.pt"
        memory_data = torch.load(
            memory_path,
            map_location="cpu",
            weights_only=True,
        )

        # Match the Space: memory was normalized before FP16 storage.
        memory = memory_data["patches"].float().to(device)
        head = load_head(
            args.heads / f"{category}_head.pt",
            category,
            memory.shape[1],
            device,
        )

        for group, label in (
            ("good", 0),
            ("logical_anomalies", 1),
            ("structural_anomalies", 1),
        ):
            paths = image_paths(
                args.dataset / category / "test" / group
            )

            for index, image_path in enumerate(paths, 1):
                with torch.inference_mode():
                    patches = F.normalize(
                        encoder.encode(image_path)["patches"]
                        .squeeze(0)
                        .float()
                        .to(device),
                        dim=1,
                    )

                    nearest = torch.cat([
                        1.0 - (chunk @ memory.T).max(dim=1).values
                        for chunk in patches.split(64)
                    ])
                    reconstruction = reconstruction_distances(
                        head,
                        patches,
                    )

                    # Fixed before looking at test labels.
                    fused = (nearest + reconstruction) / 2.0

                    result = {
                        "category": category,
                        "group": group,
                        "label": label,
                        "image_path": str(image_path),
                        "baseline_score": top_tenth_score(nearest),
                        "trained_score": top_tenth_score(
                            reconstruction
                        ),
                        "fusion_score": top_tenth_score(fused),
                    }

                rows.append(result)

                if index % 25 == 0 or index == len(paths):
                    print(
                        f"{category}/{group}: "
                        f"{index}/{len(paths)}",
                        flush=True,
                    )

        del memory, head
        if device.type == "cuda":
            torch.cuda.empty_cache()

    if not rows:
        raise ValueError("No test images found")

    with (args.output / "scores.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    report: dict = {
        "protocol": {
            "training": (
                "Normal train/good patch features only; normal "
                "images split by image into training/validation"
            ),
            "evaluation": (
                "Held-out test/good versus test/logical_anomalies "
                "and test/structural_anomalies"
            ),
            "baseline": (
                "20,000-patch compact memory, cosine "
                "nearest-normal, top 10% mean"
            ),
            "trained": (
                "Frozen DINOv3 plus normal-patch autoencoder, "
                "cosine reconstruction, top 10% mean"
            ),
            "fusion": (
                "Fixed equal-weight per-patch "
                "baseline/reconstruction distances, top 10% mean"
            ),
            "caution": (
                "No anomaly validation set; do not select a "
                "method or operating threshold using this test "
                "set and then report its performance as "
                "independently held-out. Scores are not "
                "calibrated probabilities."
            ),
        },
        "methods": {},
    }

    for key in (
        "baseline_score",
        "trained_score",
        "fusion_score",
    ):
        category_scores = {}

        for category in CATEGORIES:
            subset = [
                row
                for row in rows
                if row["category"] == category
            ]
            category_scores[category] = summarize(
                subset,
                key,
            )
            category_scores[category]["logical_auroc"] = (
                summarize(
                    [
                        row
                        for row in subset
                        if row["group"]
                        != "structural_anomalies"
                    ],
                    key,
                )["auroc"]
            )
            category_scores[category]["structural_auroc"] = (
                summarize(
                    [
                        row
                        for row in subset
                        if row["group"]
                        != "logical_anomalies"
                    ],
                    key,
                )["auroc"]
            )

        report["methods"][key] = {
            "pooled": summarize(rows, key),
            "categories": category_scores,
            "mean_category_auroc": float(
                np.mean([
                    item["auroc"]
                    for item in category_scores.values()
                ])
            ),
        }

    (args.output / "metrics.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    for key, result in report["methods"].items():
        print(
            f"{key}: pooled AUROC="
            f"{result['pooled']['auroc']:.4f}, "
            f"AP={result['pooled']['average_precision']:.4f}, "
            f"mean-category AUROC="
            f"{result['mean_category_auroc']:.4f}"
        )

    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()