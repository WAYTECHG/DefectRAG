# Model card: DefectRAG visual detector (profile `dinov2_tuned_v1`)

Version of 2026-11-07. This card describes the model that scores inspection photos in the DefectRAG dashboard. Every
number comes from files in this repository (`results/tuned_deployment_evaluation.json`, `results/mvtec_eval.json`,
`docs/ENCODER_DIAGNOSTIC.md`, `docs/MVTEC_EVALUATION.md`).

## Model details

* **What it is:** a nearest-neighbour anomaly detector. It compares the patch features of a photo with a memory of patch
  features from normal photos of the same product. A photo whose patches have no close normal match gets a high
  *difference score*. It is not a classifier: it does not name defects and it does not output a probability.
* **Encoder:** DINOv2 ViT-S/14 (22 M parameters), a modified copy of `facebook/dinov2-small` (Apache-2.0). The last 4 of
  12 transformer blocks and the final layer norm were fine-tuned (details below); the other blocks are unchanged.
  Stored in half precision (44 MB) in `models/encoder_dinov2_tuned/`, with a receipt of the base revision and hashes.
* **Memory (one per product):** 32,768 patch vectors of 384 numbers each (25 MB), chosen by greedy farthest-point
  selection (a PatchCore-style coreset) from all patches of the product's normal training photos.
* **Scoring:** short image edge resized to 448 px, 14 px patches; cosine distance to the nearest memory patch; an
  unsupervised PCA step keeps foreground patches; the image score is the mean of the largest 1% of foreground patch
  distances. A per-patch map gives the highlighted-areas picture.
* **Decision:** one threshold per product, all set by the same rule (below), plus a ±5% "closer look" band around it.
* **Code:** `backend/highres.py` (scoring), `scripts/encoder_finetune.py` (fine-tune), `scripts/build_tuned_profile.py`
  and `scripts/activate_tuned.py` (banks, thresholds, cards). The previous profiles (frozen encoder, random-sample banks;
  and the first DINOv3 prototype) stay installed and can be selected again.
* **Author and licence:** the project owner. Application code is MIT. The modified encoder keeps the Apache-2.0 licence of
  the base model and is not an official Meta release.

## Intended use

* A **screening aid** for the 12 VisA product categories (PCB 1–4, capsules, candle, cashew, chewing gum, fryum, pipe
  fryum, macaroni 1–2) inside the dashboard: staff pick the product, add a photo, read the verdict and the highlighted
  areas, and decide. Staff review is part of the design (verdicts Good / Closer look / Unusual).
* Study and demonstration of normal-image-only anomaly detection and of its evaluation.

**Out of scope:** products outside the 12 categories; photos taken under other lighting, camera or pose; automatic
rejection or release of real goods without a person; safety-critical decisions; naming or classifying defects;
reading the score as a percentage chance of a defect. The product category is chosen by the operator and is **not**
verified by the model.

## Training and calibration data

* **Source:** the official VisA training split (Zou et al., ECCV 2022, CC BY 4.0), normal images only.
* **Per product:** 810 photos fit the memory and the fine-tune; 90 further normal photos (every tenth by content hash)
  are held out and used only to set the threshold. No anomalous photo and no mask is used for training, memory or
  thresholds.
* **Fine-tune:** the encoder saw only synthetic defects painted on those normal photos: irregular bites out of an
  object's edge with a dark rim, missing pieces, blended textures from another photo, stains and scratches, 1–3 per
  image, 20% of images left clean. A small head learned to mark the changed patches, and a consistency loss (weight 2.0)
  kept the features of untouched patches close to the original encoder. 2,500 steps, batch 8, AdamW (1e-5 for the
  encoder, 1e-3 for the head), bf16, about 22 minutes on one laptop GPU (mostly CPU time spent drawing the synthetic defects). One shared encoder for all 12 products. The head is
  discarded after training; only the encoder is used.
* **Thresholds:** one rule for every product: the 95th percentile of its 90 held-out normal scores (about 5 in 100
  normal reference photos are flagged). Earlier versions used a more sensitive 80th percentile for macaroni 1 and 2
  because their defects were missed too often; it was removed on 2026-11-07 so that every product, and every
  comparison in this repository, uses the same rule.

## Evaluation

Official VisA test assignments, 200 images per product (100 normal, 100 anomalous), 2,400 in total. **The test images
were already seen during development, so these figures are descriptive, not an independent validation.** Several
variants were scored on the same images, which favours the one that was chosen.

