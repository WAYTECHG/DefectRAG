from __future__ import annotations

import sys
from pathlib import Path

# ============================================================
# Project root import
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
from PIL import Image
from sklearn.metrics import roc_auc_score

from vision.dinov3_encoder import DINOv3Encoder


# ============================================================
# Configuration
# ============================================================

CATEGORIES = [
    "breakfast_box",
    "juice_bottle",
    "pushpins",
    "screw_bag",
    "splicing_connectors",
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# Find images
# ============================================================

def find_images(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


# ============================================================
# Find ground-truth mask
# ============================================================

def find_mask(
    dataset_category_dir: Path,
    anomaly_type: str,
    image_path: Path,
) -> Path | None:
    """
    Locate the MVTec LOCO AD ground-truth mask.

    Dataset structure:

        test/
            logical_anomalies/
                000.png

        ground_truth/
            logical_anomalies/
                000/
                    000.png

    Same structure applies to structural_anomalies.
    """

    image_stem = image_path.stem

    mask_dir = (
        dataset_category_dir
        / "ground_truth"
        / anomaly_type
        / image_stem
    )

    if not mask_dir.exists():
        return None

    # Expected mask:
    # ground_truth/<type>/<image_id>/<image_id>.png

    exact_mask = (
        mask_dir
        / f"{image_stem}.png"
    )

    if exact_mask.exists():
        return exact_mask

    # Fallback: find the first image inside the folder.
    masks = [
        path
        for path in mask_dir.iterdir()
        if path.is_file()
        and path.suffix.lower()
        in {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".tif",
            ".tiff",
        }
    ]

    if masks:
        return masks[0]

    return None


# ============================================================
# Load normal DINOv3 memory bank
# ============================================================

def load_memory_bank(
    feature_dir: Path,
) -> torch.Tensor:

    feature_files = sorted(
        feature_dir.rglob("*.pt")
    )

    if not feature_files:
        raise FileNotFoundError(
            f"No feature files found in:\n{feature_dir}"
        )

    print(
        f"Loading {len(feature_files)} normal feature files..."
    )

    all_patches = []

    for index, feature_file in enumerate(
        feature_files,
        start=1,
    ):

        data = torch.load(
            feature_file,
            weights_only=True,
        )

        patches = data["patches"]

        if patches.ndim != 3:
            raise ValueError(
                f"Unexpected patch shape in:\n"
                f"{feature_file}\n"
                f"Shape: {tuple(patches.shape)}"
            )

        patches = patches.squeeze(0).float()

        all_patches.append(patches)

        if index % 100 == 0:
            print(
                f"Loaded "
                f"{index}/{len(feature_files)}"
            )

    memory_bank = torch.cat(
        all_patches,
        dim=0,
    )

    memory_bank = F.normalize(
        memory_bank,
        p=2,
        dim=1,
    )

    print(
        f"Memory bank shape: "
        f"{tuple(memory_bank.shape)}"
    )

    return memory_bank


# ============================================================
# Generate anomaly map
# ============================================================

@torch.inference_mode()
def generate_anomaly_map(
    encoder: DINOv3Encoder,
    image_path: Path,
    memory_bank: torch.Tensor,
    device: torch.device,
    patch_batch_size: int = 32,
) -> tuple[np.ndarray, float, tuple[int, int]]:

    features = encoder.encode(
        image_path
    )

    patches = (
        features["patches"]
        .squeeze(0)
        .float()
    )

    patches = F.normalize(
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

        query = patches[
            start:end
        ].to(device)

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

    number_of_patches = distances.shape[0]

    grid_size = int(
        np.sqrt(number_of_patches)
    )

    if (
        grid_size * grid_size
        != number_of_patches
    ):
        raise ValueError(
            f"Patch count {number_of_patches} "
            f"is not square."
        )

    anomaly_map = distances.reshape(
        grid_size,
        grid_size,
    ).numpy()

    # --------------------------------------------------------
    # Image anomaly score = maximum patch score
    # --------------------------------------------------------

    anomaly_score = float(
        anomaly_map.max()
    )

    max_index = int(
        np.argmax(anomaly_map)
    )

    max_row = max_index // grid_size
    max_col = max_index % grid_size

    return (
        anomaly_map,
        anomaly_score,
        (max_row, max_col),
    )


# ============================================================
# Resize anomaly map
# ============================================================

def resize_anomaly_map(
    anomaly_map: np.ndarray,
    target_width: int,
    target_height: int,
) -> np.ndarray:

    tensor = torch.from_numpy(
        anomaly_map
    ).float()

    tensor = tensor.unsqueeze(0).unsqueeze(0)

    resized = F.interpolate(
        tensor,
        size=(
            target_height,
            target_width,
        ),
        mode="bilinear",
        align_corners=False,
    )

    return (
        resized.squeeze()
        .numpy()
    )


# ============================================================
# Normalize anomaly map
# ============================================================

def normalize_map(
    anomaly_map: np.ndarray,
) -> np.ndarray:

    minimum = anomaly_map.min()
    maximum = anomaly_map.max()

    if maximum <= minimum:
        return np.zeros_like(
            anomaly_map,
            dtype=np.float32,
        )

    return (
        (anomaly_map - minimum)
        / (maximum - minimum)
    )


# ============================================================
# Pixel AUROC
# ============================================================

def calculate_pixel_auroc(
    anomaly_map: np.ndarray,
    mask: np.ndarray,
) -> float:

    scores = anomaly_map.reshape(-1)
    targets = (
        mask.astype(np.uint8)
        .reshape(-1)
    )

    # AUROC is undefined when a mask contains only
    # one class. For anomalous samples, a valid mask
    # should contain foreground pixels.
    if (
        targets.min()
        == targets.max()
    ):
        return float("nan")

    return float(
        roc_auc_score(
            targets,
            scores,
        )
    )


# ============================================================
# Region overlap at threshold
# ============================================================

def calculate_region_overlap(
    anomaly_map: np.ndarray,
    mask: np.ndarray,
    threshold: float,
) -> float:

    prediction = (
        anomaly_map >= threshold
    )

    ground_truth = (
        mask > 0
    )

    intersection = np.logical_and(
        prediction,
        ground_truth,
    ).sum()

    union = np.logical_or(
        prediction,
        ground_truth,
    ).sum()

    if union == 0:
        return 0.0

    return float(
        intersection / union
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate DINOv3 anomaly localization "
            "against MVTec LOCO AD ground-truth masks."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help=(
            "Root MVTec LOCO AD dataset directory."
        ),
    )

    parser.add_argument(
        "--features",
        type=Path,
        required=True,
        help=(
            "Root directory containing DINOv3 "
            "features."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/localization"
        ),
    )

    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help=(
            "Optional category. If omitted, "
            "all five categories are evaluated."
        ),
    )

    args = parser.parse_args()

    dataset_root = args.dataset
    feature_root = args.features
    output_dir = args.output_dir

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Select categories
    # --------------------------------------------------------

    if args.category is None:

        categories = CATEGORIES

    else:

        if args.category not in CATEGORIES:
            raise ValueError(
                f"Unknown category: "
                f"{args.category}"
            )

        categories = [
            args.category
        ]

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 100)
    print("DINOv3 LOCALIZATION EVALUATION")
    print("=" * 100)
    print(f"Device: {device}")

    # --------------------------------------------------------
    # Load DINOv3 once
    # --------------------------------------------------------

    encoder = DINOv3Encoder()

    all_results = []

    # ========================================================
    # Category loop
    # ========================================================

    for category in categories:

        print("\n")
        print("=" * 100)
        print(f"CATEGORY: {category}")
        print("=" * 100)

        category_dir = (
            dataset_root
            / category
        )

        normal_features = (
            feature_root
            / category
            / "train"
            / "good"
        )

        if not category_dir.exists():
            print(
                f"Skipping missing category:\n"
                f"{category_dir}"
            )
            continue

        if not normal_features.exists():
            print(
                f"Skipping because feature directory "
                f"is missing:\n"
                f"{normal_features}"
            )
            continue

        # ----------------------------------------------------
        # Load normal memory
        # ----------------------------------------------------

        memory_bank = load_memory_bank(
            normal_features
        )

        memory_bank = memory_bank.to(
            device
        )

        # ----------------------------------------------------
        # Evaluate logical + structural anomalies
        # ----------------------------------------------------

        test_groups = [
            "logical_anomalies",
            "structural_anomalies",
        ]

        for anomaly_type in test_groups:

            test_dir = (
                category_dir
                / "test"
                / anomaly_type
            )

            if not test_dir.exists():
                print(
                    f"Missing test directory: "
                    f"{test_dir}"
                )
                continue

            images = find_images(
                test_dir
            )

            print(
                f"\n{anomaly_type}: "
                f"{len(images)} images"
            )

            for index, image_path in enumerate(
                images,
                start=1,
            ):

                print(
                    f"\r[{index}/{len(images)}] "
                    f"{image_path.name}",
                    end="",
                )

                # ------------------------------------------------
                # Generate DINOv3 patch anomaly map
                # ------------------------------------------------

                (
                    patch_map,
                    image_score,
                    max_patch,
                ) = generate_anomaly_map(
                    encoder=encoder,
                    image_path=image_path,
                    memory_bank=memory_bank,
                    device=device,
                )

                # ------------------------------------------------
                # Load original image dimensions
                # ------------------------------------------------

                with Image.open(
                    image_path
                ) as image:

                    image_width, image_height = (
                        image.size
                    )

                # ------------------------------------------------
                # Resize 14x14 anomaly map
                # ------------------------------------------------

                pixel_map = (
                    resize_anomaly_map(
                        patch_map,
                        target_width=image_width,
                        target_height=image_height,
                    )
                )

                pixel_map = normalize_map(
                    pixel_map
                )

                # ------------------------------------------------
                # Locate ground-truth mask
                # ------------------------------------------------

                mask_path = find_mask(
                    dataset_category_dir=category_dir,
                    anomaly_type=anomaly_type,
                    image_path=image_path,
                )

                if mask_path is None:

                    print(
                        f"\nWARNING: "
                        f"No mask found for "
                        f"{image_path}"
                    )

                    continue

                # ------------------------------------------------
                # Load mask
                # ------------------------------------------------

                with Image.open(
                    mask_path
                ) as mask_image:

                    mask_image = mask_image.convert(
                        "L"
                    )

                    mask_image = mask_image.resize(
                        (
                            image_width,
                            image_height,
                        ),
                        Image.Resampling.NEAREST,
                    )

                    mask = np.array(
                        mask_image
                    )

                mask_binary = (
                    mask > 0
                )

                # ------------------------------------------------
                # Pixel AUROC
                # ------------------------------------------------

                pixel_auroc = (
                    calculate_pixel_auroc(
                        pixel_map,
                        mask_binary,
                    )
                )

                # ------------------------------------------------
                # Region overlap at several thresholds
                # ------------------------------------------------

                overlaps = {}

                for threshold in [
                    0.25,
                    0.50,
                    0.75,
                ]:

                    overlaps[
                        f"overlap_{threshold:.2f}"
                    ] = calculate_region_overlap(
                        pixel_map,
                        mask_binary,
                        threshold,
                    )

                all_results.append(
                    {
                        "category": category,
                        "anomaly_type": anomaly_type,
                        "image_path": str(
                            image_path
                        ),
                        "mask_path": str(
                            mask_path
                        ),
                        "image_anomaly_score": image_score,
                        "max_patch_row": max_patch[0],
                        "max_patch_col": max_patch[1],
                        "pixel_auroc": pixel_auroc,
                        **overlaps,
                    }
                )

            print()

        del memory_bank

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ========================================================
    # Summary
    # ========================================================

    if not all_results:
        raise RuntimeError(
            "No localization results were produced."
        )

    valid_aurocs = np.array(
        [
            item["pixel_auroc"]
            for item in all_results
            if not np.isnan(
                item["pixel_auroc"]
            )
        ],
        dtype=np.float64,
    )

    threshold_metrics = {}

    for threshold in [
        0.25,
        0.50,
        0.75,
    ]:

        key = (
            f"overlap_{threshold:.2f}"
        )

        values = np.array(
            [
                item[key]
                for item in all_results
            ],
            dtype=np.float64,
        )

        threshold_metrics[key] = {
            "mean": float(values.mean()),
            "median": float(
                np.median(values)
            ),
        }

    summary = {
        "num_anomalous_images": len(
            all_results
        ),
        "mean_pixel_auroc": float(
            valid_aurocs.mean()
        )
        if len(valid_aurocs)
        else None,
        "median_pixel_auroc": float(
            np.median(valid_aurocs)
        )
        if len(valid_aurocs)
        else None,
        "region_overlap": threshold_metrics,
    }

    # --------------------------------------------------------
    # Per-category summary
    # --------------------------------------------------------

    for category in categories:

        category_results = [
            item
            for item in all_results
            if item["category"]
            == category
        ]

        if not category_results:
            continue

        category_aurocs = np.array(
            [
                item["pixel_auroc"]
                for item in category_results
                if not np.isnan(
                    item["pixel_auroc"]
                )
            ],
            dtype=np.float64,
        )

        summary[
            category
        ] = {
            "num_images": len(
                category_results
            ),
            "mean_pixel_auroc": (
                float(
                    category_aurocs.mean()
                )
                if len(category_aurocs)
                else None
            ),
            "median_pixel_auroc": (
                float(
                    np.median(
                        category_aurocs
                    )
                )
                if len(category_aurocs)
                else None
            ),
        }

    # ========================================================
    # Save CSV
    # ========================================================

    csv_path = (
        output_dir
        / "localization_results.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        fieldnames = [
            "category",
            "anomaly_type",
            "image_path",
            "mask_path",
            "image_anomaly_score",
            "max_patch_row",
            "max_patch_col",
            "pixel_auroc",
            "overlap_0.25",
            "overlap_0.50",
            "overlap_0.75",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            all_results
        )

    # ========================================================
    # Save JSON
    # ========================================================

    json_path = (
        output_dir
        / "localization_summary.json"
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

    # ========================================================
    # Print final result
    # ========================================================

    print("\n")
    print("=" * 100)
    print("LOCALIZATION EVALUATION")
    print("=" * 100)

    print(
        f"Anomalous images evaluated: "
        f"{summary['num_anomalous_images']}"
    )

    print(
        f"Mean pixel AUROC: "
        f"{summary['mean_pixel_auroc']:.4f}"
    )

    print(
        f"Median pixel AUROC: "
        f"{summary['median_pixel_auroc']:.4f}"
    )

    print("\nRegion overlap:")

    for key, value in threshold_metrics.items():

        print(
            f"{key}: "
            f"mean={value['mean']:.4f}, "
            f"median={value['median']:.4f}"
        )

    print("\nPer category:")

    for category in categories:

        if category not in summary:
            continue

        row = summary[category]

        print(
            f"{category:<25}"
            f"AUROC={row['mean_pixel_auroc']:.4f}"
        )

    print("\nSaved:")
    print(
        f"CSV:  {csv_path}"
    )

    print(
        f"JSON: {json_path}"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()