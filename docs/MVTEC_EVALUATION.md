# One-shot evaluation on MVTec AD (protocol written before any MVTec score existed)

Written 2026-11-07, before the dataset was scored. Purpose: test whether the changes made on VisA (a farthest-point
coreset memory bank and a DINOv2 fine-tuned on synthetic defects) still help on a benchmark that played no part in
their design. Nothing below is tuned on MVTec; if a result disappoints it is reported as it is.

## Data

* MVTec AD (Bergmann, Fauser, Sattlegger, Steger, CVPR 2019; IJCV 2021), licence CC BY-NC-SA 4.0 (non-commercial use).
* The official site was unreachable from the development machine, so the 15 category folders were downloaded from the
  Hugging Face mirror `foersben/mvtec-ad`, which keeps the original layout (`<category>/train/good`, `test/...`,
  `ground_truth/...`). It is a third-party copy. Its integrity is checked against the published counts before use:
  3,629 training normals, 467 normal and 1,258 anomalous test images, one mask per anomalous image, 15 categories.
* The 15 categories: bottle, cable, capsule, carpet, grid, hazelnut, leather, metal_nut, pill, screw, tile,
  toothbrush, transistor, wood, zipper. Texture categories (carpet, grid, leather, tile, wood) have no object to find
  and may stress the PCA foreground heuristic; it is kept unchanged on purpose.

## Arms (all three fixed now)

| arm | encoder | memory bank |
| --- | --- | --- |
| A, previous recipe | original `facebook/dinov2-small` (`models/encoder_dinov2`) | random sample: up to 48 foreground + 16 other patches per training image, capped at 32,768 patches (seed 42) |
| B, coreset | original encoder | greedy farthest-point coreset of 32,768 patches (seed 42) over all patches of the fit images |
| C, deployed | VisA-fine-tuned encoder (`models/encoder_dinov2_tuned`, never trained on MVTec) | the same 32,768-patch coreset (seed 42) |

Identical for all arms: short edge 448 px, 14-px patches, unit-length features, cosine nearest-neighbour distance,
PCA foreground heuristic exactly as in `backend/highres.py`, image score = mean of the largest 1% of foreground patch
distances. No parameter was changed for MVTec.

## Fit / calibration split

Per category, the training normals are sorted by (content SHA-256, file name); every tenth distinct hash is held out
(about 10%, the VisA rule). The remaining images build the banks; the held-out normals only produce thresholds. The test
images are never used for fitting or thresholds.

## Thresholds and metrics

* Primary metric: image AUROC per category and the macro mean over the 15 categories. Secondary: pixel AUROC at 224x224
  (masks resized with nearest neighbour; normal images count as all-negative), image average precision.
* Operating point: threshold = linear 95th percentile of the held-out normal scores, the same for every category. With
  only 6 to 40 held-out normals per category this is noisy, so AUROC is the headline and recall / false alarms are
  descriptive.
* Differences between arms: paired bootstrap of the AUROC difference (2,000 resamples within normals and within
  anomalies, 95% interval). A difference counts as clear only if its interval excludes zero.

## Rules

1. One run, seed 42. A crash may be resumed; nothing is re-run or adjusted after seeing results.
2. Any deviation from this protocol is written down in the results section with its reason.
3. Claims are limited to what the numbers show: "descriptive, on a mirror copy of MVTec AD, one run".
4. Expected, stated in advance: MVTec AD is close to saturated for frozen DINO-based detectors (about 99% AUROC in the
   literature), so the arms are likely to differ by less than one point. The useful outcome is "does not hurt on an
   unseen benchmark", not a large gain.

## Code check and data handling notes

* `scripts/mvtec_eval.py` was checked with `--smoke` on a 20-image fit subset and 11 test images of `bottle` only to
  confirm that it runs and returns finite scores. That output was deleted and printed no metric; no decision depends
  on it.
* The first attempt to download the mirror stopped silently at the Hugging Face rate limit (1,000 API requests per 5
  minutes) while the downloader reported success. This was caught by the integrity check (file counts against the
  published numbers) before any scoring; the download was resumed with a completeness check until every file was
  present.

## Results (one run, 2026-11-07; no deviation from the protocol)

