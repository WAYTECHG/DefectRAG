"""Report for round 5 (CPU only; run scripts.encoder_tuned_coreset first).

    python -m scripts.encoder_tuned_coreset_report

Primary comparison, fixed before any result: the 32,768-patch coreset built from the fine-tuned (realistic-defect)
encoder against the 32,768-patch coreset built from the frozen encoder, the version that would be shipped otherwise.
Also shown: the deployed bank, the frozen full bank and the tuned full bank. Same rules as round 2/3: scores standardised
with the 90 held-out normals only, paired bootstrap 95% intervals, thresholds from held-out normals only (q95 for every
category, and the deployed q80 for macaroni1/2 shown separately). Descriptive only: the test images were already seen.
"""

import json

import numpy as np

from backend.config import ROOT
from scripts.diagnose_encoder import auroc
from scripts.encoder_candidates_report import (
    DEPLOYED_QUANTILE,
    HARD_TYPES,
    RESULTS,
    anomaly_types,
    bootstrap_difference,
)

EXPERIMENTS = ROOT / "experiments"
TUNED_CORESET = EXPERIMENTS / "dinov2_tuned_coreset"
OUT = ROOT / "results" / "encoder_tuned_coreset.json"
METHODS = ("frozen base", "frozen core32k", "frozen full", "tuned full", "tuned core32k")
REFERENCE = "frozen core32k"
WEAK = ("macaroni1", "macaroni2", "pcb2")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pick(category):
    """(held-out, test) score arrays per method, in the order of the sorted test image names."""
    frozen = read(RESULTS / f"{category}.json")
    banks = read(EXPERIMENTS / "dinov2_banks" / f"{category}.json")
    tuned_full = read(EXPERIMENTS / "dinov2_candidates_realistic" / f"{category}.json")
    tuned_core = read(TUNED_CORESET / f"{category}.json")
    names = sorted(frozen["test"])
    held_names = sorted(frozen["heldout"])
    sources = {
        "frozen base": (frozen, "base"),
        "frozen core32k": (banks, "core32k"),
        "frozen full": (frozen, "full"),
        "tuned full": (tuned_full, "full"),
        "tuned core32k": (tuned_core, "core32k"),
    }
    out = {}
    for label, (record, key) in sources.items():
        out[label] = (
            np.array([record["heldout"][n][key] for n in held_names], float),
            np.array([record["test"][n][key] for n in names], float),
        )
    labels = np.array([frozen["labels"][n] for n in names])
    return out, labels, names


def main():
    rng = np.random.default_rng(2027)
    categories = sorted(p.stem for p in TUNED_CORESET.glob("*.json") if ".smoke" not in p.name)
    report = {}
    for category in categories:
        arrays, labels, names = pick(category)
        standard = {k: ((h - h.mean()) / h.std(), (t - h.mean()) / h.std()) for k, (h, t) in arrays.items()}
        reference = standard[REFERENCE][1]
        entry = {}
        for label, (z_held, z_test) in standard.items():
            result = {"auroc": auroc(z_test[labels == 1], z_test[labels == 0])}
            if label != REFERENCE:
                result["vs_frozen_core32k"] = bootstrap_difference(labels, z_test, reference, rng).tolist()
            for tag, quantile in (("q95", 0.95), ("deployed", DEPLOYED_QUANTILE.get(category, 0.95))):
                threshold = np.quantile(z_held, quantile)
                result[f"recall_{tag}"] = float((z_test[labels == 1] >= threshold).mean())
                result[f"false_alarm_{tag}"] = float((z_test[labels == 0] >= threshold).mean())
            if category in HARD_TYPES:
                kinds = anomaly_types(category, names)
                hard = np.array([HARD_TYPES[category] in kinds[n] for n in names])
                result["auroc_hard_type"] = auroc(z_test[hard & (labels == 1)], z_test[labels == 0])
            entry[label] = result
        report[category] = entry
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def mark(m):
        interval = m.get("vs_frozen_core32k")
        if not interval:
            return "  "
        return " ▲" if interval[0] > 0 else " ▼" if interval[1] < 0 else "  "

    print(f"Categories: {len(categories)}  (▲/▼ = clearly better/worse than the FROZEN 32k coreset)\n")
    print(f"{'category':<11}" + "".join(f"{m:>16}" for m in METHODS))
    for category in categories:
        print(
            f"{category:<11}"
            + "".join(f"{report[category][m]['auroc']:>14.3f}{mark(report[category][m])}" for m in METHODS)
        )
    print(f"{'MEAN':<11}" + "".join(f"{np.mean([report[k][m]['auroc'] for k in categories]):>16.3f}" for m in METHODS))
    weak = [k for k in WEAK if k in report]
    if weak:
        print(
            f"{'weak 3':<11}"
            + "".join(f"{np.mean([report[k][m]['auroc'] for k in weak]):>16.3f}" for m in METHODS)
            + f"   (mean over {', '.join(weak)})"
        )
    tuned = "tuned core32k"
    better = sum(mark(report[k][tuned]) == " ▲" for k in categories)
    worse = sum(mark(report[k][tuned]) == " ▼" for k in categories)
    print(
        f"\ntuned coreset vs frozen coreset: clearly better in {better}, clearly worse in {worse} of {len(categories)}"
    )

    print("\nHard defect types (AUROC of that type against all normals)")
    print(f"{'category / type':<40}" + "".join(f"{m:>16}" for m in METHODS))
    for category, kind in HARD_TYPES.items():
        if category in report:
            print(
                f"{category + ' / ' + kind:<40}"
                + "".join(f"{report[category][m]['auroc_hard_type']:>16.3f}" for m in METHODS)
            )

    print("\nOperating points: q95 for every category; deployed = q80 for macaroni1/2")
    print(
        f"{'category':<11}{'method':<16}{'AUROC':>7}{'q95 recall':>12}{'q95 false':>11}{'dep. recall':>13}{'dep. false':>12}"
    )
    for category in (c for c in ("macaroni1", "macaroni2", "pcb2", "candle", "cashew") if c in report):
        for label in ("frozen base", "frozen core32k", "tuned core32k"):
            m = report[category][label]
            print(
                f"{category:<11}{label:<16}{m['auroc']:>7.3f}{m['recall_q95']:>12.0%}{m['false_alarm_q95']:>11.0%}"
                f"{m['recall_deployed']:>13.0%}{m['false_alarm_deployed']:>12.0%}"
            )
    print(f"\nWritten to results/{OUT.name}. Descriptive only (test images already seen in development).")


if __name__ == "__main__":
    main()
