"""Measure how well the assistant's language model picks and paraphrases evidence.

Builds a labelled question set from the knowledge documents, runs the real answer workflow
(retrieve, validate, generate, validate) and scores it with the project's own validator.

    python -m scripts.qwen_eval --split test --model qwen2.5:3b --tag base

Results are appended to experiments/qwen_lora_v1/runs/<tag>_<split>.jsonl and can be resumed.
Only the language-model step changes between runs; retrieval and checks are identical.
"""

import argparse
import json
import math
import random
import re
import time
import uuid

from backend.config import CATEGORIES, ROOT, Settings
from backend.rag import EvidenceWorkflow, KnowledgeIndex

OUT = ROOT / "experiments" / "qwen_lora_v1"

# Each topic: which model family the inspection must have (evidence is filtered by family),
# regex patterns that identify a correct supporting sentence, and question wordings.
# Wordings in "test" are never used for training.
TOPICS = {
    "score_meaning": (
        "any",
        r"score is not a defect probability|larger anomaly score",
        [
            "What does the anomaly score mean?",
            "Is the score a probability that this part is defective?",
            "How should I read the score number?",
            "Does a higher score mean more defects?",
        ],
        ["Explain what this score tells me.", "Can I treat the score as the chance of a defect?"],
    ),
    "verdict_good": (
        "any",
        r"Good means",
        [
            "What does a Good verdict mean?",
            "When is a result labelled Good?",
            "How does the system decide something is Good?",
            "What makes an inspection Good?",
        ],
        ["Explain the Good label.", "Under what condition do I get Good?"],
    ),
    "verdict_anomalous": (
        "any",
        r"Anomalous means",
        [
            "What does Anomalous mean?",
            "When is an inspection flagged as Anomalous?",
            "How does a result become Anomalous?",
            "What is needed for an Anomalous verdict?",
        ],
        ["Explain the Anomalous label.", "Why would a result be called Anomalous?"],
    ),
    "verdict_uncertain": (
        "any",
        r"Uncertain means|five-percent band",
        [
            "What does Uncertain mean?",
            "What is the Uncertain verdict?",
            "How wide is the Uncertain zone?",
            "When is a result Uncertain?",
        ],
        ["Explain the Uncertain label.", "How is the uncertain range defined?"],
    ),
    "review_band": (
        "any",
        r"review band is an operational heuristic|five-percent band",
        [
            "What is the review band?",
            "Is the review band a statistical confidence interval?",
            "How reliable is the review band?",
            "What kind of measure is the five percent band?",
        ],
        ["Tell me about the review band.", "Is the review band calibrated?"],
    ),
    "good_not_proof": (
        "any",
        r"not proof of factory acceptance",
        [
            "Does Good mean the product is safe?",
            "Can I ship a part just because it is Good?",
            "Is a Good result proof of acceptance?",
            "Does Good guarantee the part has no defects?",
        ],
        ["Is Good a guarantee of quality?", "Can I rely on Good as factory acceptance?"],
    ),
    "historical": (
        "any",
        r"Historical inspections retain|newer active model does not change",
        [
            "Will an old inspection change when a new model is installed?",
            "Do past results keep their original model?",
            "Does updating the model rewrite earlier verdicts?",
            "What happens to historical inspections after a model update?",
        ],
        ["Are earlier verdicts recalculated with the newer model?", "Do old heatmaps change after an upgrade?"],
    ),
    "saved_fields": (
        "any",
        r"saves its model ID",
        [
            "What information is saved with each inspection?",
            "Which details does an inspection record store?",
            "What gets saved for every inspection?",
            "Which fields are kept in a saved inspection?",
        ],
        ["What does the saved record contain?", "List what is stored for an inspection."],
    ),
    "heatmap": (
        "any",
        r"heatmap shows cosine distance|Larger distances indicate",
        [
            "What does the heatmap show?",
            "How is the heatmap computed?",
            "What do the brighter areas on the heatmap mean?",
            "What is measured by the heatmap?",
        ],
        ["Explain this heatmap.", "How do I read the heatmap?"],
    ),
    "coarse_localization": (
        "any",
        r"coarse localization|interpolation does not add",
        [
            "Is the heatmap a precise defect outline?",
            "Can the heatmap segment the exact defect?",
            "How precise is the localization?",
            "Does the heatmap name the defect?",
        ],
        ["Is localization exact?", "Does interpolation add detail to the heatmap?"],
    ),
    "product_scope": (
        "any",
        r"wrong-product uploads|operator selects the product category",
        [
            "What if I choose the wrong product category?",
            "Can I upload any kind of photo?",
            "Who selects the product category?",
            "Are wrong-product uploads supported?",
        ],
        ["What happens with an unsupported kind of image?", "Does the system detect the product type itself?"],
    ),
    "alerts_errors": (
        "any",
        r"create local review alerts|error event",
        [
            "What happens when a model failure occurs?",
            "When are review alerts created?",
            "Do failed runs create inspections?",
            "Which results trigger alerts?",
        ],
        ["What events create alerts?", "Is an error saved as a successful inspection?"],
    ),
    "visa": (
        "any",
        r"VisA provides|official one-class split|PCB1, capsules|Image-level labels|Multiclass masks|Normal images have no stored",
        [
            "What is the VisA dataset?",
            "How does the official VisA split work?",
            "What does VisA contain?",
            "Which products does VisA include?",
        ],
        ["Tell me about VisA.", "Does VisA include anomaly masks?"],
    ),
    "visa_license": (
        "any",
        r"CC BY 4\.0|SPot-the-Difference|Amazon Science",
        [
            "What licence is the VisA dataset under?",
            "Who should be credited for VisA?",
            "Who released the VisA dataset?",
            "How must VisA be attributed?",
        ],
        ["What is the VisA licence?", "Which paper introduced VisA?"],
    ),
    "legacy_profile": (
        "dinov3",
        r"frozen DINOv3 ViT-S/16|224 by 224|64 normal images|Original DINOv3|identifies the original|maximizes validation F1|Calibration uses 32",
        [
            "What is the original DINOv3 profile?",
            "What number of normal images does the original profile fit per product?",
            "What input size does the DINOv3 profile use?",
            "How is the original profile calibrated?",
        ],
        ["Describe the legacy model profile.", "What patch grid does the original profile use?"],
    ),
    "highres_profile": (
        "dinov2",
        r"frozen DINOv2 ViT-S/14|448-pixel|PCA-based foreground|averages the largest one percent|identifies the AnomalyDINO",
        [
            "What is the DINOv2 high-resolution profile?",
            "What image size does the high-resolution profile use?",
            "How is the anomaly score computed in this profile?",
            "What does the foreground heuristic do?",
        ],
        ["Describe the high-resolution model.", "Is the PCA foreground filter reliable?"],
    ),
    "calibration": (
        "dinov2",
        r"maximum heldout normal score|ten-percent holdout|no anomalous images",
        [
            "How is the decision threshold chosen?",
            "Which images set the threshold?",
            "Are anomalous images used to pick the threshold?",
            "How is the operational threshold calibrated?",
        ],
        ["Explain how the threshold is calibrated.", "What is the threshold based on?"],
    ),
    "metrics": (
        "dinov2",
        r"Image mAP is|Mean image AUROC|Pixel mAP|not bounding-box mAP",
        [
            "What is image mAP?",
            "How is mean image AUROC computed?",
            "Is mAP here the same as YOLO box mAP?",
            "Does DefectRAG predict bounding boxes?",
        ],
        ["Explain pixel mAP.", "Is this mAP measured at an IoU threshold?"],
    ),
    "retrospective": (
        "dinov2",
        r"retrospective development evaluation|Earlier official test exposure",
        [
            "Is the evaluation an untouched external test?",
            "Was the model evaluated on unseen data?",
            "How trustworthy is the reported accuracy?",
            "Why is the evaluation called retrospective?",
        ],
        ["Is the benchmark independent?", "Does earlier test exposure affect the results?"],
    ),
    "dinomaly": (
        "any",
        r"Dinomaly uses|compact nearest-normal fallback|does not establish|reconstruction|different method",
        [
            "How does Dinomaly differ from this detector?",
            "Does this app use Dinomaly reconstruction?",
            "What is Dinomaly?",
            "Can Dinomaly benchmark numbers describe this application?",
        ],
        ["Compare this model with Dinomaly.", "Is reconstruction used here?"],
    ),
}

