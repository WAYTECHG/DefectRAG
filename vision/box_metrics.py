"""Geometry for a single proposal against the enclosing ground-truth mask box."""

from __future__ import annotations

import numpy as np


def mask_box(mask: np.ndarray) -> dict[str, int] | None:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return None
    return {"x_min": int(xs.min()), "y_min": int(ys.min()),
            "x_max": int(xs.max()) + 1, "y_max": int(ys.max()) + 1}


def box_iou(a: dict[str, int], b: dict[str, int]) -> float:
    width = max(0, min(a["x_max"], b["x_max"]) - max(a["x_min"], b["x_min"]))
    height = max(0, min(a["y_max"], b["y_max"]) - max(a["y_min"], b["y_min"]))
    overlap = width * height
    area_a = max(0, a["x_max"] - a["x_min"]) * max(0, a["y_max"] - a["y_min"])
    area_b = max(0, b["x_max"] - b["x_min"]) * max(0, b["y_max"] - b["y_min"])
    union = area_a + area_b - overlap
    return overlap / union if union else 0.0
