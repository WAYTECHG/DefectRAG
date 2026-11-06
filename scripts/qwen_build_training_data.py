"""Build the fine-tuning examples for the assistant's language model.

    python -m scripts.qwen_build_training_data            # version 1 -> data/train.jsonl
    python -m scripts.qwen_build_training_data --v2       # version 2 -> data/train_v2.jsonl

Each example is the exact prompt the model sees in production (retrieved, numbered sentences)
and the answer we want back:

* answerable question -> the sentence that really answers it and a short restatement. The restatement
  is the base model's own answer when it passed the project's validator, otherwise the sentence itself.
* question the documents cannot answer -> {"claims": []}  (the model must learn to say "nothing fits").

Version 1 uses the TRAIN wordings in scripts/qwen_eval.py. Version 2 keeps every version 1 example and adds
the questions in experiments/qwen_lora_v1/v2_questions.csv (every knowledge sentence, conversational wording).
Test questions are never used: version 2 refuses any new question that is (nearly) identical to one in the
test wordings, in my_questions.csv, or in the short-question test.
"""

import argparse
import csv
import json
import random
import re
from collections import Counter

from backend.config import ROOT, Settings
from backend.rag import EvidenceWorkflow, KnowledgeIndex
from scripts.qwen_eval import (
    MY_QUESTIONS,
    OUT,
    TOPICS,
    UNANSWERABLE,
    build_items,
    knowledge_sentences,
    load_cards,
    make_inspection,
)

NUMBER = r"\d+(?:\.\d+)?"
V2_QUESTIONS = OUT / "v2_questions.csv"


def prepare_state(workflow, item):
    """Run the workflow up to the generation step. Returns None if the model would never be asked."""
    state = {"question": item["question"], "inspection": item["inspection"], "history": []}
    state.update(workflow.route(state))
    if state["mode"] == "abstained":
        return None
    state.update(workflow.retrieve(state))
    state.update(workflow.validate_evidence(state))
    return state if state.get("evidence") else None


def base_restatements(workflow, state, quotes):
    """Ask the base model once; keep restatements that pass the number check, keyed by quote_id."""
    produced = workflow.generate(dict(state))
    by_quote = {q["quote"]: qid for qid, q in quotes.items()}
    good = {}
    for claim in produced.get("raw_claims", []):
        qid = by_quote.get(claim.get("quote"))
        text = claim.get("text", "").strip()
        if qid and text and set(re.findall(NUMBER, text)) <= set(re.findall(NUMBER, claim["quote"])):
            good[qid] = text
    return good


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def protected_questions():
    """Every question that belongs to a test set, so version 2 can be checked against them."""
    from scripts.qwen_short_questions import ONE_WORD, SHORT

    protected = [q for _, (_, _, _, test) in TOPICS.items() for q in test] + UNANSWERABLE["test"]
    protected += [text for text, _ in SHORT + ONE_WORD]
    lines = [line for line in MY_QUESTIONS.read_text(encoding="utf-8-sig").splitlines() if not line.startswith("#")]
    protected += [row["question"].strip() for row in csv.DictReader(lines) if row["question"].strip()]
    return protected


def too_similar(question, protected, threshold=0.7):
    """True if the question is the same as, or a close rewording of, a protected test question."""
    a = words(question)
    return any(a == words(p) or len(a & words(p)) / len(a | words(p)) >= threshold for p in protected)


