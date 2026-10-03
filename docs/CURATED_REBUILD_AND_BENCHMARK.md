# DefectRAG v7: curated knowledge, speed, and benchmark

## The simple picture

1. **Image input:** the visitor selects one of the **five** LOCO AD products, uploads an image, and chooses baseline, trained head, or fusion.
2. **Visual detector:** frozen DINOv3 extracts patches. The selected method scores each patch; the highest 10% form an image-level score. A connected high-response region gives one proposed box and a heatmap.
3. **Visual description:** Qwen2.5-VL sees the image and three crops. Its words are an observation/hypothesis, not a verified factory defect label.
4. **Knowledge retrieval:** FAISS + BM25 retrieve from a small, developer-managed text index. Retrieval is limited to general information and the selected product category. It cannot draw a screw-bag rule from a juice-bottle document.
5. **Report:** when an approved product rule was retrieved, Qwen drafts a short cited report. Otherwise, the app reports the visual observation and explicitly says that a product rule or root cause cannot be verified. The model has not learned a product manual from LOCO images.
6. **Result and record:** the UI shows the selected method, map, box, normal reference, evidence status, report, sources, and processing time. Render may persist records to AuraDB and media to Cloudinary if configured.

MVTec LOCO AD supplies benchmark images and masks across five categories. Its public dataset description is **not a complete manufacturing specification for each object**. The current index has 13 nonempty records: eight general and one category overview per product. It has **no approved category-specific manufacturing rules**. Do not infer exact quantities, acceptable placement, or root causes from these overviews. The historical source JSONL has 24 *lines* because of blank lines, not 24 knowledge records.

## Developer-only knowledge update

Visitor upload is disabled in `app/main.py` and `app/render_main.py` and removed from the shared webpage. To add knowledge, acquire a reliable source you have permission to use; verify its exact claims and version; convert the relevant source to UTF-8 text locally; and create a manifest with one or more claims tied to exact supporting excerpts. This is human curation, **not automatic truth checking**. The validator confirms the excerpt appears in the local source; the developer still must judge whether the paraphrased claim follows from it.

Example manifest for a hypothetical future source (replace every placeholder with a real reviewed source; **do not publish this example as knowledge**):

```json
{
  "sources": [{
    "path": "reviewed_product_specification.txt",
    "title": "Actual document title and version",
    "source_url": "https://replace-with-the-real-source.example",
    "reviewed_by": "Your name",
    "reviewed_at": "YYYY-MM-DD",
    "category": "breakfast_box",
    "rules": [{
      "id": "unique_rule_id",
      "claim": "Write a precise claim that the cited excerpt supports.",
      "evidence_excerpt": "Copy an exact, short excerpt from the source text here.",
      "anomaly_type": "logical"
    }]
  }]
}
```

Prepare a **staged** corpus in PowerShell, from the project directory:

```powershell
docker compose exec api python -m scripts.prepare_curated_knowledge --manifest /app/knowledge/review_manifest.json --source-root /app/knowledge/reviewed_sources --base /app/data/knowledge/knowledge_base.jsonl --output /app/data/knowledge/staged_review.jsonl
```

The paths in the example must actually exist inside the running container. In the current Compose file `knowledge/` is baked into the image, so for newly added files **rebuild only `api`** or use `docker cp` for a one-time run. The source data, features, checkpoints, and dataset remain on mounted volumes. Inspect the staged JSONL. After developer approval, back up the old corpus, replace `data/knowledge/knowledge_base.jsonl` with the staged file, run `python -m retrieval.build_index`, check the new `documents.json`/`dense.index` pair, evaluate retrieval, and redeploy those two index files plus source changes to the Space. Rebuilding the **text index** does not rerun DINOv3 feature extraction or retrain the heads. Retain a corpus/index version and freeze the benchmark labels against it.

The `knowledge_type=product_rule`, `review_status=approved`, reviewer, and source URL fields let the application distinguish a reviewed product rule from a general article. This is a small **provenance graph in the data model**: product → rule → source/reviewer. AuraDB currently stores inspections and used evidence; it is **not** the live retrieval store. A full graph retriever would need explicit rule extraction, entity resolution, contradiction review, and its own measured benefit. A graph database alone does not remove irrelevant text or hallucinations.

## Metrics and which runs are necessary

| Evaluation | Script and output | Run again? |
|---|---|---|
| Compact memory vs head vs fusion image detection | Existing `scripts.evaluate_trained_head` → `results/runtime/evaluation/seed42`, `seed43`, `seed44` `metrics.json` and `scores.csv` | **No.** Preserve and report your existing three completed runs. |
| Normal-feature head training | Existing `scripts.train_normal_head` → `results/runtime/training/seed*/training_summary.json`, checkpoints | **No.** Normal validation loss is not defect accuracy. |
| Compact baseline/head/fusion localization | New `scripts.evaluate_compact_localization` → per-image pixel AUROC, single enclosing-mask-box IoU, and recall at IoU .5 | **Yes, once per checkpoint seed if reporting localization SD.** Saved image scores lack the per-patch maps. |
| RAG retrieval | `scripts.evaluate_rag` → Hit/Precision/Recall/MRR/nDCG@5 | Label questions and relevant IDs, then run. Re-evaluate when the index changes. |
| RAG generated report | Human review of fixed questions/images and citations | Create a separate answer-quality protocol; retrieval metrics do not measure it. |
| End-to-end latency | Space payload `timing_seconds` plus browser/Render timing | Measure on live deployment; cold starts, queue and network are additional to Space processing time. |

