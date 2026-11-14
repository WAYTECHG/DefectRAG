# Where the frozen DINOv2 detector fails (diagnostic, 2026-11-06)

Reproduce: `python -m scripts.diagnose_encoder` (read-only; no GPU, no model, nothing in the app changes;
writes `results/encoder_diagnostic.json`). It reads the cached per-image test scores and held-out normal scores in
`experiments/dinov2_highres_v1/<category>/`, the VisA annotation text (defect type) and the VisA masks (defect size).

**Counts:** "810 fit normals", "90 held-out normals" and "200 test images" below are the sizes of the larger categories.
Capsules, cashew, chewing gum, fryum and pipe fryum have 405-487 fit normals, 45-55 held-out normals and 150-160 test
images. All 12: 7,789 fit normals, 870 held-out normals and 2,162 test images (962 normal, 1,200 anomalous).

**Caveat:** these test images were already seen during development, so every figure is descriptive,
not a fresh validation. Bank-to-bank AUROC spread (4 banks per category) is 0.003-0.023, so differences smaller than
about 0.02 are noise. Groups of 10-30 images give wide uncertainty.

## Per category (deployed bank)

AUROC does not depend on the threshold. The q95 columns put every category on the same policy; "deployed" is what the
app uses (macaroni1/2 on q80, everything else q95). The script's numbers reproduce the saved deployment evaluation.

| Category | AUROC | q95 recall | q95 false alarms | Deployed policy: recall / false alarms |
|---|---:|---:|---:|---|
| macaroni2 | 0.845 | 48% | 7% | q80: 80% / 28% |
| pcb2 | 0.906 | 84% | 12% | q95 (same) |
| macaroni1 | 0.909 | 57% | 1% | q80: 85% / 24% |
| candle | 0.941 | 87% | 12% | q95 (same) |
| pcb3 | 0.955 | 87% | 9% | q95 (same) |
| pcb1 | 0.960 | 86% | 8% | q95 (same) |
| cashew | 0.961 | 90% | 18% | q95 (same) |
| capsules | 0.968 | 82% | 8% | q95 (same) |
| pcb4 | 0.987 | 96% | 4% | q95 (same) |
| chewinggum | 0.989 | 96% | 4% | q95 (same) |
| pipe_fryum | 0.989 | 99% | 4% | q95 (same) |
| fryum | 0.992 | 94% | 2% | q95 (same) |

## What the misses have in common

* **Not defect size.** Small defects are found as often as large ones (macaroni1: small thirds AUROC 0.95, large 0.89).
* **Defect type.** The weak groups are defects where something is missing or the outline changes:

| Category | Defect type | n | AUROC | Found at deployed threshold |
|---|---|---:|---:|---:|
| macaroni1 | chip around edge and corner | 25 | 0.72 | 44% |
| macaroni2 | small chip around edge | 30 | 0.71 | 57% |
| pcb2 | missing (component) | 19 | 0.78 | 53% |
| pcb3 | missing (component) | 20 | 0.89 | 65% |
| candle | weird candle wick | 11 | 0.80 | 45% |

  Texture and colour defects (scratches, cracks, colour spots, foreign particles, melt) score 0.89-1.00 in the same
  categories.
* Reading: the detector compares each small patch with normal patches. A patch of an edge chip or of a bare board
  position can still look normal on its own; the fault is in the shape or in what is absent. This is a hypothesis from
  the pattern above, not yet tested.

## What this means for the next experiments

Threshold changes cannot fix these (AUROC is unchanged). Candidates, all to be measured on the same 200 test images with
fixed rules chosen before looking at the results:

1. Position-aware matching for aligned objects (PCBs: compare with normal patches at the same place).
2. A global image-level distance (CLS token) added to the patch score (hybrid).
3. A coarser second scale for more context (hybrid).
4. Rotation-augmented reference banks (already named as a candidate in `MACARONI_RECALL_REVIEW.md`).
5. A second encoder (the retained DINOv3) fused with DINOv2 (hybrid).
6. Fine-tuning DINOv2 with synthetic defects (chips, missing parts), only if 1-5 leave the gap.

Claim an improvement only if it clears the 0.02 noise level and does not hurt the strong categories.

## Round 2: candidates measured (2026-11-06)