# Questions the documents cannot answer. A good assistant returns no claim for these.
UNANSWERABLE = {
    "train": [
        "What is the capital of France?",
        "Give me a recipe for fried rice.",
        "Write a short poem about spring.",
        "What will the weather be tomorrow?",
        "How do I sort a list in Python?",
        "Who won the last football world cup?",
        "Translate 'good morning' into Malay.",
        "Tell me a joke.",
        "Who funded the VisA dataset?",
        "What is the total number of images in VisA?",
        "Which GPU does the high-resolution profile need?",
        "How long does one inspection take on a CPU?",
        "Does the system work on metal screws?",
        "What is the false alarm rate in production?",
        "Which camera should I use for the photos?",
        "What is the AUROC of the original profile on cashew?",
        "Is this approved for medical device inspection?",
        "Who wrote the DefectRAG project?",
    ],
    "test": [
        "What is the tallest mountain in the world?",
        "Suggest a name for my cat.",
        "How do I reverse a string in JavaScript?",
        "What is 17 times 23?",
        "Who paid for the VisA benchmark?",
        "What resolution in megapixels should the photos have?",
        "Does it work on bottle caps?",
        "What is the precision on macaroni?",
        "Which lighting setup is best?",
        "Is the system certified for aerospace parts?",
    ],
}


