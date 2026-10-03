from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from vision.dinov3_encoder import DINOv3Encoder


class DINOv3AnomalyScorer:
    """
    Patch-level anomaly detector using frozen DINOv3 features.

    Normal reference:
        DINOv3 patch features extracted from normal training images.

    Test:
        DINOv3 patch features from a test image.

    Each test patch is compared against all normal reference patches.
    The nearest normal patch determines the anomaly score.

    Higher score = more anomalous.
    """

    def __init__(
        self,
        feature_dir: str | Path,
        encoder: DINOv3Encoder,
        device: str | None = None,
        max_memory_patches: int | None = None,
    ) -> None:

        self.feature_dir = Path(feature_dir)
        self.encoder = encoder

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device)

        self.memory_bank: torch.Tensor | None = None

        self.patch_grid_size: tuple[int, int] | None = None

        self.build_memory_bank(
            max_memory_patches=max_memory_patches
        )

    # ==========================================================
    # Build normal memory bank
    # ==========================================================

    def build_memory_bank(
        self,
        max_memory_patches: int | None = None,
    ) -> None:

        feature_files = sorted(
            self.feature_dir.rglob("*.pt")
        )

        if not feature_files:
            raise FileNotFoundError(
                f"No .pt feature files found in: {self.feature_dir}"
            )

        print(
            f"Found {len(feature_files)} normal feature files."
        )

        all_patches = []

        for feature_file in feature_files:

            data = torch.load(
                feature_file,
                weights_only=True,
            )

            patches = data["patches"]

            # Expected:
            # [1, number_of_patches, feature_dim]

            if patches.ndim != 3:
                raise ValueError(
                    f"Unexpected patch shape in {feature_file}: "
                    f"{tuple(patches.shape)}"
                )

            patches = patches.squeeze(0)

            # Remember spatial grid.
            # 196 -> 14 x 14
            num_patches = patches.shape[0]

            grid_size = int(np.sqrt(num_patches))

            if grid_size * grid_size != num_patches:
                raise ValueError(
                    f"Number of patches ({num_patches}) is not "
                    f"a square number in {feature_file}."
                )

            self.patch_grid_size = (
                grid_size,
                grid_size,
            )

            all_patches.append(patches)

        memory_bank = torch.cat(
            all_patches,
            dim=0,
        )

        print(
            f"Raw memory bank shape: "
            f"{tuple(memory_bank.shape)}"
        )

        # ------------------------------------------------------
        # Optional memory-bank subsampling
        # ------------------------------------------------------

        if (
            max_memory_patches is not None
            and memory_bank.shape[0] > max_memory_patches
        ):

            generator = torch.Generator()

            generator.manual_seed(42)

            indices = torch.randperm(
                memory_bank.shape[0],
                generator=generator,
            )[:max_memory_patches]

            memory_bank = memory_bank[indices]

            print(
                f"Memory bank subsampled to: "
                f"{memory_bank.shape[0]} patches"
            )

        # ------------------------------------------------------
        # L2-normalize for cosine similarity
        # ------------------------------------------------------

        memory_bank = F.normalize(
            memory_bank.float(),
            p=2,
            dim=1,
        )

        self.memory_bank = memory_bank.to(
            self.device
        )

        print(
            f"Final memory bank: "
            f"{tuple(self.memory_bank.shape)}"
        )

        if self.patch_grid_size is not None:
            print(
                f"Patch grid: "
                f"{self.patch_grid_size[0]} x "
                f"{self.patch_grid_size[1]}"
            )

    # ==========================================================
    # Score one image
    # ==========================================================

    @torch.inference_mode()
    def score_image(
        self,
        image_path: str | Path,
        similarity_batch_size: int = 64,
    ) -> dict:

        if self.memory_bank is None:
            raise RuntimeError(
                "Memory bank has not been created."
            )

        print(
            f"\nScoring image:\n{image_path}"
        )

        features = self.encoder.encode(
            image_path
        )

        patches = features["patches"]

        # [1, N, D] -> [N, D]
        patches = patches.squeeze(0).float()

        # Normalize for cosine similarity.
        patches = F.normalize(
            patches,
            p=2,
            dim=1,
        )

        num_test_patches = patches.shape[0]

        patch_distances = []

        # ------------------------------------------------------
        # Compare test patches against the normal memory bank
        #
        # We process query patches in small batches to avoid
        # allocating a huge similarity matrix.
        # ------------------------------------------------------

        for start in range(
            0,
            num_test_patches,
            similarity_batch_size,
        ):

            end = min(
                start + similarity_batch_size,
                num_test_patches,
            )

            query_patches = patches[
                start:end
            ].to(self.device)

            # cosine similarity:
            #
            # [B, D] @ [D, M]
            #
            # -> [B, M]

            similarities = torch.matmul(
                query_patches,
                self.memory_bank.T,
            )

            # Nearest normal patch = maximum similarity.
            best_similarity = similarities.max(
                dim=1
            ).values

            # Convert similarity to distance.
            distance = 1.0 - best_similarity

            patch_distances.append(
                distance.detach().cpu()
            )

        patch_distances = torch.cat(
            patch_distances,
            dim=0,
        )

        # ------------------------------------------------------
        # Image-level anomaly score
        # ------------------------------------------------------
        #
        # Mean can be dominated by mostly-normal patches.
        # Top 10% is more sensitive to localized defects.
        # ------------------------------------------------------

        top_fraction = 0.10

        top_k = max(
            1,
            int(
                len(patch_distances)
                * top_fraction
            ),
        )

        top_distances = torch.topk(
            patch_distances,
            k=top_k,
        ).values

        anomaly_score = top_distances.mean().item()

        # ------------------------------------------------------
        # Reshape patch distances to spatial anomaly map
        # ------------------------------------------------------

        if self.patch_grid_size is None:
            raise RuntimeError(
                "Patch grid size was not determined."
            )

        height, width = self.patch_grid_size

        anomaly_map = patch_distances.reshape(
            height,
            width,
        ).numpy()

        # ------------------------------------------------------
        # Normalize anomaly map to [0, 1]
        # ------------------------------------------------------

        min_value = anomaly_map.min()
        max_value = anomaly_map.max()

        if max_value > min_value:
            normalized_map = (
                anomaly_map - min_value
            ) / (
                max_value - min_value
            )
        else:
            normalized_map = np.zeros_like(
                anomaly_map
            )

        # ------------------------------------------------------
        # Locate most anomalous patch
        # ------------------------------------------------------

        max_index = int(
            torch.argmax(
                patch_distances
            )
        )

        max_row = max_index // width
        max_col = max_index % width

        return {
            "image_path": str(image_path),
            "anomaly_score": anomaly_score,
            "patch_distances": patch_distances,
            "anomaly_map": normalized_map,
            "max_patch": (
                max_row,
                max_col,
            ),
        }


