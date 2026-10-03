"""Evaluate the deployed hybrid retriever on human-labeled question/doc-ID pairs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from rag.evaluation import retrieval_metrics
from retrieval.hybrid_retriever import HybridRetriever

METRICS = ("hit_at_k", "precision_at_k", "recall_at_k", "mrr_at_k", "ndcg_at_k")


def read_gold(path: Path, valid_ids: set[str]) -> list[dict]:
    rows = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}") from exc
        qid, question, relevant = item.get("id"), item.get("question"), item.get("relevant_ids")
        if not isinstance(qid, str) or not qid.strip() or qid in seen:
            raise ValueError(f"Line {line_number}: question ID must be a unique nonempty string")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Line {line_number}: question must be nonempty")
        if not isinstance(relevant, list) or not relevant or not all(isinstance(doc, str) for doc in relevant):
            raise ValueError(f"Line {line_number}: relevant_ids must contain document IDs")
        missing = set(relevant) - valid_ids
        if missing:
            raise ValueError(f"Line {line_number}: IDs are absent from the current index: {sorted(missing)}")
        seen.add(qid)
        rows.append(item)
    if not rows:
        raise ValueError("Gold question file contains no labeled questions")
    return rows


def aggregate(rows: list[dict]) -> dict:
    return {"queries": len(rows), **{metric: mean(row[metric] for row in rows) for metric in METRICS}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True, help="Human-labeled JSONL question set")
    parser.add_argument("--index", type=Path, default=Path("retrieval/index"))
    parser.add_argument("--output", type=Path, default=Path("results/runtime/rag_eval"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=10)
    args = parser.parse_args()
    if args.k < 1 or args.candidate_k < args.k:
        parser.error("require 1 <= k <= candidate-k")

    # Validate labels against the *same* indexed chunks used by the Space.
    documents = json.loads((args.index / "documents.json").read_text(encoding="utf-8"))
    valid_ids = {doc["id"] for doc in documents}
    gold = read_gold(args.gold, valid_ids)
    retriever = HybridRetriever(index_dir=args.index, device="cpu")
    rows = []
    for item in gold:
        found = retriever.search(item["question"], k=args.k, candidate_k=args.candidate_k,
                                 category=item.get("category") if item.get("category") != "unspecified" else None)
        ids = [doc["id"] for doc in found]
        metrics = retrieval_metrics(ids, set(item["relevant_ids"]), args.k)
        rows.append({"id": item["id"], "category": item.get("category", "unspecified"),
                     "question": item["question"], "relevant_ids": json.dumps(item["relevant_ids"]),
                     "retrieved_ids": json.dumps(ids), **metrics})
        print(f"{item['id']}: hit@{args.k}={metrics['hit_at_k']:.0f} retrieved={ids}", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "per_question.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    categories = sorted({row["category"] for row in rows})
    report = {"protocol": "Human-labeled relevant chunk IDs; fixed hybrid FAISS+BM25 retrieval; binary relevance",
              "k": args.k, "candidate_k": args.candidate_k, "gold_file": str(args.gold),
              "overall": aggregate(rows),
              "by_category": {category: aggregate([row for row in rows if row["category"] == category]) for category in categories},
              "limitations": "Retrieval metrics only. They do not measure answer correctness, faithfulness, or visual localization."}
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["overall"], indent=2))


if __name__ == "__main__":
    main()
