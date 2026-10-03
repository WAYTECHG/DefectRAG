# Measuring retrieval-augmented generation

The detector's image AUROC/AP measures visual anomaly ranking. It does not measure knowledge retrieval or whether the LLM gives a factual, grounded answer. A BERT classifier might have accuracy/F1 for labeled classes; a RAG system needs separate labels for its retriever and answer quality.

## Reproducible retrieval evaluation

Create a **human-labeled** UTF-8 JSONL file at `data/knowledge/rag_eval_gold.jsonl`. Each line is one question with all relevant chunk IDs from the current `retrieval/index/documents.json`. Example schema (the example question must be reviewed against your actual index):

```json
{"id":"q001","category":"general","question":"How do logical anomalies differ from structural anomalies?","relevant_ids":["logical_definition","structural_definition"]}
```

Review the index IDs and label representative **answerable** questions across all five categories. Score unanswerable questions in a separate abstention review: this evaluator requires at least one relevant ID and cannot assign Recall@5 to an empty relevant set. Agree on relevance before running the system. If the index lacks category-specific approved rules, add reviewed knowledge and rebuild the index before expecting useful category-specific RAG results; re-annotate IDs if chunking changes. Avoid deriving questions directly from indexed sentences. The program rejects IDs absent from the current index.

From PowerShell in the project root after the updated scripts are in the running Docker container:

```powershell
docker compose exec api python -m scripts.evaluate_rag --gold /app/data/knowledge/rag_eval_gold.jsonl --index /app/retrieval/index --output /app/results/runtime/rag_eval --k 5 --candidate-k 10
Get-Content .\results\runtime\rag_eval\metrics.json
```

`metrics.json` reports macro averages across questions and per category for **Hit@5, Precision@5, Recall@5, MRR@5, and nDCG@5**. `per_question.csv` contains each retrieval ranking and score. These are real metrics only after you provide labels. The script uses the same FAISS + BM25 reciprocal-rank fusion and index as the Space; it loads the embedding model on CPU inside Docker, so the first run can take time. It does not call the LLM or claim to measure generated answers.

## Answer-quality evaluation

Separately, give reviewers a fixed sample of website questions and captured answers with retrieved sources. For each answer, label whether (1) the response answers the question, (2) every factual claim is supported by a cited source, (3) the citation points to the relevant source, and (4) a question with insufficient evidence was appropriately refused. Report the number of reviewed answers, per-category rates, disagreement between reviewers, and representative failures. An LLM judge can assist but should be checked against human ratings. Do not call the detector's AUROC a RAG metric, or report generated-answer faithfulness from retrieval metrics alone.
