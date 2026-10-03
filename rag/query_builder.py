from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_visual_inspection_query(
    category: str,
    anomaly_score: float,
    max_patch_row: int,
    max_patch_col: int,
) -> str:
    """
    Convert visual anomaly evidence into a retrieval query.

    Important:
    This does NOT claim a specific defect type.
    It only describes what the vision stage actually observed.
    """

    return f"""
Industrial visual inspection for product category: {category}.

A pretrained vision model detected an anomalous region.

Anomaly score: {anomaly_score:.4f}
Most anomalous patch location:
row={max_patch_row}, column={max_patch_col}

Retrieve domain knowledge relevant to:
- expected product configuration
- component presence
- component quantity
- component location
- structural defects
- logical anomalies
- inspection criteria
- possible explanations for an anomalous region

The retrieval system should provide evidence that can help
determine whether the observed anomaly is structural,
logical, or related to another product-specific constraint.
""".strip()


if __name__ == "__main__":
    query = build_visual_inspection_query(
        category="breakfast_box",
        anomaly_score=0.1410,
        max_patch_row=3,
        max_patch_col=12,
    )

    print(query)