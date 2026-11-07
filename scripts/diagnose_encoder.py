"""Where does the frozen DINOv2 detector fail? A read-only diagnostic.

    python -m scripts.diagnose_encoder

It reads only files that already exist: the cached per-image test scores and held-out normal
calibration scores in experiments/dinov2_highres_v1/<category>/ (thresholds are rebuilt from the
calibration scores: q95 for every category, plus the deployed q80 for Macaroni1/2), the VisA annotation
CSV (defect type text) and the VisA masks (defect size).
No model is loaded, nothing is trained and nothing in the app is changed. Masks are used for
diagnosis only. Results are written to results/encoder_diagnostic.json.

These test images were already seen during development, so the figures are descriptive, not a
fresh validation.
"""

import csv
import json

import numpy as np
from PIL import Image

from backend.config import ROOT

RUNS = ROOT / "experiments" / "dinov2_highres_v1"
VISA = ROOT / "VisA_20220922"
OUT = ROOT / "results" / "encoder_diagnostic.json"
MIN_GROUP = 8  # below this many anomalous images a rate is too noisy to read
DEPLOYED_BANK = 3  # bank_3 is the operational bank; banks 0-2 are the benchmark seeds
DEPLOYED_QUANTILE = {"macaroni1": 0.80, "macaroni2": 0.80}  # macaroni-recall-v1 policy; every other category is q95


def auroc(positive, negative):
    """Probability that a random anomaly scores higher than a random normal (ties count half)."""
    p, n = np.asarray(positive, float), np.asarray(negative, float)
    if len(p) == 0 or len(n) == 0:
        return None
    greater = (p[:, None] > n[None, :]).sum()
    ties = (p[:, None] == n[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(p) * len(n)))


def mask_fraction(path):
    with Image.open(path) as image:
        return float((np.asarray(image.convert("L")) > 0).mean())


def analyse(category):
    rows = json.loads((RUNS / category / "test_progress.json").read_text(encoding="utf-8"))
    calibration = json.loads((RUNS / category / "normal_calibration.json").read_text(encoding="utf-8"))
    held_out = np.array([p["score"] for p in calibration["predictions"]])
    annotations = {r["image"]: r for r in csv.DictReader((VISA / category / "image_anno.csv").open(encoding="utf-8"))}
    # The cards in models/highres still hold the older "maximum held-out normal" threshold. The deployed
    # thresholds are linear quantiles of the held-out normal scores: q95 everywhere, q80 for Macaroni1/2.
    q95 = float(np.quantile(held_out, 0.95))
    deployed_quantile = DEPLOYED_QUANTILE.get(category, 0.95)
    threshold = float(np.quantile(held_out, deployed_quantile))
    items = []
    for row in rows:
        note = annotations[row["image"]]
        entry = {"label": row["label"], "score": row["scores"][DEPLOYED_BANK], "image": row["image"]}
        if row["label"] == 1:
            entry["types"] = [t.strip() for t in note["label"].split(",") if t.strip()] or ["unlabelled"]
            entry["area"] = mask_fraction(VISA / note["mask"]) if note["mask"] else None
        items.append(entry)
    normal = np.array([i["score"] for i in items if i["label"] == 0])
    anomaly = [i for i in items if i["label"] == 1]
    anomaly_scores = np.array([i["score"] for i in anomaly])
    seeds = [auroc([r["scores"][b] for r in rows if r["label"] == 1], [r["scores"][b] for r in rows if r["label"] == 0])
             for b in range(len(rows[0]["scores"]))]
    result = {
        "deployed_policy": f"q{round(deployed_quantile * 100)}",
        "threshold": threshold,
        "threshold_q95": q95,
        "recall_at_q95": float((anomaly_scores >= q95).mean()),
        "normal_false_alarm_rate_at_q95": float((normal >= q95).mean()),
        "n_normal": int(len(normal)),
        "n_anomaly": int(len(anomaly)),
        "auroc_deployed": auroc(anomaly_scores, normal),
        "auroc_all_banks": [round(s, 4) for s in seeds],
        "recall_at_threshold": float((anomaly_scores >= threshold).mean()),
        "normal_false_alarm_rate": float((normal >= threshold).mean()),
        "normal_score_median": float(np.median(normal)),
        "normal_score_p95": float(np.percentile(normal, 95)),
        "anomaly_score_median": float(np.median(anomaly_scores)),
    }
    by_type = {}
    for name in sorted({t for i in anomaly for t in i["types"]}):
        group = [i["score"] for i in anomaly if name in i["types"]]
        by_type[name] = {
            "n": len(group),
            "detected_at_threshold": float((np.array(group) >= threshold).mean()),
            "auroc_vs_normals": auroc(group, normal),
        }
    result["by_defect_type"] = by_type
    sized = [i for i in anomaly if i.get("area") is not None]
    if len(sized) >= 3 * MIN_GROUP:
        cuts = np.quantile([i["area"] for i in sized], [1 / 3, 2 / 3])
        buckets = {"small": lambda a: a <= cuts[0], "medium": lambda a: cuts[0] < a <= cuts[1], "large": lambda a: a > cuts[1]}
        by_size = {}
        for name, test in buckets.items():
            group = [i for i in sized if test(i["area"])]
            scores = np.array([i["score"] for i in group])
            by_size[name] = {
                "n": len(group),
                "median_mask_area_percent": round(100 * float(np.median([i["area"] for i in group])), 3),
                "detected_at_threshold": float((scores >= threshold).mean()),
                "auroc_vs_normals": auroc(scores, normal),
            }
        result["by_defect_size"] = by_size
    return result