def load_cards():
    legacy = {c: json.loads((ROOT / "models" / f"{c}.json").read_text()) for c in CATEGORIES}
    high = {c: json.loads((ROOT / "models" / "highres" / f"{c}.json").read_text()) for c in CATEGORIES}
    return {"dinov3": legacy, "dinov2": high}


def make_inspection(cards, family, rng):
    category = rng.choice(CATEGORIES)
    card = cards[family][category]
    threshold, margin = card["threshold"], card["uncertainty_margin"]
    verdict = rng.choice(["Good", "Uncertain", "Anomalous"])
    if verdict == "Good":
        score = threshold - margin * rng.uniform(1.5, 8)
    elif verdict == "Anomalous":
        score = threshold + margin * rng.uniform(1.5, 8)
    else:
        score = threshold + margin * rng.uniform(-0.9, 0.9)
    return {
        "id": uuid.UUID(int=rng.getrandbits(128)).hex,
        "category": category,
        "verdict": verdict,
        "score": round(score, 5),
        "threshold": round(threshold, 5),
        "uncertainty_margin": round(margin, 5),
        "model_id": card["model_id"],
        "scope": "VisA benchmark appearance anomaly screening; category is user-selected and not verified by this model.",
        "localization": card.get("localization", "patch distances, interpolated; not a defect segmentation classifier"),
        "calibration": card.get("calibration"),
        "profile": card.get("profile"),
    }


MY_QUESTIONS = OUT / "my_questions.csv"


def knowledge_sentences():
    """Every sentence the assistant can quote, split exactly like rag.evidence_quotes does."""
    sources = json.loads((ROOT / "knowledge" / "sources.json").read_text(encoding="utf-8"))
    found = []
    for source in sources:
        text = (ROOT / "knowledge" / source["file"]).read_text(encoding="utf-8")
        for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
            sentence = sentence.strip()
            if len(sentence) >= 15 and not sentence.startswith("#"):
                found.append((source["id"], source["file"], sentence))
    return found


def load_my_questions(cards, rng):
    """Questions written by a person: columns 'question' and 'answer_phrase' (empty = unanswerable)."""
    import csv

    if not MY_QUESTIONS.exists():
        raise SystemExit(f"{MY_QUESTIONS} does not exist yet.")
    lines = [line for line in MY_QUESTIONS.read_text(encoding="utf-8-sig").splitlines() if not line.startswith("#")]
    sentences = knowledge_sentences()
    items = []
    problems = []
    for number, row in enumerate(csv.DictReader(lines), start=1):
        question = (row.get("question") or "").strip()
        phrase = (row.get("answer_phrase") or "").strip()
        if not question:
            continue
        if not phrase:
            family = rng.choice(["dinov2", "dinov3"])
            items.append(("unanswerable", "none", question, "", family))
            continue
        hits = [s for s in sentences if phrase.lower() in s[2].lower()]
        if not hits:
            problems.append(
                f"question {number} ({question[:50]!r}): answer_phrase {phrase!r} is not in any knowledge sentence"
            )
            continue
        sources = {h[0] for h in hits}
        family = (
            "dinov3"
            if sources == {"legacy-profile"}
            else "dinov2"
            if sources == {"highres-profile"}
            else rng.choice(["dinov2", "dinov3"])
        )
        items.append(("answerable", "mine", question, re.escape(phrase), family))
    if problems:
        raise SystemExit("Fix these rows in my_questions.csv:\n  " + "\n  ".join(problems))
    return [
        {
            "id": f"mine-{index}",
            "split": "mine",
            "kind": kind,
            "topic": topic,
            "question": question,
            "pattern": pattern,
            "inspection": make_inspection(cards, family, rng),
        }
        for index, (kind, topic, question, pattern, family) in enumerate(items)
    ]


