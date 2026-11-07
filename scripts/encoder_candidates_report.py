"""Compare the detector candidates (step 2 of 2, CPU only; run scripts.encoder_candidates first).

    python -m scripts.encoder_candidates_report

Rules fixed before any result was seen:
* Every candidate score is standardised with the mean and spread of the 90 held-out NORMAL images (no labels).
* Fusions are plain averages of those standardised scores; the list below is complete, nothing was added after looking.
* Each method is compared with the deployed one ("base") by a paired bootstrap of the AUROC difference
  (images resampled with replacement within normals and within anomalies, 2,000 rounds, 95% interval).
* A method counts as an improvement only if the interval for the difference stays above zero.
* Thresholds come from the held-out normals only: q95 for every category (a like-for-like comparison) and the
  deployed q80 for Macaroni1/2.
* The 200 test images per category were already seen during development, so this is descriptive, not a fresh test.
"""

import argparse
import csv
import json

import numpy as np

from backend.config import ROOT
from scripts.diagnose_encoder import auroc

RESULTS = ROOT / "experiments" / "dinov2_candidates"
VISA = ROOT / "VisA_20220922"
OUT = ROOT / "results" / "encoder_candidates.json"
SINGLES = ("base", "full", "fullfg", "pos", "cls", "meanpool", "coarse")
FUSIONS = {
    "base+cls": ("base", "cls"),
    "base+coarse": ("base", "coarse"),
    "base+pos": ("base", "pos"),
    "full+cls": ("full", "cls"),
    "full+meanpool": ("full", "meanpool"),
    "full+coarse": ("full", "coarse"),
    "full+pos": ("full", "pos"),
    "fullfg+coarse": ("fullfg", "coarse"),
    "full+coarse+cls": ("full", "coarse", "cls"),
    "full+coarse+pos": ("full", "coarse", "pos"),
}
HARD_TYPES = {
    "macaroni1": "chip around edge and corner",
    "macaroni2": "small chip around edge",
    "pcb2": "missing",
    "pcb3": "missing",
    "candle": "weird candle wick",
}
DEPLOYED_QUANTILE = {"macaroni1": 0.80, "macaroni2": 0.80}
ROUNDS = 2000


def standardised(record, parts):
    """Average of the held-out-normal standardised scores of the named candidates, or None if unavailable."""
    held_names, test_names = sorted(record["heldout"]), sorted(record["test"])
    held = np.zeros(len(held_names))
    test = np.zeros(len(test_names))
    for part in parts:
        h = [record["heldout"][n][part] for n in held_names]
        t = [record["test"][n][part] for n in test_names]
        if any(v is None for v in h + t):
            return None
        h, t = np.array(h, float), np.array(t, float)
        spread = h.std()
        if spread == 0:
            return None
        held += (h - h.mean()) / spread / len(parts)
        test += (t - h.mean()) / spread / len(parts)
    return held, test


def bootstrap_difference(labels, method, base, rng):
    positive, negative = np.flatnonzero(labels == 1), np.flatnonzero(labels == 0)
    differences = np.empty(ROUNDS)
    for i in range(ROUNDS):
        p = rng.choice(positive, len(positive))
        n = rng.choice(negative, len(negative))
        differences[i] = auroc(method[p], method[n]) - auroc(base[p], base[n])
    return np.percentile(differences, [2.5, 97.5])


