"""How do short or vague questions behave at different similarity cutoffs? (CPU only, no language model)

    python -m scripts.qwen_short_questions

For every question this finds the 3 most similar document chunks and records the best similarity.
A question "succeeds" at a cutoff if a chunk containing the answer sentence is among the results with
similarity >= cutoff. An unrelated question "leaks" if any chunk passes (so the language model would be asked).
Output: experiments/qwen_lora_v1/short_question_report.json
"""

import csv
import json

import numpy as np

from backend.config import ROOT
from backend.rag import KnowledgeIndex
from scripts.qwen_eval import MY_QUESTIONS, OUT, UNANSWERABLE

CUTOFFS = [0.30, 0.35, 0.40, 0.45, 0.50]

# (3 to 4 word version of the full question, phrase from the answering sentence)
SHORT = [
    ("anomaly score meaning", "not a defect probability"),
    ("Uncertain result meaning", "within a fixed five-percent band around the threshold"),
    ("Good result guarantee", "not proof of factory acceptance or product safety"),
    ("heatmap colours meaning", "shows cosine distance between each image patch feature"),
    ("warning what next", "Review source images and heatmaps before acting"),
    ("detect defect type", "does not predict specific defect types"),
    ("which model old result", "Consult that saved record"),
    ("new model old results", "does not change a historical verdict or heatmap"),
    ("analysis fails what happens", "Model failures create an error event"),
    ("alerts when", "Anomaly and uncertain events create local review alerts"),
    ("which products allowed", "wrong-product uploads are outside validated scope"),
    ("what is VisA", "VisA provides normal and anomalous product images"),
    ("sample photos source", "sample previews are resized JPEG derivatives"),
    ("VisA licence", "released by Amazon Science under CC BY 4.0"),
    ("trained on defects", "fits on normal images"),
    ("original model image size", "a 224 by 224 input"),
    ("background filtering", "PCA-based foreground heuristic filters background patches"),
    ("how threshold chosen", "maximum heldout normal score"),
    ("precision recall threshold", "use a frozen threshold"),
    ("accuracy fair test", "not an untouched external test"),
    ("copy of published method", "rather than an exact reproduction of AnomalyDINO"),
    ("normal images masks", "Normal images have no stored anomaly mask"),
    ("explanation about my photo", "must remain separate from saved image measurements"),
]
ONE_WORD = [
    ("heatmap", "shows cosine distance between each image patch feature"),
    ("VisA", "VisA provides normal and anomalous product images"),
    ("licence", "released by Amazon Science under CC BY 4.0"),
    ("alerts", "Anomaly and uncertain events create local review alerts"),
    ("Uncertain", "within a fixed five-percent band around the threshold"),
    ("score", "not a defect probability"),
    ("AnomalyDINO", "rather than an exact reproduction of AnomalyDINO"),
    ("Good", "Good means the score lies below the decision threshold"),
]


def load_full():
    lines = [line for line in MY_QUESTIONS.read_text(encoding="utf-8-sig").splitlines() if not line.startswith("#")]
    rows = list(csv.DictReader(lines))
    full = [(r["question"].strip(), r["answer_phrase"].strip()) for r in rows if r["answer_phrase"].strip()]
    unrelated = [r["question"].strip() for r in rows if r["question"].strip() and not r["answer_phrase"].strip()]
    return full, unrelated


def main():
    index = KnowledgeIndex(ROOT, OUT / "index")
    index.ensure()
    chunks = [d.page_content.lower() for d in index.documents]

    def probe(text):
        vector = np.asarray(index.embeddings.embed_query(text), dtype="float32")
        scores = index.matrix @ vector
        order = [int(i) for i in np.argsort(scores)[::-1][:3]]
        return [(i, float(scores[i])) for i in order]

    def success(phrase, hits, cutoff):
        return any(score >= cutoff and phrase.lower() in chunks[i] for i, score in hits)

    full, unrelated = load_full()
    groups = {"full question": full, "3-4 words": SHORT, "one word": ONE_WORD}
    report = {"cutoffs": CUTOFFS, "on_topic": {}, "unrelated_leak": {}}
    print(f"{'on-topic questions, right answer retrieved':44s}" + "".join(f"{c:>8.2f}" for c in CUTOFFS))
    for name, items in groups.items():
        probes = [(text, phrase, probe(text)) for text, phrase in items]
        row = [sum(success(p, h, c) for _, p, h in probes) for c in CUTOFFS]
        best = sorted(h[0][1] for _, _, h in probes)
        report["on_topic"][name] = {
            "n": len(items),
            "retrieved_at_cutoff": row,
            "lowest_best_similarity": round(best[0], 3),
            "median_best_similarity": round(best[len(best) // 2], 3),
            "below_050": [t for t, _, h in probes if h[0][1] < 0.50],
        }
        print(
            f"{name + f' (n={len(items)})':44s}"
            + "".join(f"{v:>8d}" for v in row)
            + f"   median best similarity {best[len(best) // 2]:.2f}, lowest {best[0]:.2f}"
        )
    others = unrelated + UNANSWERABLE["train"] + UNANSWERABLE["test"]
    probes = [(text, probe(text)) for text in others]
    print(f"\n{'unrelated questions that still reach the model':44s}" + "".join(f"{c:>8.2f}" for c in CUTOFFS))
    row = [sum(any(score >= c for _, score in hits) for _, hits in probes) for c in CUTOFFS]
    report["unrelated_leak"] = {"n": len(others), "reach_model_at_cutoff": row}
    print(f"{f'unrelated (n={len(others)})':44s}" + "".join(f"{v:>8d}" for v in row))
    (OUT / "short_question_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("\nsaved short_question_report.json")


if __name__ == "__main__":
    main()
