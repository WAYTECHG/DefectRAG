# Targeted Macaroni recall update — 18 October 2026

User authorized improving only Macaroni1/2 recall while minimizing compute, having
already selected higher sensitivity with more false alarms. The separate
`macaroni-recall-v1` policy uses a linear normal-calibration quantile of0.80 for
these two categories. The other ten cards remain exactly equal to the previous
q95 policy, including thresholds, model IDs and every metric.

| Saved official test results | Previous q95 | Targeted q80 |
|---|---:|---:|
| Macaroni1 recall | 57% | 85% |
| Macaroni1 precision | 98.28% | 77.98% |
| Macaroni1 normal false-positive rate | 1% | 24% |
| Macaroni1 confusion matrix, true rows normal/anomaly | [[99,1],[43,57]] | [[76,24],[15,85]] |
| Macaroni2 recall | 48% | 80% |
| Macaroni2 precision | 87.27% | 74.07% |
| Macaroni2 normal false-positive rate | 7% | 28% |
| Macaroni2 confusion matrix, true rows normal/anomaly | [[93,7],[52,48]] | [[72,28],[20,80]] |

All12 macro recall88.83%, precision90.47%, F1 89.57%, normal FPR11.10%.
These are retrospective development metrics. This operating choice followed
inspection of previously exposed test diagnostics. Numeric thresholds use only
the existing90 held-out training normals per category; they are not test-optimal
thresholds. There is no claim of independent validation or guaranteed future
recall. Substantial false alarms and15/20 missed benchmark anomalies remain.
Binary metrics use score>=threshold; the existing ±5% Uncertain review band is
separate, and Anomalous-only verdict recall is not the binary recall above.

## Why this limited change

A read-only audit compared saved nonzero heatmap support with nearest-resized
ground-truth masks at224×224. All43 Macaroni1 and52 Macaroni2 q95 false negatives
had100% support coverage, as did the caught anomalies. This provides no evidence
that wholesale foreground exclusion is the main cause. It does not prove perfect
native-resolution foreground segmentation or explain every missed defect.

The requested recall improvement is available from existing scores. Therefore no
new GPU experiment, encoder fine-tuning, rotation-bank generation, model download,
new dataset split or test inference was necessary. This improves operating recall,
not AUROC, feature separation, localization quality or named-defect recognition.
More advanced model experiments remain deferred; no claimed model improvement.

## Implementation and recovery

`scripts/prepare_macaroni_recall.py` creates
`results/macaroni_recall_deployment_evaluation.json` separately. Original cards,
banks, encoder, earlier manifests and benchmark results remain unchanged. New
Macaroni model IDs end `-q80-v1`. `backend/calibration.py` enforces that only those
two cards change, assets match, ranking metrics stay unchanged and thresholds are
valid. Local/ZeroGPU inspection and public evaluation use the same manifest.
Historical inspection records retain their actual saved decisions and thresholds.
The static showcase is not rebuilt or reclassified. No Supabase schema/data change.

Default policy when installed: `DEFECTRAG_CALIBRATION=macaroni-recall-v1`.
Restore the previous version with `normal-q95-v1`, or the original conservative
version with `normal-max-v1`; restart the backend or Space after changing it.
No asset refitting is required. Deployment/software evidence and resume status
are recorded in DEVELOPMENT_PROGRESS.md.
