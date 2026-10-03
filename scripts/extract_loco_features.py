from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from pathlib import Path

import torch
from PIL import Image
from tqdm import tqdm

from vision.dinov3_encoder import DINOv3Encoder


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def find_images(root: Path) -> list[Path]:
    """
    Recursively find supported images.
    """
    images = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    return sorted(images)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Root directory containing LOCO AD images.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("features"),
        help="Directory where feature files will be stored.",
    )

    parser.add_argument(
        "--normal-only",
        action="store_true",
        help="Extract only category/train/good images required by the web inspector.",
    )

    args = parser.parse_args()

    dataset_root = args.dataset
    output_root = args.output

    if not dataset_root.exists():
        raise FileNotFoundError(
            f"Dataset directory does not exist: {dataset_root}"
        )

    if args.normal_only:
        images = []
        for category_dir in sorted(path for path in dataset_root.iterdir() if path.is_dir()):
            normal_dir = category_dir / "train" / "good"
            if normal_dir.exists():
                images.extend(find_images(normal_dir))
        images = sorted(images)
    else:
        images = find_images(dataset_root)

    if not images:
        raise RuntimeError(
            f"No images found under: {dataset_root}"
        )

    print(f"Found {len(images)} images.")

    encoder = DINOv3Encoder()

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    failed = []

    for image_path in tqdm(images, desc="Extracting DINOv3 features"):

        try:
            relative_path = image_path.relative_to(dataset_root)

            # Preserve directory structure.
            output_path = (
                output_root
                / relative_path.parent
                / f"{relative_path.stem}.pt"
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Skip existing features so the script can resume.
            if output_path.exists():
                continue

            image = Image.open(image_path).convert("RGB")

            features = encoder.encode(image)

            torch.save(
                {
                    "image_path": str(relative_path),

                    # Global representation
                    "pooled": features["pooled"],

                    # Explicit CLS representation
                    "cls": features["cls"],

                    # DINOv3 register tokens
                    "registers": features["registers"],

                    # Spatial patch features only
                    "patches": features["patches"],
                },
                output_path,
            )

        except Exception as exc:
            failed.append(
                {
                    "image": str(image_path),
                    "error": repr(exc),
                }
            )

    print("\n=== Extraction Finished ===")
    print(f"Successful/processed: {len(images) - len(failed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFirst failures:")

        for item in failed[:10]:
            print(item)


if __name__ == "__main__":
    main()