| product | image AUROC, previous profile -> deployed | pixel AUROC | recall | false alarms | threshold |
| --- | ---: | ---: | ---: | ---: | --- |
| pcb1 | 0.960 -> **0.979** | 0.995 | 94% | 9% | q95 |
| capsules | 0.968 -> **0.978** | 0.978 | 96% | 7% | q95 |
| cashew | 0.961 -> **0.974** | 0.997 | 94% | 8% | q95 |
| candle | 0.941 -> **0.960** | 0.992 | 86% | 9% | q95 |
| chewinggum | 0.989 -> **0.992** | 0.996 | 96% | 6% | q95 |
| fryum | 0.992 -> **0.990** | 0.981 | 96% | 4% | q95 |
| macaroni1 | 0.909 -> **0.947** | 0.996 | 75% | 4% | q95 |
| macaroni2 | 0.845 -> **0.897** | 0.994 | 73% | 9% | q95 |
| pcb2 | 0.906 -> **0.958** | 0.972 | 87% | 10% | q95 |
| pcb3 | 0.955 -> **0.993** | 0.980 | 98% | 13% | q95 |
| pcb4 | 0.987 -> **0.995** | 0.983 | 95% | 2% | q95 |
| pipe_fryum | 0.989 -> **0.991** | 0.993 | 99% | 4% | q95 |
| **macro mean** | 0.950 -> **0.971** | 0.988 | 90.7% | 7.0% | |

For the same rule, the previous profile caught 83.8% with 7.4% false alarms. Average precision 0.976, F1 0.921. Pixel AUROC uses masks resized to 224 x 224 and is reported for localisation only.

### What each change contributed (VisA, mean image AUROC over 12 products)

| step | mean AUROC | three weakest products | macaroni2 |
| --- | ---: | ---: | ---: |
| frozen DINOv2 + random-sample memory (starting point) | 0.950 | 0.887 | 0.845 |
| + farthest-point coreset (same memory size) | 0.969 | 0.925 | 0.880 |
| + fine-tuned encoder (deployed) | 0.971 | 0.934 | 0.897 |

The coreset explains most of the gain. The fine-tune adds a small gain that is clear in three products (macaroni 1,
macaroni 2, pcb1) and not distinguishable from zero in the others. Tried and rejected, with numbers, in
`docs/ENCODER_DIAGNOSTIC.md`: rotated training views, DINOv3 features (alone and fused), position-aware and global
distances, and a fine-tune with simpler synthetic defects.

### Transfer check on MVTec AD (one run, protocol fixed in advance)

15 products, 1,725 test images, banks built from MVTec's own normals, encoder not trained on MVTec (`docs/MVTEC_EVALUATION.md`):

| macro mean over 15 products | random-sample memory | coreset memory | coreset + fine-tuned encoder |
| --- | ---: | ---: | ---: |
| image AUROC | 0.986 | **0.992** | **0.992** |

The coreset transfers (clear gains in cable, pill, screw; no product clearly worse). The fine-tune shows no measurable
gain there (one product clearly better, one clearly worse; macro pixel AUROC 0.881 against 0.888), so its small VisA
gain is not confirmed outside VisA.

## Limitations and known failure modes

* **Small structural defects remain the weak spot:** edge chips on macaroni (about 0.8 AUROC for that defect type) and
  missing parts on pcb2. Subtle defects whose patches each look normal can be missed.
* **Macaroni 1 and 2 catch the fewest defects** under the one rule (75% and 73%, against 86% to 99% for the other
  products). A more sensitive limit (80th percentile) would catch about 91% and 90% but flag 20% and 27% of normal
  photos; it is not the default.
* **Thresholds are not guarantees.** They come from 90 normal photos per product; a q95 threshold does not mean a 5%
  false-alarm rate on new photos. The "closer look" band is a heuristic, not a calibrated confidence.
* **Foreground heuristic:** the PCA rule assumes one object on a fairly plain background. On texture surfaces it can
  zero out regions where a defect lies, which is why pixel AUROC was only 0.56 to 0.74 for leather, tile and wood on
  MVTec AD even though their image AUROC was about 1.0. Highlighted areas are interpolated patch distances, not a
  segmentation, and stronger colours do not mean a more serious defect.
* **Distribution shift:** only VisA-style photos were tested. A different camera, lighting, background or product
  variant can raise the scores of normal photos. A photo of the wrong product category gives unreliable output.
* **Evidence quality:** test images were seen in development; the MVTec check used a third-party mirror copy and few
  held-out normals per product; no external validation on real production photos was done.
* **Fine-tune scope:** trained on VisA only; its benefit beyond VisA is unproven (see above).

## How to use

The dashboard does this automatically. In code: `backend.highres.TunedDetector(Settings()).predict(PIL_image, "pcb1")`
returns the verdict, score, threshold, model ID (`dinov2-tuned-pcb1-v1`), the bank checksum and a heatmap. Profile
selection and rollback: `DEFECTRAG_PROFILE=dinov2_highres_v1` (or `legacy`) locally, `DEFECTRAG_SPACE_PROFILE` on the
hosted Space.

## Citations and licences

* Oquab et al., *DINOv2: Learning Robust Visual Features without Supervision*, TMLR 2024. Apache-2.0.
* Damm, Laszkiewicz, Lederer, Fischer, *AnomalyDINO*, WACV 2025 (inspiration for the memory and foreground steps; not a reproduction).
* Roth et al., *Towards Total Recall in Industrial Anomaly Detection* (PatchCore), CVPR 2022 (coreset idea).
* Zou et al., *SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection and Segmentation* (VisA), ECCV 2022. CC BY 4.0.
* Bergmann et al., *MVTec AD*, CVPR 2019 and IJCV 2021. CC BY-NC-SA 4.0; used only for the transfer check.
* Third-party notices: `docs/THIRD_PARTY_NOTICES.md`.
