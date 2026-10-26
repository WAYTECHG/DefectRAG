# Model fitting, evaluation and calibration

DefectRAG uses pretrained frozen visual encoders and fitted normal-reference banks.
It is not an encoder fine-tuning project, a supervised defect classifier or a
Dinomaly reproduction. Changes to thresholds are not changes to model weights.

## Preserved profiles

| Area | Original baseline | High-resolution profile |
| --- | --- | --- |
| Encoder | Frozen DINOv3 ViT-S/16 | Frozen DINOv2 ViT-S/14 |
| Input |224×224 |448px short edge, aspect ratio retained and dimensions aligned to patches |
| Normal reference bank | Up to8,192 sampled patch features | Up to32,768 normal patch features with foreground/background sampling |
| Foreground | No foreground filtering | PCA-based heuristic with fixed processing rules |
| Benchmark | Official VisA assignments; seeds42/43/44 | Same test identities/content hashes and fixed seeds |
| Defect masks | Pixel evaluation only | Pixel evaluation only; not used to build the foreground heuristic |

The DINOv2 profile is a custom AnomalyDINO-inspired adaptation, not an exact paper
reproduction. Earlier test diagnostics informed development decisions, so the
reported comparison is retrospective development evidence, not an untouched
external validation. Include every category and seed rather than only the best.

## Reproduce an experiment deliberately

Provision the appropriate model assets and the licensed VisA dataset first. The
official one-class CSV assignments are authoritative. Training uses normal
reference images; do not replace them with a random all-image70/20/10 split.

```powershell
python -m scripts.benchmark_official --dataset 'C:/path/to/VisA_20220922'
python -m scripts.benchmark_highres --dataset 'C:/path/to/VisA_20220922'
```

These are explicit, potentially expensive experiments, not startup commands.
Completed receipts/caches allow supported runs to resume. Do not change a protocol
inside an existing experiment directory; use a separately versioned output for
new settings. The application never refits from ordinary uploads or on startup.
Model weights/banks are downloaded separately from the code repository.

## Benchmark metrics versus operating decisions

Report mean image AUROC and trapezoidal AU-PR across the12 products. Report pixel
AUROC/AU-PR separately for localization. Supplementary average precision is not
bounding-box mAP@IoU. Include preprocessing, normal-bank sampling, seed variability,
image identities and mask-map resolution. [Measured results](ACCURACY_RESULTS.md)
and [definitions](ACCURACY_AND_METRICS.md) describe the current comparison.

The deployment profile separately holds out content-grouped training normals for
calibration. Its current policy uses the fixed normal80th percentile for
Macaroni1/2 and95th percentile for the other10 products. The ±5% review band is a
heuristic, not statistical confidence. This trade-off increases recall and false
alarms while leaving the anomaly ranking and AUROC unchanged. Historical records
retain their original threshold and verdict. See
[targeted calibration](MACARONI_RECALL_UPDATE.md) and [q95 policy](SENSITIVITY_CALIBRATION.md).

Model or threshold decisions made after viewing test diagnostics need fresh,
independent validation before stronger generalization claims. Normal-only numeric
calibration does not make retrospective policy selection independent of the test.
No learning rate, optimizer or epoch count applies to frozen-bank fitting.

## RAG is a separate evaluation problem

BGE text retrieval and Qwen generation are not fine-tuning. Evaluate retrieval
relevance, citation/quote traceability, numerical faithfulness, unsupported-question
abstention, answer usefulness and latency separately from visual AUROC/recall.
Current answers use text and saved facts, not image-language reasoning. See
[Evidence Assistant architecture](ARCHITECTURE.md#evidence-assistant).