The data passed the integrity check before scoring (3,629 / 467 / 1,258 images, one mask per anomalous image, 15
categories, all 6,612 files hashed in `experiments/mvtec_manifest.json`). Raw numbers: `results/mvtec_eval.json`;
`scripts/mvtec_report.py` produced the table. The protocol file's hash is stored in every result file.

Image AUROC per category (▲ / ▼ = the paired-bootstrap 95% interval of the difference excludes zero, better / worse):

| category | A random bank, frozen | B coreset, frozen | C coreset, fine-tuned | B vs A | C vs B | C vs A |
| --- | ---: | ---: | ---: | :---: | :---: | :---: |
| bottle | 1.000 | 1.000 | 1.000 | | | |
| cable | 0.961 | 0.984 | 0.993 | ▲ | ▲ | ▲ |
| capsule | 0.958 | 0.966 | 0.967 | | | |
| carpet | 1.000 | 1.000 | 1.000 | | | |
| grid | 1.000 | 1.000 | 1.000 | | | |
| hazelnut | 1.000 | 0.999 | 0.999 | | | |
| leather | 1.000 | 1.000 | 1.000 | | | |
| metal_nut | 1.000 | 1.000 | 1.000 | | | |
| pill | 0.977 | 0.992 | 0.996 | ▲ | | ▲ |
| screw | 0.923 | 0.963 | 0.961 | ▲ | | ▲ |
| tile | 1.000 | 1.000 | 1.000 | | | |
| toothbrush | 1.000 | 1.000 | 1.000 | | | |
| transistor | 0.997 | 1.000 | 1.000 | | | |
| wood | 0.980 | 0.986 | 0.974 | | ▼ | |
| zipper | 0.993 | 0.994 | 0.996 | | | |
| **macro mean** | **0.986** | **0.992** | **0.992** | 3 ▲, 0 ▼ | 1 ▲, 1 ▼ | 3 ▲, 0 ▼ |

Other macro means (A / B / C): image average precision 0.995 / 0.997 / 0.998; pixel AUROC 0.886 / 0.888 / 0.881;
at the q95 threshold, recall 95% / 97% / 97% with false alarms 13% / 17% / 16% (6 to 40 held-out normals per
category, so these rates are noisy; AUROC is the headline).

**What this shows**

1. **The coreset transfers.** Replacing the random-sample bank by the 32,768-patch coreset raises the macro mean
   AUROC from 0.986 to 0.992 on a benchmark it was not designed on, with clear gains in the three categories with fine
   structure (cable 0.961 to 0.984, pill 0.977 to 0.992, screw 0.923 to 0.963) and no category clearly worse. Twelve of
   fifteen categories are at or near 1.000 for every arm, so there is little room for any difference.
2. **The fine-tune shows no measurable gain here.** The VisA-fine-tuned encoder gives the same macro mean as the
   coreset on the original encoder (0.992 against 0.992). It is clearly better in one category (cable 0.984 to 0.993)
   and clearly worse in one (wood 0.986 to 0.974), and its macro pixel AUROC is slightly lower (0.881 against 0.888).
   So the small VisA gain from the fine-tune (round 4b and 5) is not confirmed on an unseen dataset. It does not
   hurt the image-level result on average either.
3. **Pixel localisation is weak on textures, for every arm.** Pixel AUROC is 0.63 (leather), 0.66 (tile) and 0.74
   (wood) although the image AUROC of the same categories is 1.000 or close. The cause is most likely the foreground
   heuristic, which zeroes the map outside the mask and was written for single objects on a plain background. The
   protocol fixed that heuristic in advance, so it was not changed. Published patch-based methods report a pixel AUROC
   of about 0.96 to 0.98 on MVTec AD, so the pixel numbers here should not be compared with the literature.
4. **Limits.** One run on a third-party mirror copy of MVTec AD; thresholds from few held-out normals; the dataset is
   close to saturated; the test images were scored exactly once and nothing was adjusted afterwards.

Citation: Bergmann, Fauser, Sattlegger, Steger. MVTec AD: a comprehensive real-world dataset for unsupervised anomaly
detection. CVPR 2019; and the IJCV 2021 extension. Licence CC BY-NC-SA 4.0 (non-commercial).

