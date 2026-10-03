from __future__ import annotations

import sys
from pathlib import Path

# ============================================================
# Project root import fix
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import argparse
import csv
import json
import time

import numpy as np
import torch
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
)

from vision.dinov3_encoder import DINOv3Encoder


# ============================================================
# Configuration
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

CATEGORIES = [
    "breakfast_box",
    "juice_bottle",
    "pushpins",
    "screw_bag",
    "splicing_connectors",
]


# ============================================================
# Utility functions
# ============================================================

def find_images(directory: Path) -> list[Path]:
    """Recursively find all supported image files."""
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_normal_patch_memory(
    feature_dir: Path,
) -> torch.Tensor:
    """
    Load DINOv3 patch features from train/good
    and construct a cosine-normalized memory bank.
    """

    feature_files = sorted(
        feature_dir.rglob("*.pt")
    )

    if not feature_files:
        raise FileNotFoundError(
            f"No feature files found in:\n{feature_dir}"
        )

    all_patches = []

    print(
        f"Loading {len(feature_files)} normal feature files..."
    )

    for index, feature_file in enumerate(
        feature_files,
        start=1,
    ):

        data = torch.load(
            feature_file,
            weights_only=True,
        )

        patches = data["patches"].float()

        if patches.ndim != 3:
            raise ValueError(
                f"Unexpected patch shape in "
                f"{feature_file}: {tuple(patches.shape)}"
            )

        patches = patches.squeeze(0)

        all_patches.append(patches)

        if index % 100 == 0 or index == len(feature_files):
            print(
                f"Loaded {index}/{len(feature_files)}"
            )

    memory_bank = torch.cat(
        all_patches,
        dim=0,
    )

    memory_bank = torch.nn.functional.normalize(
        memory_bank,
        p=2,
        dim=1,
    )

    print(
        f"Memory bank shape: "
        f"{tuple(memory_bank.shape)}"
    )

    return memory_bank


@torch.inference_mode()
def score_image_max_patch(
    encoder: DINOv3Encoder,
    image_path: Path,
    memory_bank: torch.Tensor,
    device: torch.device,
    patch_batch_size: int = 32,
) -> tuple[float, tuple[int, int]]:

    features = encoder.encode(
        image_path
    )

    patches = (
        features["patches"]
        .squeeze(0)
        .float()
    )

    patches = torch.nn.functional.normalize(
        patches,
        p=2,
        dim=1,
    )

    distances = []

    for start in range(
        0,
        patches.shape[0],
        patch_batch_size,
    ):

        end = min(
            start + patch_batch_size,
            patches.shape[0],
        )

        query = patches[start:end].to(
            device
        )

        similarities = torch.matmul(
            query,
            memory_bank.T,
        )

        best_similarity = similarities.max(
            dim=1
        ).values

        patch_distance = (
            1.0 - best_similarity
        )

        distances.append(
            patch_distance.cpu()
        )

    distances = torch.cat(
        distances
    )

    max_index = int(
        torch.argmax(distances)
    )

    # 14x14 for the current setup.
    patch_count = len(distances)
    grid_size = int(np.sqrt(patch_count))

    if grid_size * grid_size != patch_count:
        raise ValueError(
            f"Patch count {patch_count} "
            f"is not a square number."
        )

    row = max_index // grid_size
    col = max_index % grid_size

    max_score = float(
        distances.max().item()
    )

    return (
        max_score,
        (row, col),
    )


