"""Write the model cards, the deployment manifest and the activation marker of profile "dinov2_tuned_v1" (CPU only).

    python -m scripts.activate_tuned            # after scripts.build_tuned_profile finished all 12 categories
    python -m scripts.activate_tuned --check    # verify the installed files and print the summary without writing

Thresholds use only the 90 held-out normal scores of each category: the fixed linear 95th percentile, and the 80th
percentile for macaroni1/2 (the same operating policy the application already uses; no test label or mask picks them).
Existing files are never overwritten with different content. Rollback: set DEFECTRAG_PROFILE=dinov2_highres_v1 (frozen
encoder, previous banks) or delete models/highres_tuned/PROFILE.json.
"""

import argparse
import json

import numpy as np

from backend.calibration import TUNED_DEFAULT_QUANTILE, TUNED_FILENAME, TUNED_POLICY, TUNED_QUANTILES
from backend.config import CATEGORIES, ROOT
from backend.vision import sha256
from scripts.audit_recall import quantile

EXPERIMENT = ROOT / "experiments" / "dinov2_tuned_v1"
BANKS = ROOT / "models" / "highres_tuned"
ENCODER = ROOT / "models" / "encoder_dinov2_tuned" / "model.safetensors"
PREVIOUS = ROOT / "results" / "macaroni_recall_deployment_evaluation.json"
METHOD = "AnomalyDINO-inspired DINOv2 ViT-S/14 fine-tuned on synthetic defects; 32,768-patch coreset memory"
PROTOCOL = (
    "Official VisA test assignments. The DINOv2 encoder was fine-tuned on synthetic defects made from normal training "
    "images (last 4 blocks only). The memory bank is a 32,768-patch coreset of normal-image patches per product. "
    "Thresholds are the 95th percentile of held-out normal scores (80th for Macaroni 1 and 2); held-out normals are "
    "never used to build the memory. Retrospective development evaluation on test images that were seen during "
    "development; not an untouched external test."
)


def binary(rows, threshold):
    tp = fp = tn = fn = 0
    for row in rows:
        predicted, actual = row["score"] >= threshold, row["label"] == 1
        tp += predicted and actual
        fp += predicted and not actual
        tn += not predicted and not actual
        fn += not predicted and actual
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }


def build_card(category, encoder_digest):
    directory = EXPERIMENT / category
    receipt = json.loads((directory / "complete.json").read_text(encoding="utf-8"))
    for name, digest in receipt["files"].items():
        assert sha256(directory / name) == digest, f"{category}: {name} changed since the build"
    bank = BANKS / f"{category}.npz"
    assert sha256(bank) == receipt["bank_sha256"], f"{category}: bank changed since the build"
    calibration = json.loads((directory / "normal_calibration.json").read_text(encoding="utf-8"))
    rows = json.loads((directory / "test_progress.json").read_text(encoding="utf-8"))
    measured = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    held = [p["score"] for p in calibration["predictions"]]
    fraction = TUNED_QUANTILES.get(category, TUNED_DEFAULT_QUANTILE)
    threshold = quantile(held, fraction)
    margin = threshold * 0.05
    scores = np.array([r["score"] for r in rows])
    metrics = {
        "image_auroc": measured["auroc"],
        "average_precision": measured["average_precision"],
        **binary(rows, threshold),
        "n_images": len(rows),
        "pixel_auroc_224": measured["pixel_auroc"],
        "pixel_average_precision_224": measured["pixel_average_precision"],
        "uncertain_fraction": float(np.mean(np.abs(scores - threshold) <= margin)),
        "latency_median_ms": None,
        "peak_gpu_mb": None,
    }
    return {
        "category": category,
        "available": True,
        "model_id": f"dinov2-tuned-{category}-v1",
        "method": METHOD,
        "profile": "dinov2_tuned_v1",
        "encoder_sha256": encoder_digest,
        "bank_sha256": sha256(bank),
        "threshold": threshold,
        "uncertainty_margin": margin,
        "heatmap_scale": calibration["heatmap_scale"],
        "uncertainty_policy": "Fixed ±5% of threshold; operational heuristic, not calibrated confidence",
        "bank_size_bytes": bank.stat().st_size,
        "encoder_size_bytes": ENCODER.stat().st_size,
        "calibration": {
            "method": f"Fixed linear {round(fraction * 100)}th percentile of heldout normal scores; no anomalous calibration",
            "normal": len(held),
            "anomalous": 0,
            "seed": 42,
            "policy": TUNED_POLICY,
            "quantile": fraction,
            "calibration_above_threshold": sum(s >= threshold for s in held),
            "future_false_positive_rate_guaranteed": False,
        },
        "train_normal_count": calibration["fit_normals"],
        "metrics": metrics,
        "resolution_short_edge": 448,
        "patch_size": 14,
        "foreground": "Unsupervised PCA threshold/sign heuristic; can fail",
        "decision_policy": TUNED_POLICY,
    }


