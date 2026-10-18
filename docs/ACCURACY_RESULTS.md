# Measured accuracy comparison

Same official test identities and content hashes. Three fixed seeds, all12 categories. Retrospective development evaluation; no new untouched-test claim.

| Product | Original AUROC | DINOv2 AUROC | Change (pp) | Original AP | DINOv2 AP |
|---|---:|---:|---:|---:|---:|
| pcb1 | 0.8795 | 0.9502 | +7.07 | 0.8549 | 0.9487 |
| capsules | 0.8164 | 0.9693 | +15.29 | 0.8958 | 0.9773 |
| cashew | 0.9691 | 0.9607 | -0.84 | 0.9857 | 0.9823 |
| candle | 0.9166 | 0.9512 | +3.47 | 0.9139 | 0.9554 |
| chewinggum | 0.9610 | 0.9913 | +3.03 | 0.9850 | 0.9961 |
| fryum | 0.8994 | 0.9914 | +9.20 | 0.9510 | 0.9959 |
| macaroni1 | 0.8207 | 0.9119 | +9.12 | 0.7977 | 0.9259 |
| macaroni2 | 0.4827 | 0.8320 | +34.92 | 0.4836 | 0.8328 |
| pcb2 | 0.7951 | 0.9258 | +13.07 | 0.7907 | 0.9315 |
| pcb3 | 0.7983 | 0.9459 | +14.76 | 0.8124 | 0.9584 |
| pcb4 | 0.9368 | 0.9899 | +5.31 | 0.9333 | 0.9898 |
| pipe_fryum | 0.9703 | 0.9959 | +2.55 | 0.9862 | 0.9981 |

| Overall metric | Original | DINOv2 |
|---|---:|---:|
| Mean image AUROC · headline | 85.38% | 95.13% |
| Mean image AU-PR | 86.47% | 95.74% |
| Mean pixel AUROC | 92.96% | 98.60% |
| Mean pixel AU-PR | 33.29% | 43.04% |
| Supplementary mean image AP | 86.58% | 95.77% |
| Supplementary mean pixel AP | 33.30% | 43.05% |

Image AUROC regressions: cashew.
Pixel AP regressions: cashew, pipe_fryum.
mAP here averages anomaly-ranking AP across products; it is not bounding-box mAP@IoU.

The benchmark uses all training normals. The deployed bank is a separate fixed-seed profile with a normal-only calibration holdout; see results/highres_deployment_evaluation.json. Historical inspections keep their original model IDs.
