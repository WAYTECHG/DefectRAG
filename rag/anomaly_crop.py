from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw


def anomaly_map_to_bounding_box(
    anomaly_map,
    image_size: tuple[int, int],
    *,
    expansion_cells: int = 1,
) -> dict:
    """Convert the connected high-response region around the peak into a box."""
    import numpy as np

    values = np.asarray(anomaly_map, dtype=np.float32)
    if values.ndim != 2 or not values.size:
        raise ValueError("anomaly_map must be a non-empty 2D array")

    rows, columns = values.shape
    peak_row, peak_column = np.unravel_index(int(np.argmax(values)), values.shape)
    cutoff = max(float(np.quantile(values, 0.82)), float(values[peak_row, peak_column]) * 0.62)
    eligible = values >= cutoff

    connected = {(int(peak_row), int(peak_column))}
    frontier = [(int(peak_row), int(peak_column))]
    while frontier:
        row, column = frontier.pop()
        for next_row, next_column in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
            point = (next_row, next_column)
            if (
                0 <= next_row < rows
                and 0 <= next_column < columns
                and eligible[next_row, next_column]
                and point not in connected
            ):
                connected.add(point)
                frontier.append(point)

    min_row = max(0, min(point[0] for point in connected) - expansion_cells)
    max_row = min(rows - 1, max(point[0] for point in connected) + expansion_cells)
    min_column = max(0, min(point[1] for point in connected) - expansion_cells)
    max_column = min(columns - 1, max(point[1] for point in connected) + expansion_cells)
    width, height = image_size
    x_min = int(round(min_column * width / columns))
    y_min = int(round(min_row * height / rows))
    x_max = int(round((max_column + 1) * width / columns))
    y_max = int(round((max_row + 1) * height / rows))
    return {
        "pixel": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
        "normalized": {
            "x_min": round(x_min / width, 6),
            "y_min": round(y_min / height, 6),
            "x_max": round(x_max / width, 6),
            "y_max": round(y_max / height, 6),
        },
        "peak_patch": {"row": int(peak_row), "column": int(peak_column)},
        "method": "connected high-response DINOv3 patches around the maximum",
    }


def patch_center_to_pixel(
    image_size: tuple[int, int],
    patch_row: int,
    patch_col: int,
    grid_size: int = 14,
) -> tuple[float, float]:
    """
    Approximate the center of a DINOv3 patch in original-image
    coordinates.

    Current DINOv3 setup uses a 14x14 spatial patch grid.
    """

    width, height = image_size

    patch_width = width / grid_size
    patch_height = height / grid_size

    center_x = (patch_col + 0.5) * patch_width
    center_y = (patch_row + 0.5) * patch_height

    return center_x, center_y


def crop_around_center(
    image: Image.Image,
    center_x: float,
    center_y: float,
    crop_width: float,
    crop_height: float,
) -> Image.Image:
    """
    Crop around a center point while clamping to image boundaries.
    """

    image_width, image_height = image.size

    left = int(center_x - crop_width / 2)
    top = int(center_y - crop_height / 2)
    right = int(center_x + crop_width / 2)
    bottom = int(center_y + crop_height / 2)

    left = max(0, left)
    top = max(0, top)
    right = min(image_width, right)
    bottom = min(image_height, bottom)

    return image.crop(
        (left, top, right, bottom)
    )


