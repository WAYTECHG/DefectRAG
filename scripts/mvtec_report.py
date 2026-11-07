"""Report for the one-shot MVTec AD evaluation (CPU only; run scripts.mvtec_eval first). Protocol: docs/MVTEC_EVALUATION.md.

    python -m scripts.mvtec_report

Image AUROC (primary), pixel AUROC and image average precision per category and macro mean, paired bootstrap 95%
intervals for the differences B-A, C-B and C-A, and descriptive operating points at the q95 threshold of the held-out
normals (same rule for every category). Results are written to results/mvtec_eval.json.
"""

import json

import numpy as np

from backend.config import ROOT
from scripts.diagnose_encoder import auroc
from scripts.encoder_candidates_report import bootstrap_difference
from scripts.mvtec_eval import ARMS, CATEGORIES, OUT

RESULT = ROOT / "results" / "mvtec_eval.json"
SUMMARY = ROOT / "results" / "mvtec_summary.json"
PROTOCOL_URL = "https://github.com/WAYTECHG/DefectRAG/blob/main/docs/MVTEC_EVALUATION.md"
LABELS = {
    "A_random_frozen": "Random-sample memory",
    "B_coreset_frozen": "Coreset memory",
    "C_coreset_tuned": "Coreset + fine-tuned encoder",
}
PAIRS = (
    ("B_coreset_frozen", "A_random_frozen"),
    ("C_coreset_tuned", "B_coreset_frozen"),
    ("C_coreset_tuned", "A_random_frozen"),
)
SHORT = {"A_random_frozen": "A", "B_coreset_frozen": "B", "C_coreset_tuned": "C"}


def main():
    rng = np.random.default_rng(2027)
    report = {}
    for category in CATEGORIES:
        path = OUT / f"{category}.json"
        if not path.exists():
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        names = sorted(record["test"])
        labels = np.array([record["labels"][n] for n in names])
        scores = {arm: np.array([record["test"][n][arm] for n in names]) for arm in ARMS}
        entry = {
            "n_test": len(names),
            "n_fit": record["n_fit"],
            "n_heldout": record["n_heldout"],
            "arms": {},
            "differences": {},
        }
        for arm in ARMS:
            held = np.array([s[arm] for s in record["heldout"].values()])
            threshold = float(np.quantile(held, 0.95))
            values = scores[arm]
            metrics = record["metrics"][arm]
            entry["arms"][arm] = {
                "auroc": auroc(values[labels == 1], values[labels == 0]),
                "pixel_auroc": metrics.get("pixel_auroc"),
                "average_precision": metrics["average_precision"],
                "recall_q95": float((values[labels == 1] >= threshold).mean()),
                "false_alarm_q95": float((values[labels == 0] >= threshold).mean()),
            }
        for better, base in PAIRS:
            low, high = bootstrap_difference(labels, scores[better], scores[base], rng)
            entry["differences"][f"{SHORT[better]}-{SHORT[base]}"] = [float(low), float(high)]
        report[category] = entry
    categories = list(report)
    RESULT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_summary(report, categories)

    def mark(interval):
        return " ▲" if interval[0] > 0 else " ▼" if interval[1] < 0 else "  "

    print(
        f"Categories scored: {len(categories)} of {len(CATEGORIES)}  (▲/▼ = clearly better/worse by paired bootstrap)\n"
    )
    print(
        f"{'category':<11}{'A random':>10}{'B coreset':>12}{'C tuned':>11}   {'B-A':>5}{'C-B':>5}{'C-A':>5}   pixel AUROC A / B / C"
    )
    for category in categories:
        a = report[category]["arms"]
        d = report[category]["differences"]
        pixel = " / ".join(f"{a[arm]['pixel_auroc']:.3f}" for arm in ARMS)
        print(
            f"{category:<11}"
            + "".join(
                f"{a[arm]['auroc']:>10.3f}" if i == 0 else f"{a[arm]['auroc']:>11.3f}" for i, arm in enumerate(ARMS)
            )
            + f"   {mark(d['B-A']):>5}{mark(d['C-B']):>5}{mark(d['C-A']):>5}   {pixel}"
        )

    def macro(arm, key):
        return float(np.mean([report[c]["arms"][arm][key] for c in categories]))

    print()
    print(
        f"{'MACRO MEAN':<11}"
        + "".join(
            f"{macro(arm, 'auroc'):>10.3f}" if i == 0 else f"{macro(arm, 'auroc'):>11.3f}" for i, arm in enumerate(ARMS)
        )
    )
    print("macro pixel AUROC:  " + "  ".join(f"{SHORT[arm]} {macro(arm, 'pixel_auroc'):.3f}" for arm in ARMS))
    print("macro image AP:     " + "  ".join(f"{SHORT[arm]} {macro(arm, 'average_precision'):.3f}" for arm in ARMS))
    print(
        "q95 recall / false alarms (macro):  "
        + "  ".join(
            f"{SHORT[arm]} {macro(arm, 'recall_q95'):.0%} / {macro(arm, 'false_alarm_q95'):.0%}" for arm in ARMS
        )
    )
    for pair in ("B-A", "C-B", "C-A"):
        better = sum(1 for c in categories if report[c]["differences"][pair][0] > 0)
        worse = sum(1 for c in categories if report[c]["differences"][pair][1] < 0)
        print(f"{pair}: clearly better in {better}, clearly worse in {worse} of {len(categories)} categories")
    print(
        "\nWritten to results/mvtec_eval.json. Descriptive; one run on a mirror copy of MVTec AD (docs/MVTEC_EVALUATION.md)."
    )


def write_summary(report, categories):
    """A compact file for the dashboard's Official benchmark page (macro means, per-product AUROC, clear differences)."""
    keys = ("auroc", "average_precision", "pixel_auroc", "recall_q95", "false_alarm_q95")
    macro = {arm: {k: float(np.mean([report[c]["arms"][arm][k] for c in categories])) for k in keys} for arm in ARMS}
    comparisons = {
        pair: {
            "better": sum(1 for c in categories if report[c]["differences"][pair][0] > 0),
            "worse": sum(1 for c in categories if report[c]["differences"][pair][1] < 0),
        }
        for pair in ("B-A", "C-B", "C-A")
    }
    summary = {
        "dataset": "MVTec AD",
        "scope": (
            "One offline run on 15 products the detector was never built for. Each product's memory comes from its own "
            "normal training photos; thresholds are the 95th percentile of held-out normal scores. These products are "
            "not available for inspection in this app."
        ),
        "protocol_url": PROTOCOL_URL,
        "arms": [{"key": arm, "label": LABELS[arm]} for arm in ARMS],
        "products": len(categories),
        "test_images": int(sum(report[c]["n_test"] for c in categories)),
        "macro_mean": macro,
        "comparisons": comparisons,
        "categories": {
            c: {"n_test": report[c]["n_test"], "arms": report[c]["arms"], "differences": report[c]["differences"]}
            for c in categories
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
