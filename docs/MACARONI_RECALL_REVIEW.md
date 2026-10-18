# Remaining Macaroni recall limitations — 18 October 2026

The active normal-q95-v1 policy still misses43/100 annotated Macaroni1 anomalies
and52/100 Macaroni2 anomalies in binary threshold evaluation. This is a material
limitation, not healthy coverage or evidence of a metric calculation bug.

A CPU-only sensitivity check reused the existing high-resolution bank3 scores
and held-out normal calibration scores. No inference, model download, retraining,
deployment or database change was performed for this review.

| Category / normal calibration quantile | Recall | Precision | Normal false alarms |
|---|---:|---:|---:|
| Macaroni1 q95, active | 57% | 98.28% | 1/100 |
| Macaroni1 q90, diagnostic only | 76% | 86.36% | 12/100 |
| Macaroni2 q95, active | 48% | 87.27% | 7/100 |
| Macaroni2 q90, diagnostic only | 66% | 80.49% | 16/100 |

The q90 thresholds are approximately0.119283 (Macaroni1) and0.134511
(Macaroni2); exact values can be reproduced from the existing normal calibration
JSON using scripts.audit_recall.quantile(scores,.90). The q90 diagnostic was NOT
activated. These are retrospective test-score observations, not independently
validated estimates or a guarantee of future sensitivity. Threshold relaxation
cannot improve AUROC, and still misses24%/34% of benchmark anomalies here.

## Recommended bounded next investigation

1. Audit false-negative locations against existing ground-truth masks and saved
   heatmaps. Inspect whether the PCA foreground heuristic excludes defect regions
   or whether retained patches simply score similarly to normal patches. Masks
   are diagnostic evaluation evidence only; they must not enter normal-only fitting.
2. Predeclare one isolated reference-preprocessing candidate using rotation
   augmentation, keeping DINOv2 frozen. The authors' implementation supports
   rotated reference images; its agnostic VisA setting enables rotations, while
   its informed setting disables them. Rotation is therefore a justified candidate,
   not a proven remedy. Our current full-data adaptation omits rotations.
3. If the mask audit identifies exclusions, preregister a separate foreground
   ablation. Change one factor at a time; do not combine speculative alterations
   and then attribute improvement to one of them. Reuse the completed baseline.
4. Use training normals for reference fitting. Reserve disjoint validation data
   for choosing the operating policy and checking false alarms. A labeled
   validation set can assess a recall target; normal-only calibration cannot
   certify recall. Keep content duplicates in the same split.
5. Report precision, recall, false-positive rate, F1 and ranking metrics, including
   failures. Existing official test results are already development-exposed;
   further scores on them remain retrospective. Fresh external validation is
   needed for an independent performance claim. Preserve baseline assets and
   activate a new version only after a measured, useful improvement.

No expensive GPU experiment was initiated. Rotation may improve invariance,
have no effect, or reduce sensitivity to some defects. Higher resolution,
instance-aware scoring or a different representation are later candidates if a
small preprocessing study fails; none is claimed to work without measurement.

Sources: [authors' preprocessing configuration](https://github.com/dammsi/AnomalyDINO/blob/main/src/utils.py),
[reference-memory implementation](https://github.com/dammsi/AnomalyDINO/blob/main/src/detection.py).