def build_items(split, contexts=2, seed=7):
    """Deterministic list of labelled items for 'train', 'test' or 'mine' (your own CSV)."""
    rng = random.Random(f"{seed}-{split}")
    cards = load_cards()
    if split == "mine":
        return load_my_questions(cards, rng)
    items = []
    for topic, (family, pattern, train, test) in TOPICS.items():
        for question in train if split == "train" else test:
            for _ in range(contexts):
                fam = rng.choice(["dinov2", "dinov3"]) if family == "any" else family
                items.append(
                    {
                        "id": f"{split}-{topic}-{len(items)}",
                        "split": split,
                        "kind": "answerable",
                        "topic": topic,
                        "question": question,
                        "pattern": pattern,
                        "inspection": make_inspection(cards, fam, rng),
                    }
                )
    for question in UNANSWERABLE[split]:
        for _ in range(contexts):
            fam = rng.choice(["dinov2", "dinov3"])
            items.append(
                {
                    "id": f"{split}-none-{len(items)}",
                    "split": split,
                    "kind": "unanswerable",
                    "topic": "none",
                    "question": question,
                    "pattern": "",
                    "inspection": make_inspection(cards, fam, rng),
                }
            )
    return items


def score_item(item, state, seconds):
    """Turn one workflow result into measured outcomes."""
    claims = state.get("claims") or []
    raw = state.get("raw_claims") or []
    trace = state.get("trace") or []
    evidence = state.get("evidence") or []
    pattern = re.compile(item["pattern"], re.I) if item["pattern"] else None
    row = {
        "id": item["id"],
        "kind": item["kind"],
        "topic": item["topic"],
        "question": item["question"],
        "seconds": round(seconds, 2),
        "mode": state.get("mode"),
        "generated": "generate" in trace,
        "generation_failed": "generation_fallback" in trace,
        "n_raw": len(raw),
        "n_valid": len(claims),
        "claims": [{"text": c["text"], "source_id": c["source_id"], "quote": c["quote"]} for c in claims],
    }
    if item["kind"] == "answerable":
        row["retrieval_hit"] = any(pattern.search(e["text"]) for e in evidence)
        row["correct"] = bool(claims) and all(pattern.search(c["quote"]) for c in claims)
        row["wrong_source"] = bool(claims) and not row["correct"]
    else:
        row["false_answer"] = bool(claims)
    return row


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def summarize(rows):
    ans = [r for r in rows if r["kind"] == "answerable"]
    una = [r for r in rows if r["kind"] == "unanswerable"]
    hit = [r for r in ans if r["retrieval_hit"]]
    out = {"items": len(rows), "answerable": len(ans), "unanswerable": len(una)}

    def rate(name, k, n):
        lo, hi = wilson(k, n)
        out[name] = {"k": k, "n": n, "rate": round(k / n, 3) if n else None, "ci95": [round(lo, 3), round(hi, 3)]}

    rate("retrieval_hit", len(hit), len(ans))
    rate("correct_all", sum(r["correct"] for r in ans), len(ans))
    rate("correct_given_retrieval", sum(r["correct"] for r in hit), len(hit))
    rate("wrong_source", sum(r["wrong_source"] for r in ans), len(ans))
    rate("no_answer_on_answerable", sum(not r["n_valid"] for r in ans), len(ans))
    rate("false_answer_on_unanswerable", sum(r["false_answer"] for r in una), len(una))
    gen = [r for r in rows if r["generated"]]
    reached = [r for r in rows if r["generated"] or r["generation_failed"]]
    rate("generation_failed", sum(r["generation_failed"] for r in reached), len(reached))
    raw_total = sum(r["n_raw"] for r in gen)
    out["validator_dropped_claims"] = {"raw": raw_total, "kept": sum(r["n_valid"] for r in gen)}
    out["mean_seconds_generated"] = round(sum(r["seconds"] for r in gen) / len(gen), 2) if gen else None
    return out