To evaluate the *same compact 20,000-patch memory and seed 42 head* on masks:

```powershell
docker compose exec api python -m scripts.evaluate_compact_localization --dataset /app/mvtec_loco_ad --memory /app/cloud/space/assets --heads /app/results/runtime/training/seed42 --output /app/results/runtime/localization/seed42
Get-Content .\results\runtime\localization\seed42\metrics.json
```

This processes anomalous images in all five categories. `--max-images 2` is only a quick pipeline check and writes `complete: false`; omit it for a reported result. Add `--save-maps` when you want compressed raw 14×14 maps for later conversion to the official evaluation format. The script combines masks for the same test image, computes mean **per-image** pixel AUROC, and compares the one displayed box with the enclosing ground-truth mask box. The latter is a descriptive single-proposal metric, **not mAP50** and not official MVTec sPRO. MVTec provides [official evaluation code on its LOCO AD page](https://www.mvtec.com/research-teaching/datasets/mvtec-loco-ad); read its included format instructions before claiming a directly comparable paper result. The `--save-maps` files are **not yet its input format**. Do not select a box threshold on test masks and present that same test as independent validation.

Why no mAP50? YOLO mAP50 requires a scored set of object-detection boxes and matched object-level ground-truth boxes across confidence thresholds. DefectRAG currently creates one connected patch-response box after scoring. LOCO is designed for image anomaly detection and localization with masks, so image AUROC/AP and pixel/region localization are the natural headline measures. Converting masks into a single enclosing rectangle allows a supplemental IoU check, not an equivalent YOLO comparison.

For RAG, label `data/knowledge/rag_eval_gold.jsonl` with questions and relevant IDs from the **deployed index**, then run:

```powershell
docker compose exec api python -m scripts.evaluate_rag --gold /app/data/knowledge/rag_eval_gold.jsonl --index /app/retrieval/index --output /app/results/runtime/rag_eval --k 5 --candidate-k 10
```

Create categories for questions so the evaluation uses the same category filter as the website. Do not write questions by merely copying sentences from indexed documents. Test unanswerable product-specific questions as well; the current retrieval metrics script requires nonempty relevant IDs and therefore does **not** score abstention. Review unanswerable cases separately and report their abstention rate. With the current generic corpus, product-specific answer accuracy should not be claimed.

## Speed and user experience

- The inspection page shows an **actual elapsed timer**, not invented server stages. The Space payload includes detection/localization, VLM observation, and retrieval/report durations; queue and network time add to those numbers.
- The visual observation generation is shorter (240 token cap). A report with approved product rules has a shorter 300-token cap and at most four passages of up to 700 characters each. When no approved product rule is retrieved, the app returns a clearly bounded observation without a second LLM call. That reduces model work but does not promise a fixed number of seconds.
- First requests can still wait for Render and Space cold starts and a shared GPU queue. To determine the bottleneck, collect at least 20 warm and 5 cold runs, record median and p95 *total* browser time and Space phase times, then decide whether hardware or architecture changes are needed.
- The `Qwen2.5-VL-3B` model is used for both visual observation and the optional grounded report. Reducing token caps may shorten latency, but can truncate structured JSON; the code falls back to an unstructured observation when JSON parsing fails. Track this failure rate before claiming an improvement.

## Deployment order for v7 source update

1. Back up the current Windows project. Merge the v7 changed/new source files, keeping `mvtec_loco_ad/`, `features/`, `.env`, `results/runtime/`, `cloud/space/assets/*.pt`, `cloud/references/`, and the *current* `retrieval/index/` unless intentionally rebuilding knowledge.
2. Deploy updated Space code with its matching bank/checkpoints and index. Test one baseline inspection, one trained selection, a general knowledge question, and a question for an unsupported product rule. The old `/inspect` still supports an older Render inspection gateway; `/ask` now accepts an optional category.
3. Rebuild/redeploy Render with the new UI and gateway. Test mobile upload, method switching, missing checkpoint messaging, source status, elapsed timer, and contact form. Update local Docker API separately if you use it.
4. Run the existing unit tests. The local code checks do not prove a live remote endpoint, actual speed, or scientific validity.

**Research framing:** This is an anomaly detector plus an evidence-aware assistant, not DINOv3 fine-tuning or a validated factory acceptance system. The existing baseline threshold was chosen from benchmark labels and is a demonstration operating point. The three-seed comparisons use continuous scores; trained/fusion verdicts need a separately calibrated threshold and a fresh holdout to claim independent classification performance.