def main():
    categories = sorted(p.name for p in RUNS.iterdir() if (p / "test_progress.json").exists())
    report = {}
    for category in categories:
        report[category] = analyse(category)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Per category, deployed bank (descriptive, development-exposed test set).")
    print("AUROC does not depend on the threshold. 'q95' columns compare every category on the same policy;")
    print("'deployed' shows the policy the app really uses (q80 for macaroni1/2).\n")
    print(f"{'category':<11}{'AUROC':>7}{'bank spread':>13}  | {'q95 recall':>10}{'q95 false':>10}  | {'deployed':>8}{'recall':>8}{'false':>7}")
    for name, r in sorted(report.items(), key=lambda kv: kv[1]["auroc_deployed"]):
        spread = max(r["auroc_all_banks"]) - min(r["auroc_all_banks"])
        print(f"{name:<11}{r['auroc_deployed']:>7.3f}{spread:>13.3f}  | {r['recall_at_q95']:>10.0%}{r['normal_false_alarm_rate_at_q95']:>10.0%}  | "
              f"{r['deployed_policy']:>8}{r['recall_at_threshold']:>8.0%}{r['normal_false_alarm_rate']:>7.0%}")
    print("\nWeakest categories: by defect size (small / medium / large thirds of the anomalous test images)")
    for name, r in sorted(report.items(), key=lambda kv: kv[1]["auroc_deployed"])[:5]:
        size = r.get("by_defect_size")
        if not size:
            continue
        cells = "   ".join(f"{k}: AUROC {v['auroc_vs_normals']:.2f}, found {v['detected_at_threshold']:.0%} "
                           f"(median {v['median_mask_area_percent']}% of image)" for k, v in size.items())
        print(f"  {name:<10}{cells}")
    print(f"\nWeakest categories: by defect type (groups with at least {MIN_GROUP} images)")
    for name, r in sorted(report.items(), key=lambda kv: kv[1]["auroc_deployed"])[:5]:
        print(f"  {name}")
        for kind, v in sorted(r["by_defect_type"].items(), key=lambda kv: kv[1]["auroc_vs_normals"]):
            if v["n"] >= MIN_GROUP:
                print(f"    {kind[:60]:<60} n={v['n']:<3} AUROC {v['auroc_vs_normals']:.2f}  found {v['detected_at_threshold']:.0%}")
    print(f"\nWritten to {OUT.relative_to(ROOT)}. Nothing else was touched.")


if __name__ == "__main__":
    main()
