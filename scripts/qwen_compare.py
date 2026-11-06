"""Print saved evaluation runs side by side.

    python -m scripts.qwen_compare gate50 lora

Each name is the --tag of a run made with scripts.qwen_eval on the test split.
"""

import json
import sys

from scripts.qwen_eval import OUT

ROWS = [
    ("retrieval_hit", "right chunk retrieved", "higher"),
    ("correct_all", "fully correct answers", "higher"),
    ("wrong_source", "answered with a wrong sentence", "lower"),
    ("no_answer_on_answerable", "no answer although one exists", "lower"),
    ("false_answer_on_unanswerable", "answered an unanswerable question", "lower"),
    ("generation_failed", "model output unusable (JSON/timeout)", "lower"),
]


def cell(v):
    lo, hi = v["ci95"]
    return f"{v['k']}/{v['n']} = {v['rate']:.0%} [{lo:.0%}-{hi:.0%}]"


def main():
    args = sys.argv[1:]
    split = "test"
    if "--split" in args:
        split = args[args.index("--split") + 1]
        del args[args.index("--split") : args.index("--split") + 2]
    tags = args
    if not tags:
        sys.exit("usage: python -m scripts.qwen_compare [--split test|mine] TAG [TAG ...]")
    data = {t: json.loads((OUT / f"summary_{t}_{split}.json").read_text()) for t in tags}
    print(f"{'measure':38s}" + "".join(f"{t:30s}" for t in tags) + "better is")
    for key, label, better in ROWS:
        print(f"{label:38s}" + "".join(f"{cell(data[t][key]):30s}" for t in tags) + better)
    print(f"{'seconds per generated answer':38s}" + "".join(f"{data[t]['mean_seconds_generated']!s:30s}" for t in tags))
    print("\n[...] is a 95% confidence interval. If two intervals overlap a lot, the difference may be noise.")


if __name__ == "__main__":
    main()
