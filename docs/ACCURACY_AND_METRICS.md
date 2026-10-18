# Accuracy profile and overall metrics

The previous baseline remains preserved. The new experiment is a custom adaptation
inspired by AnomalyDINO (WACV 2025), not a paper reproduction or Dinomaly model.
It changes representation/preprocessing rather than fine-tuning network weights.

| Setting | Original official benchmark | DINOv2 candidate |
|---|---|---|
| Encoder | DINOv3 Small/16 | DINOv2 Small/14 |
| Input | 224×224 | Short edge 448, preserve aspect, crop to patch multiple 14 |
| Typical grid | 14×14 | 32×48 for a 3:2 image |
| Foreground | No filtering | PCA component threshold 10, center orientation, 2D morphology |
| Memory | 8,192 uniformly sampled patches | Up to 32,768 patches, balanced across normal images and foreground/background |
| Seeds | 42,43,44 | 42,43,44, all reported |
| Benchmark training | All official training normals | Same |
| Test | All official test identities | Same |
| Defect masks | Pixel evaluation only | Pixel evaluation only; never used for foreground heuristic |
| Operational threshold | Separate normal-only holdout | Separate content-grouped 10% training-normal holdout, maximum score |

The candidate uses the official train/test assignments. Its memory sampling,
full-data setting, Hugging Face encoder, 2D morphology and no-rotation setting are
explicit differences from the paper's default few-shot recipe. Settings are frozen
in experiments/dinov2_highres_v1/protocol.json before scoring the test set.
Earlier test results informed this development effort: any comparison or release
selection is retrospective, not an untouched external evaluation. No best-seed
selection or per-category switching is performed. Report every category.

## Official overall metrics first

Use **mean image-level AUROC (I-AUROC) across all 12 categories** as the headline
anomaly-detection number, with **mean image AU-PR** beside it. The official VisA
paper reports both and favors AU-PR for imbalanced data. Localization uses
mean pixel AUROC and pixel AU-PR separately; no single official score combines
image detection and localization. See Section 4.2 of the VisA paper:
https://arxiv.org/html/2207.14315 .

## Supplementary AP / mAP

AP is not exclusive to YOLO, but YOLO box-matching mAP is a different evaluation.
AP summaries here are supporting metrics, not a substitute for the official
VisA AUROC/AU-PR pair.

For each product, treat anomalous images as positive and normal images as negative.
Rank them by anomaly score and compute average precision (AP). **Image mAP** is
the arithmetic mean of those 12 AP values. Each product has equal weight. With 3
fixed seeds, report the mean and sample standard deviation of the resulting macro
metrics as well. AP depends on the prevalence of anomalous examples; compare
methods using the same test identities rather than mixing different splits.

**Mean image AUROC** averages the 12 category AUROCs. **Pixel mAP** averages each
category's pixel AP, including normal images' all-zero masks, and measures
localization. **Mean image AU-PR** uses trapezoidal integration; AP uses the
non-interpolated precision-recall weighting. They are different metrics.

This is not YOLO mAP@0.5 or mAP@0.5:0.95: this application does not predict boxes
or named defect classes, so there is no box IoU threshold. A high image mAP does
not establish fine-grained localization or factory acceptance.

The preserved original official report has mean image AUROC 85.38%, image mAP 86.58%,
mean image AU-PR 86.47% and pixel mAP 33.30%. The new measured report is saved only
after all 12 categories finish. The dashboard compares them explicitly.

## Resume without repeating completed work

Use the already installed interpreter and PYTHONPATH from the main README:

```powershell
python -u -m scripts.benchmark_highres --dataset "C:\Users\User\Downloads\VisA_20220922"
```

Per-image feature caches, per-image test predictions/maps and completed category
receipts are saved. Completed categories and cached images are skipped. Do not
change protocol.json or reuse its output directory for different settings. New
settings require a separate versioned experiment. Original models and release
archives remain intact.

Activation is separate from benchmarking. The installer verifies completion,
compares retrospective macro AUROC and mAP, installs one fixed seed 42 operational
profile under models/highres and writes PROFILE.json only after all 12 cards exist.
The app uses it automatically only if installed and active. Force the original
model with DEFECTRAG_PROFILE=legacy before restarting. Historical inspections
retain their original scores/model IDs and are not recomputed.

## References

- https://arxiv.org/html/2405.14529v2
- https://github.com/dammsi/AnomalyDINO
- https://huggingface.co/facebook/dinov2-small
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html

The Model performance page also reports precision, recall and F1 at the normal-calibrated operational threshold. Better AUROC/mAP does not guarantee every operating-point metric improves; threshold policy and review-band behavior must be considered separately.
