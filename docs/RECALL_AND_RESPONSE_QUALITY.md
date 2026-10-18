# Operating recall and question-focused evidence answers

**18 October follow-up:** the original policy discussed below is preserved.
The separately versioned normal-q95 sensitivity policy raises retrospective macro
recall to83.83%, with precision93.26% and normal false-alarm rate7.43%.
See [trade-offs, all12 categories and rollback](SENSITIVITY_CALIBRATION.md).

## Precision and recall describe different failures

At the frozen operational threshold, precision is TP/(TP+FP); recall is
TP/(TP+FN). Precision1.000 and recall0.480 means all observed flagged images were
anomalous, while52% of annotated anomalous images were missed. It is not strong
coverage for an application intended to catch most defects. Precision1.000 is a
finite-test observation, not a promise of perfect future precision.

The displayed deployment examples include Capsules/Candle recall48%, Macaroni1
15%, Macaroni2 25% and PCB2 1%. The latter is especially weak:99% of labelled
anomalies lie below that binary decision threshold. These binary metrics use the
threshold alone; the dashboard's additional review band creates an Uncertain state
and does not retroactively improve the reported binary recall.

This bank calibrates the threshold as the maximum score of held-out normal
training images, deliberately limiting normal-image flags. That threshold can be
too high for anomaly coverage even when AUROC is good. Overall deployment macro
recall60.17% is separate from the retrospective three-seed mean image AUROC95.13%.
AUROC measures ranking across thresholds, not detection recall at a chosen one.

A future threshold study should reserve suitable labelled validation anomalies
or use a declared normal-quantile operating policy, choose the target trade-off
before evaluation, then report the frozen policy on held-out data. Choosing the
best threshold from these same test labels would contaminate reported performance.
No threshold, weights, bank, split or evaluation metric was changed in the earlier
answer/UI update. The subsequent sensitivity policy is documented separately above.
[Recall definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html).

## Actual RAG and the repeated answer bug

The application contains retrieval-augmented generation: question/inspection
context → BGE embeddings → attributed document retrieval → Qwen generation →
citation/quote validation. LangChain and LangGraph are libraries used to implement
that workflow; their names alone do not explain it. The About page now explicitly
names RAG. Direct score/verdict questions correctly use saved measurements without
claiming to call the LLM.

The overlap was caused by unconditional application-side measurement-prefix
assembly, not by missing retrieval. Heatmap/documentation questions now render
the topic-specific cited answer without a verdict prefix. Score-meaning answers
explain distance versus accuracy directly. Explicit result summaries can still
include measured verdict/threshold facts once. Original facts remain available in
the measurements panel and response metadata. Existing saved conversations are
preserved; these changes affect newly generated answers.

QC means quality control. Its decorative initials were replaced with a labelled
scan icon. SOP means standard operating procedure: an approved factory process
document. The included screening policy describes application behavior/limits;
it does not supply approved factory acceptance criteria, operating settings or
repair procedures. The About copy now explains that distinction plainly.