def require_server(url):
    """Stop with a clear message if nothing answers at the model server address."""
    import urllib.request

    for path in ("/api/tags", "/"):
        try:
            urllib.request.urlopen(url.rstrip("/") + path, timeout=5).read()
            return
        except OSError:
            continue
    raise SystemExit(
        f"No model server is answering at {url}. Start it first (scripts.qwen_serve, or Ollama) and retry."
    )


SPACE_SYSTEM = (
    "Follow the application instructions. Return only valid JSON matching the supplied schema. "
    "No markdown fences or commentary."
)


def make_local_generator(model_dir, style):
    """Generate the way the Hugging Face Space does: bf16 weights, greedy decoding, output format NOT forced.

    style "space": the Space's own wrapper (system message + 'JSON schema: ...' appended to the prompt).
    style "plain": the prompt exactly as used in training.
    Returns a function with the same (prompt, schema) -> {"json": text} contract as deployment/space/generation.py.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda").eval()

    @torch.inference_mode()
    def generate(prompt, schema):
        if style == "space":
            messages = [
                {"role": "system", "content": SPACE_SYSTEM},
                {"role": "user", "content": prompt + "\nJSON schema: " + json.dumps(schema)},
            ]
        else:
            messages = [{"role": "user", "content": prompt}]
        values = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True
        )
        if values["input_ids"].shape[-1] > 4096:
            raise ValueError("Evidence request exceeds the bounded generation context")
        values = {key: value.to("cuda") for key, value in values.items()}
        output = model.generate(**values, max_new_tokens=384, do_sample=False, use_cache=True)
        text = tokenizer.decode(output[0, values["input_ids"].shape[-1] :], skip_special_tokens=True).strip()
        return {"json": text, "metadata": {}}

    return generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local-model", default=None, help="folder of a merged model: run it in-process like the Space"
    )
    parser.add_argument("--style", choices=["space", "plain"], default="space", help="with --local-model")
    parser.add_argument("--split", choices=["train", "test", "mine"], default="test")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--tag", default="base")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--url", default=None, help="Ollama-compatible server (default: your Ollama)")
    parser.add_argument("--list-sentences", action="store_true", help="write the quotable sentences to a file and exit")
    parser.add_argument("--check", action="store_true", help="with --split mine: only check the CSV, run nothing")
    args = parser.parse_args()
    if args.list_sentences:
        path = OUT / "knowledge_sentences.txt"
        rows = knowledge_sentences()
        path.write_text("\n".join(f"[{source}] {sentence}" for source, _, sentence in rows) + "\n", encoding="utf-8")
        print(f"wrote {len(rows)} sentences to {path}")
        return
    if args.check:
        items = build_items("mine")
        answerable = sum(i["kind"] == "answerable" for i in items)
        print(
            f"my_questions.csv is valid: {len(items)} questions ({answerable} answerable, {len(items) - answerable} unanswerable)"
        )
        return
    runs = OUT / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    path = runs / f"{args.tag}_{args.split}.jsonl"
    done = {json.loads(l)["id"]: json.loads(l) for l in path.read_text().splitlines()} if path.exists() else {}
    settings = Settings(ollama_model=args.model)
    if args.url:
        settings.ollama_url = args.url
    generator = None
    if args.local_model:
        generator = make_local_generator(args.local_model, args.style)
    else:
        require_server(settings.ollama_url)
    workflow = EvidenceWorkflow(settings, KnowledgeIndex(ROOT, OUT / "index"), generator)
    items = build_items(args.split)
    if args.limit:
        items = items[: args.limit]
    failures_in_a_row = 0
    for n, item in enumerate(items, 1):
        if item["id"] in done:
            continue
        start = time.perf_counter()
        state = workflow.graph.invoke({"question": item["question"], "inspection": item["inspection"], "history": []})
        row = score_item(item, state, time.perf_counter() - start)
        failures_in_a_row = failures_in_a_row + 1 if row["generation_failed"] else 0
        if failures_in_a_row >= 3:
            raise SystemExit(
                "STOPPED: the language model failed 3 times in a row, so these results would be meaningless. "
                "Is the server still running? Nothing from the failed items was saved."
            )
        done[item["id"]] = row
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            f"{n}/{len(items)} {item['kind'][:3]} {row['mode']:<15} {row['seconds']:>5}s  {item['question'][:60]}",
            flush=True,
        )
    summary = summarize([done[i["id"]] for i in items if i["id"] in done])
    (OUT / f"summary_{args.tag}_{args.split}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