def v2_items(rng):
    """Items from v2_questions.csv: 1 inspection per answerable question, 2 per unanswerable one."""
    cards = load_cards()
    sentences = knowledge_sentences()
    protected = protected_questions()
    lines = [line for line in V2_QUESTIONS.read_text(encoding="utf-8-sig").splitlines() if not line.startswith("#")]
    items, dropped = [], []
    for number, row in enumerate(csv.DictReader(lines), start=1):
        question, phrase = row["question"].strip(), row["answer_phrase"].strip()
        if not question:
            continue
        if too_similar(question, protected):
            dropped.append(f"too similar to a test question: {question}")
            continue
        hits = [s for s in sentences if phrase and phrase.lower() in s[2].lower()]
        if phrase and not hits:
            raise SystemExit(f"v2_questions.csv row {number}: phrase not found in any sentence: {phrase!r}")
        sources = {h[0] for h in hits}
        if sources == {"legacy-profile"}:
            families = ["dinov3"]
        elif sources == {"highres-profile"}:
            families = ["dinov2"]
        else:
            families = ["dinov2", "dinov3"]
        for _ in range(1 if phrase else 2):
            items.append(
                {
                    "id": f"v2-{len(items)}",
                    "kind": "answerable" if phrase else "unanswerable",
                    "topic": "v2" if phrase else "none",
                    "question": question,
                    "pattern": re.escape(phrase) if phrase else "",
                    "inspection": make_inspection(cards, rng.choice(families), rng),
                }
            )
    return items, dropped


def make_example(workflow, item, stats):
    """One training example for an item, or None when the model would not be asked or the answer is missing."""
    state = prepare_state(workflow, item)
    if state is None:
        stats["skipped: model would not be asked (no evidence or prohibited topic)"] += 1
        return None
    prompt, quotes = workflow.build_prompt(state)
    if item["kind"] == "unanswerable":
        claims = []
    else:
        pattern = re.compile(item["pattern"], re.I)
        wanted = [qid for qid, q in quotes.items() if pattern.search(q["quote"])][:2]
        if not wanted:
            stats["skipped: answer sentence not in retrieved evidence"] += 1
            return None
        restated = base_restatements(workflow, state, quotes)
        claims = [{"quote_id": qid, "text": restated.get(qid, quotes[qid]["quote"])} for qid in wanted]
        stats["restatement from base model"] += sum(qid in restated for qid in wanted)
        stats["restatement = the sentence itself"] += sum(qid not in restated for qid in wanted)
    stats[f"example: {item['kind']}"] += 1
    return {
        "id": item["id"],
        "kind": item["kind"],
        "topic": item["topic"],
        "pattern": item["pattern"],
        "prompt": prompt,
        "completion": json.dumps({"claims": claims}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b", help="Ollama model used for restatements")
    parser.add_argument("--contexts", type=int, default=2, help="version 1: inspections per question")
    parser.add_argument("--v2", action="store_true", help="add the version 2 questions to the version 1 examples")
    args = parser.parse_args()
    out_dir = OUT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = Counter()
    if args.v2:
        examples = [json.loads(line) for line in (out_dir / "train.jsonl").read_text(encoding="utf-8").splitlines()]
        stats["example: version 1 kept as they are"] = len(examples)
        workflow = EvidenceWorkflow(Settings(ollama_model=args.model), KnowledgeIndex(ROOT, OUT / "index"))
        items, dropped = v2_items(random.Random("v2-7"))
        for message in dropped:
            print("dropped:", message)
        examples += [e for e in (make_example(workflow, item, stats) for item in items) if e]
        path = out_dir / "train_v2.jsonl"
    else:
        workflow = EvidenceWorkflow(Settings(ollama_model=args.model), KnowledgeIndex(ROOT, OUT / "index"))
        examples = [
            e
            for e in (make_example(workflow, item, stats) for item in build_items("train", contexts=args.contexts))
            if e
        ]
        path = out_dir / "train.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in examples) + "\n", encoding="utf-8")
    print(f"wrote {len(examples)} examples to {path}")
    for key, value in sorted(stats.items()):
        print(f"  {value:4d}  {key}")
    lengths = sorted(len(e["prompt"]) + len(e["completion"]) for e in examples)
    print(f"characters per example: min {lengths[0]}, median {lengths[len(lengths) // 2]}, max {lengths[-1]}")


if __name__ == "__main__":
    main()