def anomaly_types(category, names):
    rows = {r["image"]: r for r in csv.DictReader((VISA / category / "image_anno.csv").open(encoding="utf-8"))}
    return {n: [t.strip() for t in rows[n]["label"].split(",")] for n in names}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", default="base", choices=SINGLES, help="method every difference is measured against")
    anchor = parser.parse_args().anchor
    rng = np.random.default_rng(2026)
    records = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(RESULTS.glob("*.json"))
        if ".smoke" not in p.name
    }
    methods = list(SINGLES) + list(FUSIONS)
    report = {}
    for category, record in records.items():
        names = sorted(record["test"])
        labels = np.array([record["labels"][n] for n in names])
        entry = {"reproduction_max_abs_difference": record["reproduction"]["test_max_abs_difference"], "methods": {}}
        _, base_test = standardised(record, (anchor,))
        for name in methods:
            parts = (name,) if name in SINGLES else FUSIONS[name]
            got = standardised(record, parts)
            if got is None:
                continue
            held, test = got
            value = auroc(test[labels == 1], test[labels == 0])
            interval = None if name == anchor else bootstrap_difference(labels, test, base_test, rng).tolist()
            result = {"auroc": value, "difference_vs_base_95": interval}
            for label, quantile in (("q95", 0.95), ("deployed", DEPLOYED_QUANTILE.get(category, 0.95))):
                threshold = np.quantile(held, quantile)
                result[f"recall_{label}"] = float((test[labels == 1] >= threshold).mean())
                result[f"false_alarm_{label}"] = float((test[labels == 0] >= threshold).mean())
            if category in HARD_TYPES:
                types = anomaly_types(category, names)
                hard = np.array([HARD_TYPES[category] in types[n] for n in names])
                result["auroc_hard_type"] = auroc(test[hard & (labels == 1)], test[labels == 0])
            entry["methods"][name] = result
        report[category] = entry
    target = OUT if anchor == "base" else OUT.with_name(f"encoder_candidates_vs_{anchor}.json")
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")

    categories = list(report)
    print(
        f"Categories analysed: {len(categories)}. Harness reproduces the app: largest difference "
        f"{max(e['reproduction_max_abs_difference'] for e in report.values()):.5f}\n"
    )

    def table(columns, title):
        print(title)
        print(f"{'category':<11}" + "".join(f"{c:>17}" for c in columns))
        for category in categories:
            cells = []
            for c in columns:
                m = report[category]["methods"].get(c)
                if m is None:
                    cells.append(f"{'n/a':>17}")
                    continue
                mark = ""
                if m["difference_vs_base_95"] is not None:
                    low, high = m["difference_vs_base_95"]
                    mark = " ▲" if low > 0 else " ▼" if high < 0 else ""
                cells.append(f"{m['auroc']:>15.3f}{mark:<2}")
            print(f"{category:<11}" + "".join(cells))
        macro = []
        for c in columns:
            values = [report[k]["methods"][c]["auroc"] for k in categories if c in report[k]["methods"]]
            macro.append(f"{np.mean(values):>17.3f}" if len(values) == len(categories) else f"{'n/a':>17}")
        print(f"{'MEAN':<11}" + "".join(macro) + "\n")

    print(f"AUROC per category. ▲ = better than '{anchor}' (95% interval above 0), ▼ = worse.\n")
    table(SINGLES, "Single candidates")
    table(list(FUSIONS)[:5], "Fusions (1/2)")
    table(list(FUSIONS)[5:], "Fusions (2/2)")

    print("Hard defect types (AUROC of that type against all normals)")
    print(
        f"{'category / type':<40}"
        + "".join(f"{c:>14}" for c in ("base", "full", "fullfg", "coarse", "full+coarse", "full+pos"))
    )
    for category, kind in HARD_TYPES.items():
        if category not in report:
            continue
        cells = [
            report[category]["methods"].get(c, {}).get("auroc_hard_type")
            for c in ("base", "full", "fullfg", "coarse", "full+coarse", "full+pos")
        ]
        print(f"{category + ' / ' + kind:<40}" + "".join(f"{'n/a':>14}" if v is None else f"{v:>14.3f}" for v in cells))

    ranked = sorted(
        (m for m in methods if m != "base" and all(m in report[k]["methods"] for k in categories)),
        key=lambda m: -np.mean([report[k]["methods"][m]["auroc"] for k in categories]),
    )
    print("\nOperating points for the three best methods by mean AUROC (thresholds from held-out normals only)")
    print("q95 = same policy everywhere; deployed = q80 for macaroni1/2")
    shown = ["base", "full"] + [m for m in ranked if m != "full"][:2]
    print(
        f"{'category':<11}{'method':<17}{'AUROC':>7}{'q95 recall':>12}{'q95 false':>11}{'dep. recall':>13}{'dep. false':>12}"
    )
    for category in categories:
        if category not in ("macaroni1", "macaroni2", "pcb2", "candle", "cashew"):
            continue
        for name in shown:
            m = report[category]["methods"][name]
            print(
                f"{category:<11}{name:<17}{m['auroc']:>7.3f}{m['recall_q95']:>12.0%}{m['false_alarm_q95']:>11.0%}"
                f"{m['recall_deployed']:>13.0%}{m['false_alarm_deployed']:>12.0%}"
            )
    print(
        "\nA method is an improvement only if the weak categories gain with an interval above 0 and no category is "
        "significantly worse (▼). Written to results/encoder_candidates.json."
    )


if __name__ == "__main__":
    main()
