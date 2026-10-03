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

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
)

from vision.dinov3_encoder import DINOv3Encoder


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

def find_images(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_feature_files(feature_dir: Path):
    """
    Load pre-extracted DINOv3 features from training-good images.

    Returns:
        patch_memory: [N_patches, D]
        global_memory: [N_images, D]
        patch_grid: (H, W)
    """

    files = sorted(feature_dir.rglob("*.pt"))

    if not files:
        raise RuntimeError(
            f"No feature files found in {feature_dir}"
        )

    all_patches = []
    all_global = []

    patch_grid = None

    print(f"Loading {len(files)} normal feature files...")

    for index, file_path in enumerate(files, start=1):

        data = torch.load(
            file_path,
            weights_only=True,
        )

        patches = data["patches"].float().squeeze(0)
        pooled = data["pooled"].float().squeeze(0)

        num_patches = patches.shape[0]
        side = int(np.sqrt(num_patches))

        if side * side != num_patches:
            raise ValueError(
                f"Patch count {num_patches} in "
                f"{file_path} is not square."
            )

        patch_grid = (side, side)

        all_patches.append(patches)
        all_global.append(pooled)

        if index % 100 == 0 or index == len(files):
            print(
                f"Loaded {index}/{len(files)}"
            )

    patch_memory = torch.cat(
        all_patches,
        dim=0,
    )

    global_memory = torch.stack(
        all_global,
        dim=0,
    )

    # L2 normalization for cosine similarity.
    patch_memory = F.normalize(
        patch_memory,
        p=2,
        dim=1,
    )

    global_memory = F.normalize(
        global_memory,
        p=2,
        dim=1,
    )

    return (
        patch_memory,
        global_memory,
        patch_grid,
    )


def top_fraction_mean(
    distances: torch.Tensor,
    fraction: float,
) -> float:

    k = max(
        1,
        int(len(distances) * fraction),
    )

    return torch.topk(
        distances,
        k=k,
    ).values.mean().item()


def top_k_mean(
    distances: torch.Tensor,
    k: int,
) -> float:

    k = min(
        k,
        len(distances),
    )

    return torch.topk(
        distances,
        k=k,
    ).values.mean().item()


# ============================================================
# Scoring
# ============================================================

@torch.inference_mode()
def score_image(
    encoder: DINOv3Encoder,
    image_path: Path,
    patch_memory: torch.Tensor,
    global_memory: torch.Tensor,
    device: torch.device,
    patch_batch_size: int = 32,
) -> dict:
    """
    Compute raw patch and global anomaly information.
    """

    features = encoder.encode(
        image_path
    )

    patches = features["patches"].squeeze(0).float()

    pooled = features["pooled"].squeeze(0).float()

    patches = F.normalize(
        patches,
        p=2,
        dim=1,
    )

    pooled = F.normalize(
        pooled,
        p=2,
        dim=0,
    )

    # --------------------------------------------------------
    # Local patch anomaly
    # --------------------------------------------------------

    patch_distances = []

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
            patch_memory.T,
        )

        best_similarity = similarities.max(
            dim=1
        ).values

        distances = 1.0 - best_similarity

        patch_distances.append(
            distances.cpu()
        )

    patch_distances = torch.cat(
        patch_distances,
        dim=0,
    )

    # --------------------------------------------------------
    # Local scores
    # --------------------------------------------------------

    max_score = patch_distances.max().item()

    top5_score = top_k_mean(
        patch_distances,
        5,
    )

    top10_percent_score = top_fraction_mean(
        patch_distances,
        0.10,
    )

    top20_percent_score = top_fraction_mean(
        patch_distances,
        0.20,
    )

    # --------------------------------------------------------
    # Global anomaly
    # --------------------------------------------------------

    global_similarity = torch.matmul(
        global_memory.to(device),
        pooled.to(device),
    )

    best_global_similarity = (
        global_similarity.max().item()
    )

    global_score = (
        1.0 - best_global_similarity
    )

    return {
        "max_score": float(max_score),
        "top5_score": float(top5_score),
        "top10_score": float(top10_percent_score),
        "top20_score": float(top20_percent_score),
        "global_score": float(global_score),
        "patch_distances": patch_distances.numpy(),
    }


# ============================================================
# Normalization for fusion
# ============================================================

def robust_normalize(values: np.ndarray) -> np.ndarray:
    """
    Convert raw scores to approximately [0, 1]
    using percentile-based normalization.

    This is used only for the exploratory fusion ablation.
    """

    low = np.percentile(
        values,
        5,
    )

    high = np.percentile(
        values,
        95,
    )

    if high <= low:
        return np.zeros_like(values)

    normalized = (
        values - low
    ) / (
        high - low
    )

    return np.clip(
        normalized,
        0.0,
        1.0,
    )


# ============================================================
# Evaluation helpers
# ============================================================

