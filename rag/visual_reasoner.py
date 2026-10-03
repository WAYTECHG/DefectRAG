from __future__ import annotations

import json
import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ollama
from PIL import Image


class VisualReasoner:

    def __init__(
        self,
        model: str = "qwen2.5vl:3b",
        host: str | None = None,
        timeout: int = 120,
    ) -> None:

        self.model = model
        self.client = ollama.Client(host=host, timeout=timeout)

    @staticmethod
    def _model_image(path: str | Path, longest_side: int) -> bytes:
        """Limit visual tokens and image transfer without changing stored inspection images."""
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((longest_side, longest_side), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=82)
            return buffer.getvalue()

    def analyze(
        self,
        full_image: str | Path,
        small_crop: str | Path,
        medium_crop: str | Path,
        large_crop: str | Path,
        category: str,
        anomaly_score: float,
        patch_row: int,
        patch_col: int,
    ) -> dict:

        # The local fast path uses the full view and one focused crop. The
        # other generated crops remain available as inspection artifacts.
        full_view = self._model_image(full_image, 768)
        focused_view = self._model_image(medium_crop, 512)

        prompt = f"""
You are an industrial visual-inspection assistant.

Product category:
{category}

A frozen DINOv3 anomaly detector has identified a region
that differs from the learned normal-product memory.

Detector information:
- anomaly score: {anomaly_score:.6f}
- strongest anomaly patch: row={patch_row}, column={patch_col}
- spatial grid: 14 x 14

You are given two images:

IMAGE 1:
The complete product.

IMAGE 2:
A focused crop around the strongest deviation.

IMPORTANT:
The crop was selected by an anomaly detector.
Do not assume that the anomaly detector is correct.
Instead, inspect the images carefully and determine whether
you can identify a visible difference.

Your task is NOT to make the final defect diagnosis.

You must:

1. Describe only what is visually observable.
2. Compare the suspicious area with nearby product regions.
3. Determine whether there is evidence of:
   - missing component
   - misplaced component
   - abnormal component arrangement
   - unusual object presence
   - structural surface defect
   - no clearly visible defect
4. Distinguish observation from interpretation.
5. Explicitly state uncertainty.
6. Do not invent product specifications or manufacturing rules.

If the evidence is insufficient, use "unknown".

Return ONLY valid JSON:

{{
  "visual_observation": "...",
  "local_observation": "...",
  "suspected_issue": "...",
  "possible_anomaly_type": "logical | structural | unknown",
  "confidence": 0.0,
  "evidence": [
    "...",
    "..."
  ],
  "uncertainty": "..."
}}

Confidence must be between 0 and 1.
"""

        response = self.client.chat(
            model=self.model,
            format="json",
            options={"num_ctx": 4096, "num_predict": 320, "temperature": 0.1},
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [full_view, focused_view],
                }
            ],
        )

        text = response[
            "message"
        ][
            "content"
        ].strip()

        return self._parse_json(
            text
        )

    @staticmethod
    def _parse_json(
        text: str,
    ) -> dict:

        # Remove markdown code fences.
        if text.startswith("```"):

            lines = text.splitlines()

            lines = [
                line
                for line in lines
                if not line.strip().startswith(
                    "```"
                )
            ]

            text = "\n".join(
                lines
            ).strip()

        try:

            return json.loads(
                text
            )

        except json.JSONDecodeError:

            return {
                "visual_observation": text,
                "local_observation": "unknown",
                "suspected_issue": "unknown",
                "possible_anomaly_type": "unknown",
                "confidence": 0.0,
                "evidence": [],
                "uncertainty": (
                    "VLM returned invalid JSON."
                ),
                "raw_response": text,
            }


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
    )

    parser.add_argument(
        "--small",
        required=True,
    )

    parser.add_argument(
        "--medium",
        required=True,
    )

    parser.add_argument(
        "--large",
        required=True,
    )

    parser.add_argument(
        "--category",
        required=True,
    )

    parser.add_argument(
        "--score",
        type=float,
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

    args = parser.parse_args()

    reasoner = VisualReasoner()

    result = reasoner.analyze(
        full_image=args.image,
        small_crop=args.small,
        medium_crop=args.medium,
        large_crop=args.large,
        category=args.category,
        anomaly_score=args.score,
        patch_row=args.row,
        patch_col=args.col,
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        )
    )