Reproduce: `python -m scripts.encoder_candidates` (GPU, about 36 minutes for all 12 categories; writes per-image scores
to `experiments/dinov2_candidates/`), then `python -m scripts.encoder_candidates_report` (CPU; `--anchor full` compares
against the full bank). The harness reproduces the app's saved scores exactly (largest difference 0.00000), so
differences come from the candidate, not from a different pipeline. Rules were fixed in the code before any result:
standardise with the 90 held-out normals only, a fixed list of 10 averaged fusions, paired bootstrap 95% intervals,
thresholds from held-out normals only. Same development-exposed 200 test images, so still descriptive.

**Finding 1: the deployed bank is a 4% sample.** It keeps 48 foreground + 16 other patches per training image, capped at
32,768 patches (the full set is 0.44-1.35 million per category). Using every patch of the 810 fit normals as the bank
("full") raised AUROC in all 12 categories and lowered none; no training:

| Category | Deployed | Full bank |  | Category | Deployed | Full bank |
|---|---:|---:|---|---|---:|---:|
| macaroni2 | 0.845 | 0.885 |  | pcb1 | 0.960 | 0.974 |
| pcb2 | 0.906 | 0.958 |  | capsules | 0.968 | 0.976 |
| macaroni1 | 0.909 | 0.934 |  | pcb4 | 0.987 | 0.996 |
| candle | 0.941 | 0.960 |  | chewinggum | 0.989 | 0.991 |
| pcb3 | 0.955 | 0.980 |  | pipe_fryum | 0.989 | 0.992 |
| cashew | 0.961 | 0.976 |  | fryum | 0.992 | 0.993 |

Mean AUROC 0.950 -> 0.968. The 95% interval of the difference stays above zero in 7 of 12 categories (candle, cashew,
macaroni1, macaroni2, pcb1, pcb2, pcb3) and in none is it below zero.

**Finding 2: hybrids add little on top of the full bank.** Position-aware matching (mean 0.964), foreground-only full
bank (0.965) and the best fusions (full+coarse+pos 0.969, full+pos 0.968, full+coarse+cls 0.968) are all within 0.001
of the full bank alone on average. Against the full bank, a few categories gain (candle, pcb1, cashew) and a few lose
(macaroni1/2 with global features), so any per-category pick would be tuning on the test set. Global distances alone
are much worse (class token 0.868, pooled 0.844, half-resolution 0.923 mean AUROC).

**Finding 3: the structural defects are only partly fixed.** AUROC of the weak defect types, deployed -> full bank:
macaroni1 edge chip 0.72 -> 0.78, macaroni2 edge chip 0.71 -> 0.77, pcb2 missing 0.78 -> 0.87, pcb3 missing 0.89 ->
0.94, candle wick 0.80 -> 0.82. Chips stay the weakest (about 0.77). No candidate here fixes them.

**Operating points, q95 for every category** (recall / false alarms, deployed -> full bank; held-out normals are only
90 images, so a single rate moves by about 1 point per image and AUROC is the steadier number):
macaroni1 57% / 1% -> 69% / 0%; macaroni2 48% / 7% -> 55% / 9%; pcb2 84% / 12% -> 87% / 9%; cashew 90% / 18% -> 91% /
8%. At the deployed q80 for macaroni: macaroni1 85% / 24% -> 90% / 25%; macaroni2 80% / 28% -> 90% / 33%.

**Cost of the full bank:** 0.44-1.35 million patches per category, 8.2 GB in half precision for all 12 (the deployed
banks total about 0.3 GB). Too large to ship as is. Foreground-only is about 3.9 GB.

**What follows:** a bank-size study (larger random caps per image, then a coreset) to find the smallest bank that keeps
most of the gain; only then touch the app. Any fine-tune must now beat the full-bank baseline (mean 0.968; macaroni2
0.885), not the deployed one.

## Round 3: how small can the bank be, plus rotation and DINOv3 (2026-11-06)

All 12 categories, same test images, same rules as round 2 (scores standardised with the 90 held-out normals only,
paired bootstrap 95% intervals). The round-3 harness reproduces the app's saved scores exactly (maximum difference
0.00000). Descriptive only: the test images were already seen during development. Raw numbers:
`results/encoder_banks.json`.