def put(path, text, check):
    if path.exists():
        assert path.read_text(encoding="utf-8") == text, f"Preserve differing existing file: {path.name}"
    elif not check:
        path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify and print only; write nothing")
    args = parser.parse_args()
    digest = sha256(ENCODER)
    cards = {category: build_card(category, digest) for category in CATEGORIES}
    keys = ("image_auroc", "average_precision", "precision", "recall", "f1", "false_positive_rate")
    macro = {k: float(np.mean([c["metrics"][k] for c in cards.values()])) for k in keys}
    macro["pixel_auroc_224"] = float(np.mean([c["metrics"]["pixel_auroc_224"] for c in cards.values()]))
    macro["pixel_average_precision_224"] = float(
        np.mean([c["metrics"]["pixel_average_precision_224"] for c in cards.values()])
    )
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    assert macro["image_auroc"] > previous["macro_mean"]["image_auroc"], "Tuned profile did not improve macro AUROC"
    manifest = {
        "method": METHOD,
        "profile": "dinov2_tuned_v1",
        "protocol": PROTOCOL,
        "encoder_sha256": digest,
        "device": "cuda",
        "categories": cards,
        "macro_mean": macro,
        "decision_policy": TUNED_POLICY,
        "validation_scope": (
            "Held-out-normal thresholds and cached-score/software consistency checks; future recall and false-alarm "
            "rates are not guaranteed."
        ),
        "policy_selection_context": (
            "Same operating policy as the previous profile (q95 for every category, q80 for macaroni1/2). "
            "The test images were already seen in development, so these figures are descriptive."
        ),
        "previous_profile": {
            "profile": previous["profile"],
            "macro_mean": previous["macro_mean"],
            "source": "results/macaroni_recall_deployment_evaluation.json",
        },
        "source_sha256": {
            f"experiments/dinov2_tuned_v1/{c}/{name}": sha256(EXPERIMENT / c / name)
            for c in CATEGORIES
            for name in ("normal_calibration.json", "test_progress.json", "metrics.json")
        },
    }
    for category, card in cards.items():
        put(BANKS / f"{category}.json", json.dumps(card, indent=2) + "\n", args.check)
    put(ROOT / "results" / TUNED_FILENAME, json.dumps(manifest, indent=2) + "\n", args.check)
    marker = {
        "status": "active",
        "profile": "dinov2_tuned_v1",
        "categories": list(CATEGORIES),
        "deployment_evaluation": f"results/{TUNED_FILENAME}",
        "release_choice": (
            "One fixed fine-tune variant and one fixed bank size (32,768-patch coreset), chosen before scoring; "
            "no per-category selection. Descriptive evidence only (docs/ENCODER_DIAGNOSTIC.md)."
        ),
        "recovery": "Set DEFECTRAG_PROFILE=dinov2_highres_v1 (frozen encoder, previous banks) or legacy",
    }
    put(BANKS / "PROFILE.json", json.dumps(marker, indent=2) + "\n", args.check)
    print(json.dumps({"macro_mean": macro, "previous_macro_mean": previous["macro_mean"]}, indent=2))
    for category, card in cards.items():
        m = card["metrics"]
        print(
            f"{category:<11} AUROC {m['image_auroc']:.3f}  threshold {card['threshold']:.4f}  recall {m['recall']:.0%} "
            f"false alarms {m['false_positive_rate']:.0%}"
        )
    print("checked only" if args.check else "written")


if __name__ == "__main__":
    main()
