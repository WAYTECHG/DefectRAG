"""Report for round 3 (CPU only; run scripts.encoder_banks first).

    python -m scripts.encoder_banks_report

Merges the round-3 scores (experiments/dinov2_banks) with the round-2 scores (experiments/dinov2_candidates) and uses
the same rules as scripts.encoder_candidates_report: scores standardised with the 90 held-out normals only, paired
bootstrap 95% intervals of the AUROC difference, thresholds from held-out normals only. The one fusion is fixed
here, before any result: the full DINOv2 bank averaged with the DINOv3 full bank. Descriptive only, because the test
images were already seen during development.
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
    standardised,
)

BANKS = ROOT / "experiments" / "dinov2_banks"
OUT = ROOT / "results" / "encoder_banks.json"
SIZES = ("base", "cap128", "cap256", "cap512", "core32k", "core64k", "core96k", "full")
OTHERS = ("base", "full", "rot", "dinov3full", "full+dinov3full")
FUSION = {"full+dinov3full": ("full", "dinov3full")}
WEAK = ("macaroni1", "macaroni2", "pcb2")
BYTES_PER_PATCH = 384 * 2  # half precision


def load():
    merged = {}
    for path in sorted(BANKS.glob("*.json")):
        if ".smoke" in path.name:
            continue
        banks = json.loads(path.read_text(encoding="utf-8"))
        earlier = json.loads((RESULTS / path.name).read_text(encoding="utf-8"))
        for split in ("heldout", "test"):
            for name, scores in banks[split].items():
                earlier[split][name].update(scores)
        earlier["bank_patches"].update(banks["bank_patches"])
        earlier["bank_patches"]["all_patches"] = banks["bank_patches"]["all_patches"]
        earlier["reproduction_round3"] = banks["reproduction"]["test_max_abs_difference"]
        merged[path.stem] = earlier
    return merged


def main():
    rng = np.random.default_rng(2027)
    records = load()
    categories = list(records)
    methods = [m for m in dict.fromkeys(SIZES + OTHERS) if m != "base"]
    report = {}
    for category, record in records.items():
        names = sorted(record["test"])
        labels = np.array([record["labels"][n] for n in names])
        _, base_test = standardised(record, ("base",))
        _, full_test = standardised(record, ("full",))
        entry = {}
        for name in ["base"] + methods:
            got = standardised(record, FUSION.get(name, (name,)))
            if got is None:
                continue
            held, test = got
            result = {
                "auroc": auroc(test[labels == 1], test[labels == 0]),
                "vs_base": None if name == "base" else bootstrap_difference(labels, test, base_test, rng).tolist(),
                "vs_full": None
                if name in ("base", "full")
                else bootstrap_difference(labels, test, full_test, rng).tolist(),
            }
            for label, quantile in (("q95", 0.95), ("deployed", DEPLOYED_QUANTILE.get(category, 0.95))):
                threshold = np.quantile(held, quantile)
                result[f"recall_{label}"] = float((test[labels == 1] >= threshold).mean())
                result[f"false_alarm_{label}"] = float((test[labels == 0] >= threshold).mean())
            if category in HARD_TYPES:
                kinds = anomaly_types(category, names)
                hard = np.array([HARD_TYPES[category] in kinds[n] for n in names])
                result["auroc_hard_type"] = auroc(test[hard & (labels == 1)], test[labels == 0])
            entry[name] = result
        report[category] = entry
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Categories analysed: {len(categories)} (round-3 harness reproduces the app within "
        f"{max(r['reproduction_round3'] for r in records.values()):.5f})\n"
    )

    def mark(m, key):
        interval = m.get(key)
        if not interval:
            return "  "
        return " ▲" if interval[0] > 0 else " ▼" if interval[1] < 0 else "  "

    def table(columns, key, title):
        print(title)
        print(f"{'category':<11}" + "".join(f"{c:>17}" for c in columns))
        for category in categories:
            cells = []
            for c in columns:
                m = report[category].get(c)
                cells.append(f"{'n/a':>17}" if m is None else f"{m['auroc']:>15.3f}{mark(m, key)}")
            print(f"{category:<11}" + "".join(cells))
        means = []
        for c in columns:
            values = [report[k][c]["auroc"] for k in categories if c in report[k]]
            means.append(f"{np.mean(values):>17.3f}" if len(values) == len(categories) else f"{'n/a':>17}")
        print(f"{'MEAN':<11}" + "".join(means) + "\n")

    table(SIZES, "vs_base", "Bank size: AUROC (▲/▼ = clearly better/worse than the deployed bank)")

    print("Bank size summary")
    print(
        f"{'bank':<10}{'patches/cat':>13}{'MB (analysed)':>15}{'mean AUROC':>12}{'gain kept':>11}{'weak 3':>8}{'worse than full':>17}"
    )
    base_mean = np.mean([report[k]["base"]["auroc"] for k in categories])
    full_mean = np.mean([report[k]["full"]["auroc"] for k in categories])
    for name in SIZES:
        sizes = [record["bank_patches"][name] for record in records.values()]
        mean = np.mean([report[k][name]["auroc"] for k in categories])
        weak_values = [report[k][name]["auroc"] for k in WEAK if k in report]
        weak = np.mean(weak_values) if weak_values else float("nan")
        worse = sum(1 for k in categories if mark(report[k][name], "vs_full") == " ▼")
        kept = (mean - base_mean) / (full_mean - base_mean)
        print(
            f"{name:<10}{np.mean(sizes):>13,.0f}{sum(sizes) * BYTES_PER_PATCH / 1e6:>15,.0f}{mean:>12.3f}{kept:>11.0%}{weak:>8.3f}{worse:>17}"
        )
    print()

    table(OTHERS, "vs_full", "Rotation and DINOv3: AUROC (▲/▼ = clearly better/worse than the FULL bank)")

    cols = ("base", "full", "cap512", "core64k", "core96k", "rot", "dinov3full")
    print("Hard defect types (AUROC of that type against all normals)")
    print(f"{'category / type':<40}" + "".join(f"{c:>12}" for c in cols))
    for category, kind in HARD_TYPES.items():
        if category in report:
            values = [report[category].get(c, {}).get("auroc_hard_type") for c in cols]
            print(
                f"{category + ' / ' + kind:<40}"
                + "".join(f"{'n/a':>12}" if v is None else f"{v:>12.3f}" for v in values)
            )

    affordable = [m for m in SIZES if m not in ("base", "full")]
    best = max(affordable, key=lambda m: np.mean([report[k][m]["auroc"] for k in categories]))
    print(
        f"\nOperating points, q95 for every category (best affordable bank by mean AUROC: {best}); "
        "deployed = q80 for macaroni1/2"
    )
    print(
        f"{'category':<11}{'method':<10}{'AUROC':>7}{'q95 recall':>12}{'q95 false':>11}{'dep. recall':>13}{'dep. false':>12}"
    )
    for category in (c for c in ("macaroni1", "macaroni2", "pcb2", "candle", "cashew") if c in report):
        for name in ("base", best, "full"):
            m = report[category][name]
            print(
                f"{category:<11}{name:<10}{m['auroc']:>7.3f}{m['recall_q95']:>12.0%}{m['false_alarm_q95']:>11.0%}"
                f"{m['recall_deployed']:>13.0%}{m['false_alarm_deployed']:>12.0%}"
            )
    print("\nWritten to results/encoder_banks.json. Descriptive only (test images already seen in development).")


if __name__ == "__main__":
    main()