| bank | patches / category | MB (all 12, fp16) | mean AUROC | gain kept | weak 3 (macaroni1/2, pcb2) | categories clearly worse than full |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deployed (random sample) | 30,363 | 280 | 0.950 | 0% | 0.887 | 0 |
| 128 random patches per image | 83,083 | 766 | 0.959 | 51% | 0.905 | 4 |
| 256 random patches per image | 166,165 | 1,531 | 0.962 | 69% | 0.910 | 2 |
| 512 random patches per image | 331,373 | 3,054 | 0.965 | 86% | 0.917 | 2 |
| **coreset 32,768** | 32,768 | 302 | 0.969 | 104% | 0.925 | 0 |
| **coreset 65,536** | 65,536 | 604 | 0.969 | 108% | 0.928 | 0 |
| coreset 98,304 | 98,304 | 906 | 0.969 | 108% | 0.928 | 0 |
| every patch (full) | 888,853 | 8,192 | 0.968 | 100% | 0.926 | 0 |

**Finding 4: a greedy farthest-point coreset keeps the whole gain at the deployed bank size.** A 32,768-patch coreset
(the same memory as today's bank, 302 MB for all 12 categories) reaches mean AUROC 0.969, the same as the 8.2 GB full
bank (0.968), and is never clearly worse than it in any category. Random sampling cannot do this: even 512 random
patches per image (ten times the size) keeps only 86% of the gain. The coreset keeps the rare, unusual patches that
random sampling drops, and those are what flag a defect. Going from 32k to 65k patches adds nothing measurable
(0.969 to 0.969; weak categories 0.925 to 0.928), so 32,768 is the sensible size: no larger bank, no extra latency.
Deployed -> coreset 32k: candle 0.941 -> 0.960, cashew 0.961 -> 0.978, macaroni1 0.909 -> 0.935, macaroni2 0.845 ->
0.880, pcb1 0.960 -> 0.972, pcb2 0.906 -> 0.959, pcb3 0.955 -> 0.987. No category is clearly worse; pipe_fryum
(0.989 -> 0.989) and fryum are within bank-to-bank noise.

**Finding 5: rotated training views do not help.** Four rotations with 256 patches each (about as large as the full
bank) average 0.960, below the full bank (0.968) and clearly worse in 5 categories. The objects in VisA are
photographed in a fixed orientation, so rotated copies only add patches that never occur at test time.

**Finding 6: DINOv3 is a different kind of detector, not a better one.** Alone it averages 0.928 and collapses on
macaroni2 (0.599) and macaroni1 (0.834), but it is the best single method on candle (0.987 against 0.960; the weird
wick type 0.965 against 0.821), cashew (0.985) and ties on pcb2/pipe_fryum. Averaged with the DINOv2 full bank the
fusion reaches 0.970 against 0.968, a gain inside the noise, and it clearly loses on macaroni2 (0.852 against 0.885).
Only 2 categories gain clearly (candle and cashew) and it needs a second 22M-parameter model online.
Not worth shipping as a general rule; a per-category choice would be tuning on the test images.

**Finding 7: the chip defects are still the limit.** AUROC of the weak types, deployed -> full -> coreset 64k:
macaroni1 chip 0.72 -> 0.78 -> 0.81, macaroni2 chip 0.71 -> 0.77 -> 0.77, pcb2 missing 0.78 -> 0.87 -> 0.87, pcb3
missing 0.89 -> 0.94 -> 0.96. Macaroni2 small chips stay near 0.77 whatever the bank.

**Operating points at q95 for every category** (recall / false alarms, deployed -> coreset 64k): macaroni1 57% / 1% ->
71% / 1%; macaroni2 48% / 7% -> 71% / 12%; pcb2 84% / 12% -> 88% / 10%; cashew 90% / 18% -> 91% / 8%; candle 87% / 12% ->
87% / 9%. At the deployed q80 for macaroni: macaroni1 85% / 24% -> 91% / 22%; macaroni2 80% / 28% -> 89% / 30%.
Macaroni2 at q95 trades recall for false alarms; at the 90 held-out normals a single image moves a rate by about 1 point.

**What follows:** (1) the coreset is the candidate to ship, because it needs no extra model and no extra memory;
changing the app would mean rebuilding the 12 banks with the coreset, re-deriving thresholds from held-out normals
only, checking that the healthy-image rates stay sensible and republishing, which needs your approval. (2) Round 4
(fine-tuning the last DINOv2 blocks with synthetic structural defects) must beat the coreset/full-bank baseline (mean
0.969; macaroni2 0.880-0.885), not the deployed bank, to be worth the extra weights.

## Round 4: fine-tuning the last DINOv2 blocks (2026-11-06)

One configuration, fixed before any result: the last 4 transformer blocks, the final layer norm and a linear head were
trained for 2,500 steps (batch 8, 5.5 minutes on the GPU) to find synthetic structural defects (cut-and-paste, erased
region, edge swap) made from the 810 fit normals per category. A consistency loss kept the features of untouched patches
close to the frozen model. The 90 held-out normals and the 200 test images were never read in training. Every bank was
then rebuilt from the tuned features and scored on the same test images (`scripts.encoder_finetune_report`, raw numbers
in `results/encoder_finetune.json`). The model learned its task (patch accuracy 0.99, consistency loss 0.001-0.002), so
the result below is not a failed training run.

| encoder and bank | mean AUROC | weak 3 (macaroni1/2, pcb2) |
| --- | ---: | ---: |
| frozen, deployed 32k random sample | 0.950 | 0.887 |
| frozen, every patch | 0.968 | 0.926 |
| frozen, coreset 32,768 patches (round 3) | 0.969 | 0.925 |
| **tuned, every patch** | **0.970** | 0.930 |
| tuned, foreground-only full bank | 0.967 | |
| tuned, position-aware | 0.966 | |

**Finding 8: fine-tuning does not clearly help.** Against the frozen full bank, the tuned full bank is +0.002 on
average (0.970 against 0.968). The paired 95% interval of the difference is above zero in 1 of 12 categories (pcb3
0.980 -> 0.987) and below zero in none; in 5 categories the score is lower or equal (capsules 0.976 -> 0.974, cashew
0.976 -> 0.974, fryum 0.993 -> 0.991, pcb4 and pipe_fryum unchanged). That is inside the bank-to-bank noise of 0.003-0.023 measured
earlier, so I do not claim an improvement. The hard defect types move in the right direction but only slightly:
macaroni1 chip 0.782 -> 0.797, macaroni2 chip 0.771 -> 0.788, pcb3 missing 0.935 -> 0.953, candle wick 0.821 -> 0.834,
pcb2 missing 0.866 -> 0.861 (no change). Macaroni2 overall 0.885 -> 0.892.

At the like-for-like q95 threshold for every category, macaroni1 recall is 69% -> 70% (false alarms 0% -> 3%) and
macaroni2 66% against 55% (false alarms 10% against 9%); at the deployed q80, macaroni1 92% / 26% and macaroni2 90% / 31%
against 90% / 25% and 90% / 33%. Those moves are one to three images.

**Why it probably does not help more:** the synthetic defects (pasted squares, flat fills) look unlike a real macaroni
chip, and the frozen features are already close to what the detector needs. The remaining errors are a few subtle chips
whose patches each look like normal macaroni.

**Cost of using it:** a second set of encoder weights (a 44 MB file) and re-deriving banks and
thresholds for the gain of +0.002, which is not distinguishable from zero. Not worth it for this variant; round 4b below
retries with more realistic defects. The tuned weights are kept in `experiments/dinov2_finetune/` and are not part of the app.

### Round 4b: the same fine-tune with more realistic synthetic defects (2026-11-07)

Only the synthetic defects changed (everything else identical to round 4): irregular bites out of the object's edge
with a darker fracture rim, missing pieces, textured blotches blended in from another image, stains and scratches
(`scripts.encoder_finetune --train --realistic`; raw numbers in `results/encoder_finetune_realistic.json`).

| encoder and bank (every patch) | mean AUROC | macaroni1 | macaroni2 | pcb2 |
| --- | ---: | ---: | ---: | ---: |
| frozen | 0.968 | 0.934 | 0.885 | 0.958 |
| tuned, simple defects (round 4) | 0.970 | 0.937 | 0.892 | 0.962 |
| **tuned, realistic defects (4b)** | **0.971** | 0.941 | 0.900 | 0.962 |

Against the frozen full bank the 95% interval is above zero in 3 of 12 categories (macaroni1, macaroni2, pcb1) and below
zero in 1 (cashew 0.976 -> 0.972). Chip defects: macaroni1 0.782 -> 0.808, macaroni2 0.771 -> 0.799 (round 4:
0.797 and 0.788); pcb2 "missing" stays 0.866 -> 0.861. At q95 for every category macaroni2 recall is 55% -> 63% with
false alarms 9% -> 11%; at the deployed q80, macaroni1 90% / 25% -> 93% / 24% and macaroni2 90% / 33% -> 91% / 30%.

Reading it: realistic defects help more than simple ones and the gain sits where the defects were aimed (macaroni edge
chips), but it is small (+0.003 mean AUROC) and cashew gets slightly worse. Two fine-tune variants have now been
scored on the same development-exposed test images, so this is a selected result and not independent confirmation. All
tuned numbers also use a full bank (8 GB); a deployable 32k coreset built from tuned features was not tested.

## Round 5: a deployable coreset built from the fine-tuned encoder (2026-11-07)

Fixed before any result: the realistic-defect encoder from round 4b (the only variant carried forward), a 32,768-patch
farthest-point coreset of all fit-normal patches (the same recipe and size as round 3), the same scoring rule
(`scripts.encoder_tuned_coreset`, `scripts.encoder_tuned_coreset_report`; raw numbers in
`results/encoder_tuned_coreset.json`). Held-out normals and test images were only scored.

| bank (32,768 patches unless stated) | mean AUROC | weak 3 (macaroni1/2, pcb2) | macaroni1 | macaroni2 |
| --- | ---: | ---: | ---: | ---: |
| deployed random sample, frozen encoder | 0.950 | 0.887 | 0.909 | 0.845 |
| coreset, frozen encoder | 0.969 | 0.925 | 0.935 | 0.880 |
| every patch (8 GB), tuned encoder | 0.971 | 0.934 | 0.941 | 0.900 |
| **coreset, tuned encoder** | **0.971** | **0.934** | **0.947** | **0.897** |

**Finding 9: the fine-tune gain survives at the deployable size.** Against the frozen coreset, the tuned coreset is
clearly better in 3 of 12 categories (macaroni1 0.935 -> 0.947, macaroni2 0.880 -> 0.897, pcb1 0.972 -> 0.979) and
clearly worse in none; the mean moves 0.969 -> 0.971. Against what is deployed today: mean 0.950 -> 0.971 and weak
3 0.887 -> 0.934 (macaroni2 0.845 -> 0.897, macaroni1 0.909 -> 0.947), at the same bank size.

Hard defect types, frozen coreset -> tuned coreset: macaroni1 chip 0.777 -> 0.822, macaroni2 chip 0.748 -> 0.785,
pcb3 missing 0.956 -> 0.976, candle wick 0.826 -> 0.827, but pcb2 missing 0.860 -> 0.844 (not clearly different).
Operating points, q95 for every category, frozen coreset -> tuned coreset (recall / false alarms): macaroni1 72% / 1% ->
75% / 4%, macaroni2 63% / 7% -> 73% / 9%, pcb2 90% / 12% -> 87% / 10%, cashew 92% / 4% -> 94% / 8%. At the deployed q80:
macaroni1 89% / 20% -> 91% / 20%, macaroni2 86% / 29% -> 90% / 27%.

Cautions: (1) the gain over the frozen coreset is small (+0.002 mean) and concentrated in the macaroni categories and
pcb1; cashew (0.978 -> 0.974) and fryum (0.996 -> 0.990) are slightly lower, though not clearly. (2) Every number comes
from the same 200 test images per category, already seen in development, and two fine-tune variants were scored on them,
so treat it as descriptive, not as an independent test. (3) Shipping it would replace the frozen encoder by one
fine-tuned on the 12 VisA categories, so the "frozen DINOv2" wording in the README and app has to change.

## Overall conclusion of the detector study

1. **The biggest, safest gain is the bank, not the encoder.** Replacing the deployed random-sample bank with a
   32,768-patch farthest-point coreset of the same frozen DINOv2 features lifts mean AUROC from 0.950 to 0.969 (weak 3:
   0.887 -> 0.925) at the same memory and latency.
2. **A fine-tune adds a small extra gain where it was aimed.** A synthetic-defect fine-tune with simple defects did not
   clearly help (round 4); with realistic edge bites, missing pieces, blotches, stains and scratches it improved the
   macaroni categories and pcb1, and the gain survived at the 32k coreset size (mean 0.971, weak 3 0.934).
3. **Nothing else helped reliably:** rotated views, DINOv3 and fusions with global or position-aware scores.
4. **The limit that remains:** small edge chips on macaroni (about 0.79-0.82 AUROC for the tuned coreset).

Shipping either option (coreset on the frozen encoder, or coreset on the tuned encoder) means rebuilding the 12 deployed
banks, re-deriving thresholds from held-out normals only, checking healthy-image rates, updating the wording, and
republishing the Space. That needs the project owner's approval; nothing in the app, Space or model cards was changed.

## Installed locally as profile dinov2_tuned_v1 (2026-11-07)

Option chosen: the 32,768-patch coreset on the realistic-defect fine-tuned encoder. Built with
`scripts.build_tuned_profile` (encoder folder `models/encoder_dinov2_tuned`, banks `models/highres_tuned`), cards,
manifest and marker written by `scripts.activate_tuned`. Thresholds when first installed: q95 of the 90 held-out normal
scores for every category, q80 for macaroni1/2 (the policy already in use); see "One rule for every product" at the end
of this page for the later change. The previous profile and its files are untouched.

| macro mean, 12 categories | previous profile | tuned profile |
| --- | ---: | ---: |
| image AUROC | 0.950 | 0.971 |
| image average precision | 0.956 | 0.976 |
| recall at the operating threshold | 88.8% | 93.5% |
| false alarms on normal test images | 11.1% | 9.9% |
| pixel AUROC (224) | 0.986 | 0.988 |

Checks: scores computed through the application's own code path equal the saved experiment scores exactly on the GPU
(difference 0) and within 0.0003 on the CPU (the uncertainty band is 5% of the threshold, about 0.005); about 40 ms per
image on the GPU; the full test suite (220 passed, 2 skipped), ruff, mypy and the 274 frontend tests pass. Rollback:
`DEFECTRAG_PROFILE=dinov2_highres_v1` (or `legacy`) locally, `DEFECTRAG_SPACE_PROFILE=dinov2_highres_v1` on the Space,
or delete `models/highres_tuned/PROFILE.json`.

Not done yet (needs the project owner): republish the Space (`deployment/space/publish.py` now includes the new
files), update `scripts/fetch_public_assets.py` to the new Space revision and patterns, then push to GitHub.

## Published to the Hugging Face Space (2026-11-07)

Released as Space commit `0db4e63` (model files + patched server code, `deployment/space/tuned_release.py`), the
dashboard wording as `5c2c018` and the assistant knowledge as `bc6bc66`. Before uploading, the patched Space tree was
rebuilt locally from the live snapshot and booted (12 banks verified, `/api/evaluation` and `/api/models` answered).
After the restart: `/api/evaluation` reports profile `dinov2_tuned_v1` with mean AUROC 0.9711; 24 real inspections on
the live Space (12 categories, one good and one anomalous sample each) returned the expected model ID, bank checksum,
threshold and GPU device, with scores within 0.0003 of the local application and no verdict differences; the assistant
described the profile correctly from the updated knowledge file. Rollback options: see `docs/OPERATIONS.md`.

## Transfer check on MVTec AD (2026-11-07)

A one-shot evaluation on MVTec AD (15 categories, protocol written before scoring: `docs/MVTEC_EVALUATION.md`) tested
whether the VisA findings hold on an unseen benchmark. The coreset bank transferred (macro mean image AUROC 0.986 with
the random-sample bank, 0.992 with the coreset, clear gains in cable, pill and screw, none clearly worse). The
fine-tuned encoder did not add anything measurable (0.992, one category clearly better, one clearly worse, pixel AUROC
slightly lower), so the fine-tune's small VisA gain is not confirmed outside VisA. The coreset is the robust
contribution; the fine-tune is a documented, modest, VisA-specific improvement.

## One rule for every product (2026-11-07)

The q80 setting for Macaroni 1 and 2 made comparisons unfair (those two products were judged more leniently than the
other ten), so the deployed profile now uses the 95th percentile of the held-out normal scores for **every** product
(`TUNED_QUANTILES` in `backend/calibration.py` is empty). Space commit `e3d580c` changed the code rule, the two macaroni
cards and the manifest together (`deployment/space/tuned_thresholds.py`; staged boot test first, rollback saved).
AUROC does not depend on the threshold and is unchanged. At the operating point:

| macro mean, 12 products | previous profile, q95 for all | tuned profile, q95 for all |
| --- | ---: | ---: |
| defects caught (recall) | 83.8% | 90.7% |
| normal photos flagged | 7.4% | 7.0% |

| product | q80 (before) caught / flagged | q95 (now) caught / flagged |
| --- | ---: | ---: |
| macaroni1 | 91% / 20% | 75% / 4% |
| macaroni2 | 90% / 27% | 73% / 9% |

The price of one rule is lower recall on macaroni, the hardest products. A more sensitive limit remains possible by
adding a per-product entry to `TUNED_QUANTILES` and regenerating the cards with `scripts.activate_tuned`.

