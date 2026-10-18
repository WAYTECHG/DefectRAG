# Recall-oriented decision calibration

**Follow-up:** the current default `macaroni-recall-v1` changes only Macaroni1/2
to normal-q80. The q95 policy described below remains selectable and preserved.
See [targeted recall update](MACARONI_RECALL_UPDATE.md).

## What changed

The original maximum-held-out-normal threshold was too conservative for the
requested anomaly-catching workflow. Its precision/recall calculations were
correct: all 12 confusion matrices, precision, recall and F1 were reproduced
from cached genuine inference scores. Calibration/test content hashes and label
polarity were checked. PCB2's largest normal calibration score was 0.34184;
its normal 95th percentile was 0.12522. One extreme score therefore set a much
higher operating threshold. This is not evidence that the image is mislabeled.

The user selected **prioritize catching anomalies; accept more false alarms**.
The separate `normal-q95-v1` policy uses the linear 95th percentile of existing
held-out training-normal scores for every product. No per-category quantile or
test-optimal threshold is selected. Encoder, memory banks, image scores, masks,
heatmap normalization, dataset assignments and official ranking metrics stay
unchanged. This is decision calibration, not retraining or improved AUROC.

## Measured trade-off on saved official test scores

| Macro mean over 12 products | Original maximum-normal policy | Normal q95 policy |
|---|---:|---:|
| Recall | 60.17% | 83.83% |
| Precision | 97.59% | 93.26% |
| F1 | 68.63% | 87.56% |
| Normal-image false-positive rate | 2.42% | 7.43% |

| Product | Original recall | q95 recall | q95 precision | Normal images flagged |
|---|---:|---:|---:|---:|
| PCB1 | 78% | 86% | 91.5% | 8/100 |
| Capsules | 48% | 82% | 94.3% | 5/60 |
| Cashew | 88% | 90% | 90.9% | 9/50 |
| Candle | 48% | 87% | 87.9% | 12/100 |
| Chewing gum | 96% | 96% | 98.0% | 2/50 |
| Fryum | 88% | 94% | 98.9% | 1/50 |
| Macaroni1 | 15% | 57% | 98.3% | 1/100 |
| Macaroni2 | 25% | 48% | 87.3% | 7/100 |
| PCB2 | 1% | 84% | 87.5% | 12/100 |
| PCB3 | 69% | 87% | 90.6% | 9/101 |
| PCB4 | 68% | 96% | 96.0% | 4/101 |
| Pipe fryum | 98% | 99% | 98.0% | 2/50 |

These are **retrospective development measurements**, not an untouched validation
set or a guarantee of future recall. The sensitivity audit and previous test
results were seen before this policy was adopted. Although numeric thresholds
use only normal calibration scores, this development choice was informed by the
observed recall problem. Quantile95 is a declared workflow choice, not a threshold
optimized against test labels. A fresh external/labeled validation set is still
needed to certify a desired recall or false-alarm target. The holdout contains
45–91 normals per category; a 95th percentile does not guarantee a future 5% FPR.
Macaroni recall remains weak and requires separate approved model research or
additional representative validation data; threshold changes do not solve every
feature-separation limitation.

Binary metrics use `score >= threshold`. The UI also applies the existing ±5%
review band, producing an Uncertain verdict near the threshold. Those images
receive review alerts; binary recall is not identical to Anomalous-only verdict
recall. Neither is a calibrated confidence interval.

## Versioning, deployment and recovery

`results/highres_deployment_evaluation.json` and `models/highres/*.json` retain
the original cards. `results/sensitive_deployment_evaluation.json` is separate.
Local and ZeroGPU inference load the same guarded overlay through
`backend/calibration.py`. `/api/models` and `/api/evaluation` select the same
policy. New model IDs end in `-q95-v1`; records store their actual threshold,
margin and calibration. Historical records are never reclassified or rewritten.
The static showcase is preserved with its original recorded results.

The default is q95 when its manifest is installed. Restore original decisions
by setting `DEFECTRAG_CALIBRATION=normal-max-v1` and restarting the backend/Space.
Set `normal-q95-v1` to restore sensitivity. Unknown policies or mismatched assets
fail closed. A source installation without the overlay keeps original behavior.

```powershell
# Read saved results; no inference or training:
python -m scripts.audit_recall
# Reproduce the separate calibration manifest; differing existing output is refused:
python -m scripts.prepare_sensitive_calibration
```

The audit saves source SHA-256 hashes and checks original inputs again before
writing its separate report. No model download, new training run, GPU request,
Supabase schema change or historical-record mutation is needed for calibration.
Software verification: 56 focused calibration/API/answer/high-resolution tests
passed; 6 frontend tests and both local/cloud builds passed. Deployment status
and final hosted checks are recorded in DEVELOPMENT_PROGRESS.md.