def evaluate_metric(
    labels: np.ndarray,
    scores: np.ndarray,
) -> tuple[float, float]:

    auroc = roc_auc_score(
        labels,
        scores,
    )

    ap = average_precision_score(
        labels,
        scores,
    )

    return (
        float(auroc),
        float(ap),
    )


def evaluate_subset(
    results: list[dict],
    score_key: str,
    anomaly_type: str | None = None,
) -> tuple[float, float]:

    if anomaly_type is None:

        selected = results

    else:

        selected = [
            item
            for item in results
            if item["anomaly_type"]
            in {
                "good",
                anomaly_type,
            }
        ]

    labels = np.array(
        [
            item["label"]
            for item in selected
        ]
    )

    scores = np.array(
        [
            item[score_key]
            for item in selected
        ]
    )

    return evaluate_metric(
        labels,
        scores,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "DINOv3 anomaly-score ablation on "
            "MVTec LOCO AD."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--features",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/breakfast_box_ablation"
        ),
    )

    parser.add_argument(
        "--fusion-alpha",
        type=float,
        default=0.7,
        help=(
            "Weight assigned to local top-10%% score "
            "in exploratory global+local fusion."
        ),
    )

    args = parser.parse_args()

    dataset = args.dataset
    feature_dir = args.features
    output_dir = args.output_dir

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Dataset paths
    # --------------------------------------------------------

    test_dirs = {
        "good": dataset / "test" / "good",
        "logical_anomalies": (
            dataset
            / "test"
            / "logical_anomalies"
        ),
        "structural_anomalies": (
            dataset
            / "test"
            / "structural_anomalies"
        ),
    }

    for name, path in test_dirs.items():

        if not path.exists():
            raise FileNotFoundError(
                f"Missing test directory: {path}"
            )

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 80)
    print("DINOv3 ANOMALY SCORE ABLATION")
    print("=" * 80)
    print(f"Device: {device}")

    # --------------------------------------------------------
    # Load encoder once
    # --------------------------------------------------------

    encoder = DINOv3Encoder()

    # --------------------------------------------------------
    # Load normal memory bank
    # --------------------------------------------------------

    (
        patch_memory,
        global_memory,
        patch_grid,
    ) = load_feature_files(
        feature_dir
    )

    patch_memory = patch_memory.to(
        device
    )

    global_memory = global_memory.to(
        device
    )

    print(
        f"\nPatch memory: "
        f"{tuple(patch_memory.shape)}"
    )

    print(
        f"Global memory: "
        f"{tuple(global_memory.shape)}"
    )

    print(
        f"Patch grid: "
        f"{patch_grid}"
    )

    # --------------------------------------------------------
    # Evaluate all test images
    # --------------------------------------------------------

    all_results = []

    for anomaly_type, directory in test_dirs.items():

        images = find_images(directory)

        label = (
            0
            if anomaly_type == "good"
            else 1
        )

        print("\n" + "=" * 80)
        print(
            f"Evaluating {anomaly_type}: "
            f"{len(images)} images"
        )
        print("=" * 80)

        for index, image_path in enumerate(
            images,
            start=1,
        ):

            print(
                f"[{index}/{len(images)}] "
                f"{image_path.name}",
                end="\r",
            )

            scores = score_image(
                encoder=encoder,
                image_path=image_path,
                patch_memory=patch_memory,
                global_memory=global_memory,
                device=device,
            )

            all_results.append(
                {
                    "image_path": str(
                        image_path
                    ),
                    "label": label,
                    "anomaly_type": anomaly_type,
                    **{
                        key: value
                        for key, value in scores.items()
                        if key != "patch_distances"
                    },
                }
            )

        print()

    # --------------------------------------------------------
    # Convert raw arrays
    # --------------------------------------------------------

    max_scores = np.array(
        [
            item["max_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    top5_scores = np.array(
        [
            item["top5_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    top10_scores = np.array(
        [
            item["top10_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    top20_scores = np.array(
        [
            item["top20_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    global_scores = np.array(
        [
            item["global_score"]
            for item in all_results
        ],
        dtype=np.float64,
    )

    labels = np.array(
        [
            item["label"]
            for item in all_results
        ],
        dtype=np.int32,
    )

    # --------------------------------------------------------
    # Global + local fusion
    # --------------------------------------------------------
    #
    # This is an exploratory ablation. The normalization is
    # performed over the evaluated set because the two raw
    # score scales are different.
    #
    # We will NOT treat this as the final research result until
    # we establish a proper train-only calibration procedure.
    # --------------------------------------------------------

    normalized_local = robust_normalize(
        top10_scores
    )

    normalized_global = robust_normalize(
        global_scores
    )

    alpha = args.fusion_alpha

    fusion_scores = (
        alpha * normalized_local
        + (1.0 - alpha)
        * normalized_global
    )

    # --------------------------------------------------------
    # Score definitions
    # --------------------------------------------------------

    scoring_methods = {
        "max_patch": max_scores,
        "top5_mean": top5_scores,
        "top10_percent_mean": top10_scores,
        "top20_percent_mean": top20_scores,
        "global_only": global_scores,
        "global_local_fusion": fusion_scores,
    }

    # --------------------------------------------------------
    # Build metrics
    # --------------------------------------------------------

    metric_rows = []

    for method_name, scores in scoring_methods.items():

        overall_auroc, overall_ap = (
            evaluate_metric(
                labels,
                scores,
            )
        )

        logical_mask = np.isin(
            np.arange(len(labels)),
            [
                i
                for i, item in enumerate(
                    all_results
                )
                if item["anomaly_type"]
                in {
                    "good",
                    "logical_anomalies",
                }
            ],
        )

        structural_mask = np.isin(
            np.arange(len(labels)),
            [
                i
                for i, item in enumerate(
                    all_results
                )
                if item["anomaly_type"]
                in {
                    "good",
                    "structural_anomalies",
                }
            ],
        )

        logical_auroc, logical_ap = (
            evaluate_metric(
                labels[logical_mask],
                scores[logical_mask],
            )
        )

        structural_auroc, structural_ap = (
            evaluate_metric(
                labels[structural_mask],
                scores[structural_mask],
            )
        )

        metric_rows.append(
            {
                "method": method_name,
                "overall_auroc": overall_auroc,
                "overall_ap": overall_ap,
                "logical_auroc": logical_auroc,
                "logical_ap": logical_ap,
                "structural_auroc": (
                    structural_auroc
                ),
                "structural_ap": structural_ap,
            }
        )

    # --------------------------------------------------------
    # Save metrics CSV
    # --------------------------------------------------------

    metrics_csv = (
        output_dir
        / "ablation_metrics.csv"
    )

    with open(
        metrics_csv,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "overall_auroc",
                "overall_ap",
                "logical_auroc",
                "logical_ap",
                "structural_auroc",
                "structural_ap",
            ],
        )

        writer.writeheader()

        writer.writerows(
            metric_rows
        )

    # --------------------------------------------------------
    # Save image-level scores
    # --------------------------------------------------------

    scores_csv = (
        output_dir
        / "ablation_scores.csv"
    )

    with open(
        scores_csv,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        fieldnames = [
            "image_path",
            "label",
            "anomaly_type",
            "max_patch",
            "top5_mean",
            "top10_percent_mean",
            "top20_percent_mean",
            "global_only",
            "global_local_fusion",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for index, item in enumerate(
            all_results
        ):

            writer.writerow(
                {
                    "image_path": item[
                        "image_path"
                    ],
                    "label": item["label"],
                    "anomaly_type": item[
                        "anomaly_type"
                    ],
                    "max_patch": item[
                        "max_score"
                    ],
                    "top5_mean": item[
                        "top5_score"
                    ],
                    "top10_percent_mean": item[
                        "top10_score"
                    ],
                    "top20_percent_mean": item[
                        "top20_score"
                    ],
                    "global_only": item[
                        "global_score"
                    ],
                    "global_local_fusion": fusion_scores[
                        index
                    ],
                }
            )

    # --------------------------------------------------------
    # Save JSON summary
    # --------------------------------------------------------

    summary = {
        "dataset": str(dataset),
        "num_images": len(all_results),
        "fusion_alpha": alpha,
        "methods": metric_rows,
        "notes": [
            (
                "global_local_fusion uses "
                "evaluation-set percentile "
                "normalization and is therefore "
                "exploratory, not a final calibrated "
                "research metric."
            )
        ],
    }

    json_path = (
        output_dir
        / "ablation_summary.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            indent=4,
        )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n")
    print("=" * 100)
    print("ANOMALY SCORE ABLATION RESULTS")
    print("=" * 100)

    header = (
        f"{'Method':<24}"
        f"{'Overall':>12}"
        f"{'Logical':>12}"
        f"{'Structural':>14}"
        f"{'AP Overall':>14}"
    )

    print(header)
    print("-" * 100)

    for row in metric_rows:

        print(
            f"{row['method']:<24}"
            f"{row['overall_auroc']:>12.4f}"
            f"{row['logical_auroc']:>12.4f}"
            f"{row['structural_auroc']:>14.4f}"
            f"{row['overall_ap']:>14.4f}"
        )

    # --------------------------------------------------------
    # Best method
    # --------------------------------------------------------

    best = max(
        metric_rows,
        key=lambda row: row[
            "overall_auroc"
        ],
    )

    print("\n")
    print(
        f"Best by overall AUROC: "
        f"{best['method']}"
    )

    print(
        f"AUROC: "
        f"{best['overall_auroc']:.4f}"
    )

    print("\nSaved:")
    print(
        f"Metrics: {metrics_csv}"
    )

    print(
        f"Scores:  {scores_csv}"
    )

    print(
        f"Summary: {json_path}"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()