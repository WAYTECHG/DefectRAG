from __future__ import annotations

import threading
import time
import uuid
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.config import (
    CLOUD_MEMORY_DIR,
    FEATURES_DIR,
    HEAD_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    REFERENCE_DIR,
    RESULTS_DIR,
    OLLAMA_VISION_TIMEOUT_SECONDS,
)
from app.rag_service import generate_inspection_explanation
from rag.anomaly_crop import anomaly_map_to_bounding_box, create_location_visualization, create_multiscale_crops
from knowledge.policy import evidence_status

CATEGORIES = (
    "breakfast_box",
    "juice_bottle",
    "pushpins",
    "screw_bag",
    "splicing_connectors",
)

# Youden-J operating points calculated from results/all_categories/
# all_categories_scores.csv. They are benchmark decision thresholds, not
# probabilities or universal production acceptance limits.
CATEGORY_THRESHOLDS = {
    "breakfast_box": 0.088548,
    "juice_bottle": 0.029323,
    "pushpins": 0.034935,
    "screw_bag": 0.072252,
    "splicing_connectors": 0.051088,
}

_encoder: Any = None
_scorers: dict[str, Any] = {}
_model_lock = threading.Lock()
_inspection_lock = threading.Lock()
logger = logging.getLogger("defectrag.inspection")


def _build_grounded_query(
    category: str,
    anomaly_score: float,
    patch_row: int,
    patch_col: int,
    visual_reasoning: dict[str, Any],
) -> str:
    evidence = "\n".join(f"- {item}" for item in visual_reasoning.get("evidence", []))
    return f"""Industrial visual inspection for {category}.
Anomaly score: {anomaly_score:.6f}
Strongest patch: row={patch_row}, column={patch_col}
Visual observation: {visual_reasoning.get('visual_observation', 'unknown')}
Local observation: {visual_reasoning.get('local_observation', 'unknown')}
Suspected issue: {visual_reasoning.get('suspected_issue', 'unknown')}
Proposed anomaly type: {visual_reasoning.get('possible_anomaly_type', 'unknown')}
Observed evidence:
{evidence or '- unknown'}

Retrieve category-specific evidence about expected configuration, component presence, quantity, placement, structural defects, logical constraints, and inspection criteria. The visual hypothesis must be supported or contradicted by retrieved evidence."""


def available_categories() -> list[dict[str, Any]]:
    categories = []
    for category in CATEGORIES:
        compact = (CLOUD_MEMORY_DIR / f"{category}.pt").is_file()
        legacy = any((FEATURES_DIR / category / "train" / "good").glob("*.pt"))
        head = _head_path(category) if compact else None
        categories.append({
            "id": category,
            "label": category.replace("_", " ").title(),
            "ready": compact or legacy,
            "methods": ["baseline", "trained", "fusion"] if head else ["baseline"],
            "threshold": CATEGORY_THRESHOLDS[category],
            "reference_ready": any((REFERENCE_DIR / category).glob("*")),
        })
    return categories


def _head_path(category: str) -> Path | None:
    for candidate in (CLOUD_MEMORY_DIR / f"{category}_head.pt", HEAD_DIR / f"{category}_head.pt"):
        if candidate.is_file():
            return candidate
    return None


def _get_scorer(category: str):
    global _encoder
    if category not in CATEGORIES:
        raise ValueError(f"Unsupported category: {category}")
    memory_path = CLOUD_MEMORY_DIR / f"{category}.pt"
    feature_dir = FEATURES_DIR / category / "train" / "good"
    if not memory_path.is_file() and not any(feature_dir.glob("*.pt")):
        raise FileNotFoundError(
            f"No normal memory is available for {category}. Expected {memory_path} or features under {feature_dir}."
        )
    with _model_lock:
        if _encoder is None:
            from vision.dinov3_encoder import DINOv3Encoder
            _encoder = DINOv3Encoder()
        if category not in _scorers:
            if memory_path.is_file():
                from vision.compact_scorer import CompactDINOv3Scorer
                _scorers[category] = CompactDINOv3Scorer(category, _encoder, memory_path, _head_path(category))
            else:
                from vision.anomaly_scorer import DINOv3AnomalyScorer
                _scorers[category] = DINOv3AnomalyScorer(
                    feature_dir=feature_dir,
                    encoder=_encoder,
                    max_memory_patches=50000,
                )
    return _scorers[category]