def create_multiscale_crops(
    image_path: str | Path,
    patch_row: int,
    patch_col: int,
    grid_size: int = 14,
    output_dir: str | Path | None = None,
) -> dict:
    """
    Generate three crops around the strongest anomaly:

        small  = tightly focused
        medium = local context
        large  = wider product context
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image does not exist:\n{image_path}"
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    width, height = image.size

    center_x, center_y = patch_center_to_pixel(
        image_size=image.size,
        patch_row=patch_row,
        patch_col=patch_col,
        grid_size=grid_size,
    )

    # --------------------------------------------------------
    # Crop sizes relative to the complete image
    # --------------------------------------------------------

    crop_definitions = {
        "small": (
            width * 0.18,
            height * 0.18,
        ),
        "medium": (
            width * 0.32,
            height * 0.32,
        ),
        "large": (
            width * 0.50,
            height * 0.50,
        ),
    }

    if output_dir is None:
        output_dir = (
            PROJECT_ROOT
            / "results"
            / "visual_rag"
            / "crops"
        )

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved = {}

    for name, (
        crop_width,
        crop_height,
    ) in crop_definitions.items():

        crop = crop_around_center(
            image=image,
            center_x=center_x,
            center_y=center_y,
            crop_width=crop_width,
            crop_height=crop_height,
        )

        output_path = (
            output_dir
            / f"{image_path.stem}_{name}.png"
        )

        crop.save(
            output_path
        )

        saved[name] = str(
            output_path
        )

    return {
        "image_path": str(image_path),
        "image_size": [
            width,
            height,
        ],
        "patch": {
            "row": patch_row,
            "column": patch_col,
            "grid_size": grid_size,
        },
        "center_pixel": [
            center_x,
            center_y,
        ],
        "crops": saved,
    }


def create_location_visualization(
    image_path: str | Path,
    patch_row: int,
    patch_col: int,
    grid_size: int = 14,
    bounding_box: dict | None = None,
    label: str = "SUSPECTED ANOMALY",
    output_path: str | Path | None = None,
) -> Path:
    """
    Draw the estimated anomaly location and the small/medium/large
    crop regions on the full image.
    """

    image_path = Path(image_path)

    image = Image.open(
        image_path
    ).convert("RGB")

    width, height = image.size

    center_x, center_y = patch_center_to_pixel(
        image_size=image.size,
        patch_row=patch_row,
        patch_col=patch_col,
        grid_size=grid_size,
    )

    visualization = image.copy()

    draw = ImageDraw.Draw(
        visualization
    )

    if bounding_box and isinstance(bounding_box.get("pixel"), dict):
        pixel = bounding_box["pixel"]
        left, top, right, bottom = (pixel["x_min"], pixel["y_min"], pixel["x_max"], pixel["y_max"])
    else:
        patch_width, patch_height = width / grid_size, height / grid_size
        left = max(0, int(center_x - patch_width * 1.5))
        top = max(0, int(center_y - patch_height * 1.5))
        right = min(width, int(center_x + patch_width * 1.5))
        bottom = min(height, int(center_y + patch_height * 1.5))

    stroke = max(3, round(min(width, height) * 0.008))
    overlay = Image.new("RGBA", visualization.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((left, top, right, bottom), fill=(229, 77, 63, 35), outline=(255, 92, 76, 255), width=stroke)
    label_box = overlay_draw.textbbox((0, 0), label)
    label_width = label_box[2] - label_box[0] + 18
    label_height = label_box[3] - label_box[1] + 12
    label_top = max(0, top - label_height)
    overlay_draw.rectangle((left, label_top, min(width, left + label_width), label_top + label_height), fill=(214, 60, 49, 240))
    overlay_draw.text((left + 9, label_top + 5), label, fill=(255, 255, 255, 255))
    visualization = Image.alpha_composite(visualization.convert("RGBA"), overlay).convert("RGB")

    if output_path is None:
        output_path = (
            PROJECT_ROOT
            / "results"
            / "visual_rag"
            / "anomaly_location_multiscale.png"
        )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    visualization.save(
        output_path
    )

    return output_path


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
    )

    parser.add_argument(
        "--row",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--col",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        default=(
            "results/visual_rag/crops"
        ),
    )

    args = parser.parse_args()

    result = create_multiscale_crops(
        image_path=args.image,
        patch_row=args.row,
        patch_col=args.col,
        output_dir=args.output_dir,
    )

    print(
        "\nGenerated crops:"
    )

    for name, path in result[
        "crops"
    ].items():

        print(
            f"{name}: {path}"
        )
