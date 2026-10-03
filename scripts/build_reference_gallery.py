from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from scripts.extract_loco_features import IMAGE_EXTENSIONS


def main() -> None:
    parser = argparse.ArgumentParser(description="Create small, dataset-verified normal reference galleries for the UI.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("cloud/references"))
    parser.add_argument("--per-category", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.per_category <= 10:
        raise ValueError("--per-category must be between 1 and 10")

    for category_dir in sorted(path for path in args.dataset.iterdir() if path.is_dir()):
        normal_dir = category_dir / "train" / "good"
        images = sorted(path for path in normal_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        if not images:
            continue
        destination = args.output / category_dir.name
        destination.mkdir(parents=True, exist_ok=True)
        for index, source in enumerate(images[: args.per_category], 1):
            target = destination / f"normal_reference_{index:02d}.jpg"
            with Image.open(source) as image:
                prepared = image.convert("RGB")
                prepared.thumbnail((1200, 1200))
                prepared.save(target, quality=88, optimize=True)
        print(f"{category_dir.name}: {min(len(images), args.per_category)} references -> {destination}")


if __name__ == "__main__":
    main()
