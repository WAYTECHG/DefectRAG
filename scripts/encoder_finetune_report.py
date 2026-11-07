"""Report for round 4, the fine-tuned encoder (CPU only; run scripts.encoder_finetune and
scripts.encoder_candidates --weights first).

    python -m scripts.encoder_finetune_report

Compares, on the same 200 test images per category, the frozen DINOv2 (experiments/dinov2_candidates) with the
fine-tuned one (experiments/dinov2_candidates_ft). The primary comparison, fixed before any result: the fine-tuned full
bank against the frozen full bank (same bank recipe, only the encoder differs). Same rules as
scripts.encoder_candidates_report: scores standardised with the 90 held-out normals only, paired bootstrap 95% intervals,
thresholds from held-out normals only (q95 for every category, and the deployed q80 for macaroni1/2 shown separately).
The "base" score in the fine-tuned files mixes the deployed bank (built with the frozen encoder) with fine-tuned
features and is not meaningful, so the deployed reference always comes from the frozen files. Descriptive only.
"""

import argparse
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

FROZEN = RESULTS
TUNED = ROOT / "experiments" / "dinov2_candidates_ft"
OUT = ROOT / "results" / "encoder_finetune.json"
METHODS = (("frozen base", "frozen", "base"), ("frozen full", "frozen", "full"), ("tuned full", "tuned", "full"))
EXTRA = (("tuned fullfg", "tuned", "fullfg"), ("tuned pos", "tuned", "pos"), ("frozen pos", "frozen", "pos"))


def scores(record, name, names):
    return np.array([record["test"][n][name] for n in names], float)


def held(record, name):
    return np.array([record["heldout"][n][name] for n in sorted(record["heldout"])], float)


def main():
    global TUNED, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="ft", help="read experiments/dinov2_candidates_<tag>")
    args = parser.parse_args()
    TUNED = ROOT / "experiments" / f"dinov2_candidates_{args.tag}"
    OUT = ROOT / "results" / ("encoder_finetune.json" if args.tag == "ft" else f"encoder_finetune_{args.tag}.json")
    rng = np.random.default_rng(2027)
    report, categories = {}, sorted(p.stem for p in TUNED.glob("*.json") if ".smoke" not in p.name)
    for category in categories:
        records = {
            "frozen": json.loads((FROZEN / f"{category}.json").read_text(encoding="utf-8")),
            "tuned": json.loads((TUNED / f"{category}.json").read_text(encoding="utf-8")),
        }
        names = sorted(records["frozen"]["test"])
        assert names == sorted(records["tuned"]["test"])
        labels = np.array([records["frozen"]["labels"][n] for n in names])
        entry, cache = {}, {}
        for label, source, name in METHODS + EXTRA:
            h = held(records[source], name)
            if any(v is None for v in h) or h.std() == 0:
                continue
            t = np.array([records[source]["test"][n][name] for n in names], float)
            if np.isnan(t).any():
                continue
            cache[label] = (h, t)
        full_test = (cache["frozen full"][1] - cache["frozen full"][0].mean()) / cache["frozen full"][0].std()
        for label, (h, t) in cache.items():
            z_held, z_test = (h - h.mean()) / h.std(), (t - h.mean()) / h.std()
            result = {"auroc": auroc(z_test[labels == 1], z_test[labels == 0])}
            if label != "frozen full":
                result["vs_frozen_full"] = bootstrap_difference(labels, z_test, full_test, rng).tolist()
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
        interval = m.get("vs_frozen_full")
        if not interval:
            return "  "
        return " ▲" if interval[0] > 0 else " ▼" if interval[1] < 0 else "  "

    labels_all = [m[0] for m in METHODS + EXTRA]
    print(f"Categories: {len(categories)}  (▲/▼ = clearly better/worse than the FROZEN full bank)\n")
    print(f"{'category':<11}" + "".join(f"{c:>15}" for c in labels_all))
    for category in categories:
        row = "".join(
            f"{report[category][c]['auroc']:>13.3f}{mark(report[category][c])}"
            if c in report[category]
            else f"{'n/a':>15}"
            for c in labels_all
        )
        print(f"{category:<11}{row}")
    print(
        f"{'MEAN':<11}"
        + "".join(
            f"{np.mean([report[k][c]['auroc'] for k in categories]):>15.3f}"
            if all(c in report[k] for k in categories)
            else f"{'n/a':>15}"
            for c in labels_all
        )
    )
    wins = sum(mark(report[k]["tuned full"]) == " ▲" for k in categories)
    losses = sum(mark(report[k]["tuned full"]) == " ▼" for k in categories)
    print(f"\ntuned full vs frozen full: clearly better in {wins}, clearly worse in {losses} of {len(categories)}\n")

    print("Hard defect types (AUROC of that type against all normals)")
    print(f"{'category / type':<40}{'frozen base':>13}{'frozen full':>13}{'tuned full':>13}")
    for category, kind in HARD_TYPES.items():
        if category in report:
            cells = "".join(
                f"{report[category][c]['auroc_hard_type']:>13.3f}" for c in ("frozen base", "frozen full", "tuned full")
            )
            print(f"{category + ' / ' + kind:<40}{cells}")

    print("\nOperating points: q95 for every category; deployed = q80 for macaroni1/2")
    print(
        f"{'category':<11}{'method':<13}{'AUROC':>7}{'q95 recall':>12}{'q95 false':>11}{'dep. recall':>13}{'dep. false':>12}"
    )
    for category in (c for c in ("macaroni1", "macaroni2", "pcb2", "candle", "cashew") if c in report):
        for label in ("frozen base", "frozen full", "tuned full"):
            m = report[category][label]
            print(
                f"{category:<11}{label:<13}{m['auroc']:>7.3f}{m['recall_q95']:>12.0%}{m['false_alarm_q95']:>11.0%}"
                f"{m['recall_deployed']:>13.0%}{m['false_alarm_deployed']:>12.0%}"
            )
    print(f"\nWritten to results/{OUT.name}. Descriptive only (test images already seen in development).")


if __name__ == "__main__":
    main()
