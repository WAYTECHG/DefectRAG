from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from vision.dinov3_encoder import DINOv3Encoder
from vision.anomaly_scorer import DINOv3AnomalyScorer

from retrieval.hybrid_retriever import HybridRetriever

from rag.anomaly_crop import create_multiscale_crops
from rag.visual_reasoner import VisualReasoner


# ============================================================
# Build grounded retrieval query
# ============================================================

def build_grounded_query(
    category: str,
    anomaly_score: float,
    patch_row: int,
    patch_col: int,
    visual_reasoning: dict,
) -> str:

    observation = visual_reasoning.get(
        "visual_observation",
        "unknown",
    )

    local_observation = visual_reasoning.get(
        "local_observation",
        "unknown",
    )

    suspected_issue = visual_reasoning.get(
        "suspected_issue",
        "unknown",
    )

    anomaly_type = visual_reasoning.get(
        "possible_anomaly_type",
        "unknown",
    )

    confidence = visual_reasoning.get(
        "confidence",
        0.0,
    )

    evidence = visual_reasoning.get(
        "evidence",
        [],
    )

    uncertainty = visual_reasoning.get(
        "uncertainty",
        "unknown",
    )

    evidence_text = "\n".join(
        f"- {item}"
        for item in evidence
    )

    return f"""
Industrial visual inspection.

Product category:
{category}

Visual anomaly detector:
- anomaly score: {anomaly_score:.6f}
- strongest anomaly patch:
  row={patch_row}, column={patch_col}

Visual observation:
{observation}

Local observation:
{local_observation}

VLM hypothesis:
{suspected_issue}

VLM proposed anomaly type:
{anomaly_type}

VLM confidence:
{confidence:.2f}

Observed evidence:
{evidence_text}

Uncertainty:
{uncertainty}

IMPORTANT:
The VLM anomaly type is only a hypothesis.
It is NOT a confirmed diagnosis.

Retrieve domain knowledge that can help determine whether
the observed anomaly is:

1. a structural defect,
2. a logical/configuration defect, or
3. another product-specific anomaly.

Prioritize evidence about:
- expected product configuration
- component presence
- component quantity
- component placement
- component relationships
- structural defects
- logical constraints
- inspection criteria
- category-specific knowledge

The retrieved evidence must be able to support
or contradict the VLM hypothesis.
""".strip()


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "DINOv3 + VLM + Hybrid RAG pipeline"
        )
    )

    parser.add_argument(
        "--category",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--image",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--features",
        type=Path,
        default=(
            PROJECT_ROOT
            / "features"
        ),
    )

    parser.add_argument(
        "--retrieval-k",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--vlm-model",
        type=str,
        default="qwen2.5vl:3b",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "results"
            / "visual_rag"
            / "result.json"
        ),
    )

    args = parser.parse_args()

    # ========================================================
    # Validate paths
    # ========================================================

    if not args.image.exists():
        raise FileNotFoundError(
            f"Image does not exist:\n{args.image}"
        )

    normal_feature_dir = (
        args.features
        / args.category
        / "train"
        / "good"
    )

    if not normal_feature_dir.exists():
        raise FileNotFoundError(
            "Normal feature directory does not exist:\n"
            f"{normal_feature_dir}"
        )

    # ========================================================
    # 1. DINOv3
    # ========================================================

    print("=" * 90)
    print("DEFECTRAG MULTIMODAL PIPELINE")
    print("=" * 90)

    print("\n[1/5] Loading DINOv3...")

    encoder = DINOv3Encoder()

    # ========================================================
    # 2. Anomaly scoring
    # ========================================================

    print(
        "\n[2/5] Running anomaly detection..."
    )

    scorer = DINOv3AnomalyScorer(
        feature_dir=normal_feature_dir,
        encoder=encoder,
    )

    visual_result = scorer.score_image(
        args.image
    )

    anomaly_score = float(
        visual_result["anomaly_score"]
    )

    patch_row, patch_col = (
        visual_result["max_patch"]
    )

    print(
        f"Anomaly score: "
        f"{anomaly_score:.6f}"
    )

    print(
        f"Most anomalous patch: "
        f"({patch_row}, {patch_col})"
    )

    # ========================================================
    # 3. Multiscale anomaly crops
    # ========================================================

    print(
        "\n[3/5] Creating multiscale anomaly crops..."
    )

    crop_dir = (
        PROJECT_ROOT
        / "results"
        / "visual_rag"
        / (
            f"{args.category}_"
            f"{args.image.stem}_crops"
        )
    )

    crop_metadata = create_multiscale_crops(
        image_path=args.image,
        patch_row=patch_row,
        patch_col=patch_col,
        grid_size=14,
        output_dir=crop_dir,
    )

    small_crop = Path(
        crop_metadata["crops"]["small"]
    )

    medium_crop = Path(
        crop_metadata["crops"]["medium"]
    )

    large_crop = Path(
        crop_metadata["crops"]["large"]
    )

    print(
        f"Small crop:  {small_crop}"
    )

    print(
        f"Medium crop: {medium_crop}"
    )

    print(
        f"Large crop:  {large_crop}"
    )

    # ========================================================
    # 4. VLM visual reasoning
    # ========================================================

    print(
        "\n[4/5] Running VLM visual reasoning..."
    )

    visual_reasoner = VisualReasoner(
        model=args.vlm_model
    )

    visual_reasoning = visual_reasoner.analyze(
        full_image=args.image,
        small_crop=small_crop,
        medium_crop=medium_crop,
        large_crop=large_crop,
        category=args.category,
        anomaly_score=anomaly_score,
        patch_row=patch_row,
        patch_col=patch_col,
    )

    print(
        "\n--- VLM VISUAL REASONING ---"
    )

    print(
        json.dumps(
            visual_reasoning,
            indent=4,
            ensure_ascii=False,
        )
    )

    # ========================================================
    # Build retrieval query
    # ========================================================

    query = build_grounded_query(
        category=args.category,
        anomaly_score=anomaly_score,
        patch_row=patch_row,
        patch_col=patch_col,
        visual_reasoning=visual_reasoning,
    )

    print(
        "\n--- GROUNDED RETRIEVAL QUERY ---"
    )

    print(query)

    # ========================================================
    # 5. Hybrid retrieval
    # ========================================================

    print(
        "\n[5/5] Running hybrid retrieval..."
    )

    retriever = HybridRetriever()

    retrieved_documents = retriever.search(
        query=query,
        k=args.retrieval_k,
        candidate_k=max(
            10,
            args.retrieval_k * 2,
        ),
    )

    print(
        "\n--- RETRIEVED EVIDENCE ---"
    )

    for rank, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        print(
            f"\nEvidence {rank}: "
            f"{document['title']}"
        )

        print(
            f"RRF score: "
            f"{document['rrf_score']:.6f}"
        )

        print(
            f"Anomaly type: "
            f"{document.get('anomaly_type', 'N/A')}"
        )

        print(
            f"\n{document['text']}"
        )

        print(
            f"\nSource: "
            f"{document.get('source_url', 'N/A')}"
        )

    # ========================================================
    # Save result
    # ========================================================

    output_data = {
        "category": args.category,
        "image": str(args.image),

        "visual_evidence": {
            "anomaly_score": anomaly_score,
            "max_patch": {
                "row": patch_row,
                "column": patch_col,
            },
            "anomaly_map_shape": list(
                visual_result[
                    "anomaly_map"
                ].shape
            ),
        },

        "anomaly_crops": crop_metadata,

        "visual_reasoning": visual_reasoning,

        "retrieval_query": query,

        "retrieved_documents": [
            {
                "rank": rank,
                "id": document["id"],
                "title": document["title"],
                "category": document.get(
                    "category"
                ),
                "anomaly_type": document.get(
                    "anomaly_type"
                ),
                "rrf_score": document[
                    "rrf_score"
                ],
                "text": document["text"],
                "source": document.get(
                    "source"
                ),
                "source_url": document.get(
                    "source_url"
                ),
            }
            for rank, document in enumerate(
                retrieved_documents,
                start=1,
            )
        ],
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        args.output,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output_data,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(
        "\n"
        + "=" * 90
    )

    print(
        "Pipeline finished successfully."
    )

    print(
        f"Saved complete result to:\n"
        f"{args.output}"
    )

    print(
        "=" * 90
    )


if __name__ == "__main__":
    main()