from __future__ import annotations

import sys
from pathlib import Path

# ============================================================
# Make project root importable when running:
# python vision/evaluate_anomaly.py
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import argparse
import csv
import json
from typing import List, Dict

import numpy as np
import torch
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
)

from vision.dinov3_encoder import DINOv3Encoder
from vision.anomaly_scorer import DINOv3AnomalyScorer


# ============================================================
# Supported image extensions
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# Utilities
# ============================================================

def find_images(directory: Path) -> List[Path]:
    """Recursively find supported image files."""
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def evaluate_directory(
    scorer: DINOv3AnomalyScorer,
    directory: Path,
    label: int,
    anomaly_type: str,
) -> List[Dict]:

    images = find_images(directory)

    print()
    print("=" * 80)
    print(f"Evaluating: {anomaly_type}")
    print(f"Directory:  {directory}")
    print(f"Images:     {len(images)}")
    print("=" * 80)

    results = []

    for index, image_path in enumerate(images, start=1):

        print(
            f"\n[{index}/{len(images)}] "
            f"{image_path.name}"
        )

        try:
            result = scorer.score_image(
                image_path
            )

            anomaly_score = float(
                result["anomaly_score"]
            )

            max_row, max_col = result["max_patch"]

            results.append(
                {
                    "image_path": str(image_path),
                    "label": label,
                    "anomaly_type": anomaly_type,
                    "anomaly_score": anomaly_score,
                    "max_patch_row": max_row,
                    "max_patch_col": max_col,
                }
            )

            print(
                f"Score: {anomaly_score:.6f}"
            )

        except Exception as exc:

            print(
                f"ERROR processing {image_path}: "
                f"{exc}"
            )

    return results


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate DINOv3 patch-based anomaly "
            "detection on MVTec LOCO AD."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help=(
            "Path to one LOCO AD category, "
            "e.g. .../breakfast_box"
        ),
    )

    parser.add_argument(
        "--features",
        type=Path,
        required=True,
        help=(
            "Directory containing DINOv3 features "
            "for train/good."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/evaluation"),
        help="Directory for evaluation outputs.",
    )

    parser.add_argument(
        "--max-memory-patches",
        type=int,
        default=None,
        help=(
            "Optional memory-bank cap. "
            "Leave unset initially."
        ),
    )

    args = parser.parse_args()

    dataset_dir = args.dataset
    feature_dir = args.features
    output_dir = args.output_dir

    # --------------------------------------------------------
    # Validate paths
    # --------------------------------------------------------

    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory does not exist:\n"
            f"{dataset_dir}"
        )

    if not feature_dir.exists():
        raise FileNotFoundError(
            f"Feature directory does not exist:\n"
            f"{feature_dir}"
        )

    train_good_dir = (
        dataset_dir
        / "train"
        / "good"
    )

    test_good_dir = (
        dataset_dir
        / "test"
        / "good"
    )

    test_logical_dir = (
        dataset_dir
        / "test"
        / "logical_anomalies"
    )

    test_structural_dir = (
        dataset_dir
        / "test"
        / "structural_anomalies"
    )

    required_dirs = [
        train_good_dir,
        test_good_dir,
        test_logical_dir,
        test_structural_dir,
    ]

    for directory in required_dirs:

        if not directory.exists():
            raise FileNotFoundError(
                f"Required directory not found:\n"
                f"{directory}"
            )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load DINOv3 once
    # --------------------------------------------------------

    print("=" * 80)
    print("INITIALIZING DINOv3 ANOMALY EVALUATOR")
    print("=" * 80)

    encoder = DINOv3Encoder()

    scorer = DINOv3AnomalyScorer(
        feature_dir=feature_dir,
        encoder=encoder,
        max_memory_patches=args.max_memory_patches,
    )

    # --------------------------------------------------------
    # Evaluate three groups
    # --------------------------------------------------------

    all_results = []

    # Normal
    all_results.extend(
        evaluate_directory(
            scorer=scorer,
            directory=test_good_dir,
            label=0,
            anomaly_type="good",
        )
    )

    # Logical anomalies
    all_results.extend(
        evaluate_directory(
            scorer=scorer,
            directory=test_logical_dir,
            label=1,
            anomaly_type="logical_anomalies",
        )
    )

    # Structural anomalies
    all_results.extend(
        evaluate_directory(
            scorer=scorer,
            directory=test_structural_dir,
            label=1,
            anomaly_type="structural_anomalies",
        )
    )

    if not all_results:
        raise RuntimeError(
            "No evaluation results were produced."
        )

    # ========================================================
    # Extract labels and scores
    # ========================================================

    labels = np.array(
        [
            item["label"]
            for item in all_results
        ],
        dtype=np.int32,
    )

    scores = np.array(
        [
            item["anomaly_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    # ========================================================
    # Overall metrics
    # ========================================================

    overall_auroc = roc_auc_score(
        labels,
        scores,
    )

    overall_ap = average_precision_score(
        labels,
        scores,
    )

    # ========================================================
    # Per-category metrics
    # ========================================================

    metric_summary = {
        "overall": {
            "num_images": int(len(all_results)),
            "num_normal": int((labels == 0).sum()),
            "num_anomalous": int((labels == 1).sum()),
            "auroc": float(overall_auroc),
            "average_precision": float(overall_ap),
        }
    }

    for anomaly_type in [
        "logical_anomalies",
        "structural_anomalies",
    ]:

        subset = [
            item
            for item in all_results
            if item["anomaly_type"] == anomaly_type
        ]

        good_subset = [
            item
            for item in all_results
            if item["anomaly_type"] == "good"
        ]

        comparison = (
            good_subset
            + subset
        )

        comparison_labels = np.array(
            [
                item["label"]
                for item in comparison
            ],
            dtype=np.int32,
        )

        comparison_scores = np.array(
            [
                item["anomaly_score"]
                for item in comparison
            ],
            dtype=np.float64,
        )

        metric_summary[anomaly_type] = {
            "num_anomaly_images": len(subset),
            "auroc_vs_good": float(
                roc_auc_score(
                    comparison_labels,
                    comparison_scores,
                )
            ),
            "average_precision_vs_good": float(
                average_precision_score(
                    comparison_labels,
                    comparison_scores,
                )
            ),
        }

    # ========================================================
    # Score statistics
    # ========================================================

    score_stats = {}

    for anomaly_type in [
        "good",
        "logical_anomalies",
        "structural_anomalies",
    ]:

        category_scores = np.array(
            [
                item["anomaly_score"]
                for item in all_results
                if item["anomaly_type"] == anomaly_type
            ],
            dtype=np.float64,
        )

        score_stats[anomaly_type] = {
            "count": int(len(category_scores)),
            "mean": float(category_scores.mean()),
            "std": float(category_scores.std()),
            "min": float(category_scores.min()),
            "max": float(category_scores.max()),
            "median": float(
                np.median(category_scores)
            ),
        }

    metric_summary["score_statistics"] = score_stats

    # ========================================================
    # Save CSV
    # ========================================================

    csv_path = (
        output_dir
        / "anomaly_scores.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_path",
                "label",
                "anomaly_type",
                "anomaly_score",
                "max_patch_row",
                "max_patch_col",
            ],
        )

        writer.writeheader()

        writer.writerows(
            all_results
        )

    # ========================================================
    # Save JSON summary
    # ========================================================

    json_path = (
        output_dir
        / "evaluation_summary.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metric_summary,
            f,
            indent=4,
        )

    # ========================================================
    # Print final report
    # ========================================================

    print("\n")
    print("=" * 80)
    print("FINAL ANOMALY DETECTION EVALUATION")
    print("=" * 80)

    print(
        f"\nTotal images: "
        f"{len(all_results)}"
    )

    print(
        f"Normal images: "
        f"{(labels == 0).sum()}"
    )

    print(
        f"Anomalous images: "
        f"{(labels == 1).sum()}"
    )

    print("\nOverall:")
    print(
        f"AUROC: "
        f"{overall_auroc:.4f}"
    )

    print(
        f"Average Precision: "
        f"{overall_ap:.4f}"
    )

    print("\nPer anomaly type:")

    for anomaly_type in [
        "logical_anomalies",
        "structural_anomalies",
    ]:

        values = metric_summary[
            anomaly_type
        ]

        print(
            f"\n{anomaly_type}:"
        )

        print(
            f"  AUROC vs good: "
            f"{values['auroc_vs_good']:.4f}"
        )

        print(
            f"  AP vs good: "
            f"{values['average_precision_vs_good']:.4f}"
        )

    print("\nScore statistics:")

    for anomaly_type, stats in score_stats.items():

        print(
            f"\n{anomaly_type}:"
        )

        print(
            f"  Mean:   {stats['mean']:.6f}"
        )

        print(
            f"  Std:    {stats['std']:.6f}"
        )

        print(
            f"  Median: {stats['median']:.6f}"
        )

        print(
            f"  Min:    {stats['min']:.6f}"
        )

        print(
            f"  Max:    {stats['max']:.6f}"
        )

    print("\nSaved:")
    print(
        f"  CSV:  {csv_path}"
    )

    print(
        f"  JSON: {json_path}"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()