def evaluate_category(
    category: str,
    dataset_root: Path,
    features_root: Path,
    encoder: DINOv3Encoder,
    device: torch.device,
) -> list[dict]:

    category_root = (
        dataset_root / category
    )

    feature_root = (
        features_root
        / category
        / "train"
        / "good"
    )

    train_good = (
        category_root
        / "train"
        / "good"
    )

    test_good = (
        category_root
        / "test"
        / "good"
    )

    test_logical = (
        category_root
        / "test"
        / "logical_anomalies"
    )

    test_structural = (
        category_root
        / "test"
        / "structural_anomalies"
    )

    required = [
        train_good,
        test_good,
        test_logical,
        test_structural,
        feature_root,
    ]

    for path in required:

        if not path.exists():
            raise FileNotFoundError(
                f"Missing required path:\n{path}"
            )

    print("\n")
    print("=" * 90)
    print(f"CATEGORY: {category}")
    print("=" * 90)

    # --------------------------------------------------------
    # Load category-specific normal memory bank
    # --------------------------------------------------------

    memory_bank = load_normal_patch_memory(
        feature_root
    )

    memory_bank = memory_bank.to(
        device
    )

    # --------------------------------------------------------
    # Test groups
    # --------------------------------------------------------

    test_groups = [
        ("good", test_good, 0),
        (
            "logical_anomalies",
            test_logical,
            1,
        ),
        (
            "structural_anomalies",
            test_structural,
            1,
        ),
    ]

    category_results = []

    for anomaly_type, directory, label in test_groups:

        images = find_images(
            directory
        )

        print(
            f"\n{anomaly_type}: "
            f"{len(images)} images"
        )

        for index, image_path in enumerate(
            images,
            start=1,
        ):

            start_time = time.perf_counter()

            score, max_patch = score_image_max_patch(
                encoder=encoder,
                image_path=image_path,
                memory_bank=memory_bank,
                device=device,
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            category_results.append(
                {
                    "category": category,
                    "image_path": str(image_path),
                    "anomaly_type": anomaly_type,
                    "label": label,
                    "anomaly_score": score,
                    "max_patch_row": max_patch[0],
                    "max_patch_col": max_patch[1],
                    "inference_seconds": elapsed,
                }
            )

            print(
                f"\r[{index}/{len(images)}] "
                f"{image_path.name} "
                f"score={score:.6f}",
                end="",
            )

        print()

    return category_results


# ============================================================
# Calculate metrics
# ============================================================

def calculate_metrics(
    results: list[dict],
) -> dict:

    labels = np.array(
        [
            item["label"]
            for item in results
        ],
        dtype=np.int32,
    )

    scores = np.array(
        [
            item["anomaly_score"]
            for item in results
        ],
        dtype=np.float64,
    )

    overall_auroc = roc_auc_score(
        labels,
        scores,
    )

    overall_ap = average_precision_score(
        labels,
        scores,
    )

    output = {
        "overall": {
            "num_images": len(results),
            "num_normal": int(
                (labels == 0).sum()
            ),
            "num_anomalous": int(
                (labels == 1).sum()
            ),
            "auroc": float(
                overall_auroc
            ),
            "average_precision": float(
                overall_ap
            ),
        }
    }

    # --------------------------------------------------------
    # Per category
    # --------------------------------------------------------

    for category in CATEGORIES:

        category_results = [
            item
            for item in results
            if item["category"] == category
        ]

        category_labels = np.array(
            [
                item["label"]
                for item in category_results
            ],
            dtype=np.int32,
        )

        category_scores = np.array(
            [
                item["anomaly_score"]
                for item in category_results
            ],
            dtype=np.float64,
        )

        category_mean = float(
            category_scores.mean()
        )

        category_auroc = roc_auc_score(
            category_labels,
            category_scores,
        )

        category_ap = average_precision_score(
            category_labels,
            category_scores,
        )

        # ----------------------------------------------------
        # Logical vs good
        # ----------------------------------------------------

        logical = [
            item
            for item in category_results
            if item["anomaly_type"]
            in {
                "good",
                "logical_anomalies",
            }
        ]

        logical_labels = np.array(
            [
                item["label"]
                for item in logical
            ],
            dtype=np.int32,
        )

        logical_scores = np.array(
            [
                item["anomaly_score"]
                for item in logical
            ],
            dtype=np.float64,
        )

        logical_auroc = roc_auc_score(
            logical_labels,
            logical_scores,
        )

        # ----------------------------------------------------
        # Structural vs good
        # ----------------------------------------------------

        structural = [
            item
            for item in category_results
            if item["anomaly_type"]
            in {
                "good",
                "structural_anomalies",
            }
        ]

        structural_labels = np.array(
            [
                item["label"]
                for item in structural
            ],
            dtype=np.int32,
        )

        structural_scores = np.array(
            [
                item["anomaly_score"]
                for item in structural
            ],
            dtype=np.float64,
        )

        structural_auroc = roc_auc_score(
            structural_labels,
            structural_scores,
        )

        # ----------------------------------------------------
        # Mean inference time
        # ----------------------------------------------------

        inference_times = [
            item["inference_seconds"]
            for item in category_results
        ]

        mean_latency = float(
            np.mean(inference_times)
        )

        output[category] = {
            "num_images": len(
                category_results
            ),
            "overall_auroc": float(
                category_auroc
            ),
            "overall_average_precision": float(
                category_ap
            ),
            "logical_auroc": float(
                logical_auroc
            ),
            "structural_auroc": float(
                structural_auroc
            ),
            "mean_inference_seconds": mean_latency,
        }

    # --------------------------------------------------------
    # Mean across categories
    # --------------------------------------------------------

    category_aurocs = [
        output[category][
            "overall_auroc"
        ]
        for category in CATEGORIES
    ]

    category_aps = [
        output[category][
            "overall_average_precision"
        ]
        for category in CATEGORIES
    ]

    logical_aurocs = [
        output[category][
            "logical_auroc"
        ]
        for category in CATEGORIES
    ]

    structural_aurocs = [
        output[category][
            "structural_auroc"
        ]
        for category in CATEGORIES
    ]

    output["mean_across_categories"] = {
        "mean_overall_auroc": float(
            np.mean(category_aurocs)
        ),
        "mean_overall_average_precision": float(
            np.mean(category_aps)
        ),
        "mean_logical_auroc": float(
            np.mean(logical_aurocs)
        ),
        "mean_structural_auroc": float(
            np.mean(structural_aurocs)
        ),
    }

    return output


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate DINOv3 max-patch anomaly "
            "scoring across all MVTec LOCO AD categories."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help=(
            "Root directory containing the five "
            "LOCO AD categories."
        ),
    )

    parser.add_argument(
        "--features",
        type=Path,
        required=True,
        help=(
            "Root directory containing pre-extracted "
            "DINOv3 features."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/all_categories"
        ),
    )

    args = parser.parse_args()

    dataset_root = args.dataset
    features_root = args.features
    output_dir = args.output_dir

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 90)
    print("DINOv3 MAX-PATCH EVALUATION")
    print("=" * 90)
    print(f"Device: {device}")
    print(
        "Categories:",
        ", ".join(CATEGORIES),
    )

    # --------------------------------------------------------
    # Load DINOv3 ONCE
    # --------------------------------------------------------

    encoder = DINOv3Encoder()

    # --------------------------------------------------------
    # Evaluate all categories
    # --------------------------------------------------------

    all_results = []

    for category in CATEGORIES:

        category_results = evaluate_category(
            category=category,
            dataset_root=dataset_root,
            features_root=features_root,
            encoder=encoder,
            device=device,
        )

        all_results.extend(
            category_results
        )

        # Free GPU memory between categories.
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    metrics = calculate_metrics(
        all_results
    )

    # --------------------------------------------------------
    # Save image-level CSV
    # --------------------------------------------------------

    csv_path = (
        output_dir
        / "all_categories_scores.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        fieldnames = [
            "category",
            "image_path",
            "anomaly_type",
            "label",
            "anomaly_score",
            "max_patch_row",
            "max_patch_col",
            "inference_seconds",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            all_results
        )

    # --------------------------------------------------------
    # Save JSON metrics
    # --------------------------------------------------------

    json_path = (
        output_dir
        / "all_categories_metrics.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metrics,
            f,
            indent=4,
        )

    # --------------------------------------------------------
    # Print final table
    # --------------------------------------------------------

    print("\n")
    print("=" * 110)
    print("FINAL MULTI-CATEGORY EVALUATION")
    print("=" * 110)

    print(
        f"{'Category':<24}"
        f"{'Overall':>12}"
        f"{'Logical':>12}"
        f"{'Structural':>14}"
        f"{'AP':>12}"
        f"{'Latency(s)':>14}"
    )

    print("-" * 110)

    for category in CATEGORIES:

        row = metrics[category]

        print(
            f"{category:<24}"
            f"{row['overall_auroc']:>12.4f}"
            f"{row['logical_auroc']:>12.4f}"
            f"{row['structural_auroc']:>14.4f}"
            f"{row['overall_average_precision']:>12.4f}"
            f"{row['mean_inference_seconds']:>14.4f}"
        )

    print("-" * 110)

    mean_row = (
        metrics[
            "mean_across_categories"
        ]
    )

    print(
        f"{'MEAN':<24}"
        f"{mean_row['mean_overall_auroc']:>12.4f}"
        f"{mean_row['mean_logical_auroc']:>12.4f}"
        f"{mean_row['mean_structural_auroc']:>14.4f}"
        f"{mean_row['mean_overall_average_precision']:>12.4f}"
    )

    print("\n")
    print("Overall pooled evaluation:")
    print(
        f"AUROC: "
        f"{metrics['overall']['auroc']:.4f}"
    )

    print(
        f"Average Precision: "
        f"{metrics['overall']['average_precision']:.4f}"
    )

    print("\nSaved:")
    print(
        f"CSV:  {csv_path}"
    )

    print(
        f"JSON: {json_path}"
    )

    print("=" * 110)


if __name__ == "__main__":
    main()