def _save_heatmap(image_path: Path, anomaly_map: np.ndarray, output_path: Path) -> None:
    original = Image.open(image_path).convert("RGBA")
    normalized = np.clip(anomaly_map.astype(np.float32), 0.0, 1.0)
    map_image = Image.fromarray((normalized * 255).astype(np.uint8)).resize(
        original.size, Image.Resampling.BILINEAR
    )
    values = np.asarray(map_image, dtype=np.float32) / 255.0
    overlay = np.zeros((original.height, original.width, 4), dtype=np.uint8)
    overlay[..., 0] = 255
    overlay[..., 1] = (180 * (1.0 - values)).astype(np.uint8)
    overlay[..., 3] = (190 * values).astype(np.uint8)
    composed = Image.alpha_composite(original, Image.fromarray(overlay, "RGBA"))
    composed.convert("RGB").save(output_path, quality=94)


def inspect_image(image_path: Path, category: str, retriever: Any, method: str = "baseline") -> dict[str, Any]:
    with _inspection_lock:
        started = time.perf_counter()
        logger.info("Inspection started: category=%s method=%s", category, method)
        scorer = _get_scorer(category)
        supported = getattr(scorer, "available_methods", ("baseline",))
        if method not in supported:
            raise ValueError(f"The {method} method needs a compact bank and trained head for {category}.")
        job_id = uuid.uuid4().hex
        output_dir = RESULTS_DIR / job_id
        crop_dir = output_dir / "crops"
        output_dir.mkdir(parents=True, exist_ok=True)

        visual_result = scorer.score_image(image_path, method=method) if hasattr(scorer, "available_methods") else scorer.score_image(image_path)
        anomaly_score = float(visual_result["anomaly_score"])
        patch_row, patch_col = map(int, visual_result["max_patch"])
        threshold = CATEGORY_THRESHOLDS[category] if method == "baseline" else None
        verdict = ("anomaly detected" if anomaly_score >= threshold else "no anomaly detected") if threshold is not None else "research score — no calibrated verdict"
        logger.info("DINOv3 scoring complete in %.1fs: category=%s method=%s", time.perf_counter() - started, category, method)

        image_size = Image.open(image_path).size
        bounding_box = anomaly_map_to_bounding_box(visual_result["anomaly_map"], image_size)

        location_path = output_dir / "location.jpg"
        heatmap_path = output_dir / "heatmap.jpg"
        create_location_visualization(
            image_path=image_path,
            patch_row=patch_row,
            patch_col=patch_col,
            grid_size=14,
            bounding_box=bounding_box,
            label="ANOMALOUS REGION" if threshold is not None and anomaly_score >= threshold else "HIGHEST RESPONSE",
            output_path=location_path,
        )
        crops = create_multiscale_crops(
            image_path=image_path,
            patch_row=patch_row,
            patch_col=patch_col,
            grid_size=14,
            output_dir=crop_dir,
        )
        _save_heatmap(image_path, visual_result["anomaly_map"], heatmap_path)
        detection_seconds = time.perf_counter() - started

        from rag.visual_reasoner import VisualReasoner
        try:
            visual_reasoning = VisualReasoner(
                model=OLLAMA_VISION_MODEL,
                host=OLLAMA_BASE_URL,
                timeout=OLLAMA_VISION_TIMEOUT_SECONDS,
            ).analyze(
                full_image=image_path,
                small_crop=crops["crops"]["small"],
                medium_crop=crops["crops"]["medium"],
                large_crop=crops["crops"]["large"],
                category=category,
                anomaly_score=anomaly_score,
                patch_row=patch_row,
                patch_col=patch_col,
            )
        except Exception as exc:
            logger.exception("Ollama visual reasoning failed after %.1fs", time.perf_counter() - started)
            if "timeout" in type(exc).__name__.lower():
                raise RuntimeError(f"Visual reasoning exceeded {OLLAMA_VISION_TIMEOUT_SECONDS}s. Check Ollama logs or try a smaller image.") from exc
            raise RuntimeError(f"Visual reasoning failed in Ollama ({type(exc).__name__}). Check the Ollama logs; no model download is needed unless the model is missing.") from exc
        vision_seconds = time.perf_counter() - started - detection_seconds
        logger.info("Ollama observation complete in %.1fs: category=%s", vision_seconds, category)

        query = _build_grounded_query(
            category=category,
            anomaly_score=anomaly_score,
            patch_row=patch_row,
            patch_col=patch_col,
            visual_reasoning=visual_reasoning,
        )
        logger.info("Retrieving category evidence: category=%s", category)
        evidence = (retriever() if callable(retriever) else retriever).search(query, k=4, candidate_k=10, category=category)
        status = evidence_status(evidence, category)
        explanation = generate_inspection_explanation(
            category=category,
            verdict=verdict,
            anomaly_score=anomaly_score,
            threshold=threshold,
            patch_row=patch_row,
            patch_col=patch_col,
            visual_reasoning=visual_reasoning,
            evidence=evidence,
            scoring_method=method,
        ) if status["product_rules_available"] else (
            f"Visual observation: {visual_reasoning.get('visual_observation', 'Unknown')}. "
            + status["message"] + " The highlighted region needs human review."
        )

        reference_candidates = sorted(
            path for path in (REFERENCE_DIR / category).glob("*")
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        reference_url = f"/references/{category}/{reference_candidates[0].name}" if reference_candidates else None
        reasoning_seconds = time.perf_counter() - started - detection_seconds - vision_seconds
        logger.info("Inspection complete in %.1fs (retrieval/report %.1fs): category=%s method=%s", time.perf_counter() - started, reasoning_seconds, category, method)

        return {
            "job_id": job_id,
            "category": category,
            "verdict": verdict,
            "anomaly_score": anomaly_score,
            "threshold": threshold,
            "scoring_method": method,
            "comparison_scores": visual_result.get("comparison_scores", {"baseline": anomaly_score}),
            "calibrated": threshold is not None,
            "independently_validated_threshold": False,
            "timing_seconds": {
                "detection_and_localization": round(detection_seconds, 2),
                "visual_observation": round(vision_seconds, 2),
                "retrieval_and_report": round(reasoning_seconds, 2),
                "total": round(time.perf_counter() - started, 2),
            },
            "max_patch": {"row": patch_row, "column": patch_col, "grid_size": 14},
            "bounding_box": bounding_box,
            "visual_reasoning": visual_reasoning,
            "evidence_status": status,
            "explanation": explanation,
            "reference_example": {
                "url": reference_url,
                "label": "Dataset-verified normal reference",
                "available": bool(reference_url),
                "disclaimer": "This is a known-normal comparison image, not ground truth for the uploaded image.",
            },
            "reasoning_assurance": {
                "detector_claim": f"The bounding box marks connected high-response patches under the {method} score; it is an estimate, not a verified defect boundary.",
                "visual_claim": "The visual description reports observable appearance; proposed causes remain hypotheses.",
                "evidence_claim": "Product rules are stated only when supported by the numbered retrieved sources.",
            },
            "artifacts": {
                "location": f"/artifacts/{job_id}/location.jpg",
                "heatmap": f"/artifacts/{job_id}/heatmap.jpg",
                "small_crop": f"/artifacts/{job_id}/crops/{image_path.stem}_small.png",
                "medium_crop": f"/artifacts/{job_id}/crops/{image_path.stem}_medium.png",
                "large_crop": f"/artifacts/{job_id}/crops/{image_path.stem}_large.png",
            },
            "sources": [
                {
                    "rank": index,
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "source": doc.get("source"),
                    "source_url": doc.get("source_url"),
                    "text": doc.get("text"),
                    "score": doc.get("rrf_score"),
                }
                for index, doc in enumerate(evidence, 1)
            ],
        }