# ============================================================
# Command-line interface
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "DINOv3 patch-based anomaly scoring "
            "for MVTec LOCO AD."
        )
    )

    parser.add_argument(
        "--normal-features",
        type=str,
        required=True,
        help=(
            "Directory containing normal DINOv3 "
            "feature files."
        ),
    )

    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Test image to score.",
    )

    parser.add_argument(
        "--max-memory-patches",
        type=int,
        default=None,
        help=(
            "Optional maximum number of memory-bank patches. "
            "Useful to reduce GPU memory usage."
        ),
    )

    parser.add_argument(
        "--output",
        type=str,
        default="anomaly_result.pt",
        help="Output anomaly result file.",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Load frozen DINOv3 encoder
    # --------------------------------------------------------

    encoder = DINOv3Encoder()

    # --------------------------------------------------------
    # Build normal memory bank
    # --------------------------------------------------------

    scorer = DINOv3AnomalyScorer(
        feature_dir=args.normal_features,
        encoder=encoder,
        max_memory_patches=args.max_memory_patches,
    )

    # --------------------------------------------------------
    # Score test image
    # --------------------------------------------------------

    result = scorer.score_image(
        args.image
    )

    # --------------------------------------------------------
    # Print result
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ANOMALY RESULT")
    print("=" * 70)

    print(
        f"Image: {result['image_path']}"
    )

    print(
        f"Anomaly score: "
        f"{result['anomaly_score']:.6f}"
    )

    print(
        f"Most anomalous patch: "
        f"{result['max_patch']}"
    )

    print(
        f"Anomaly map shape: "
        f"{result['anomaly_map'].shape}"
    )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    output_path = Path(args.output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        result,
        output_path,
    )

    print(
        f"\nSaved result to: {output_path}"
    )


if __name__ == "__main__":
    main()