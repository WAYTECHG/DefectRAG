# Accuracy upgrade verification — 16 October 2026

The completed candidate is a custom AnomalyDINO-inspired frozen DINOv2 memory
model. It is not weight fine-tuning or an exact reproduction of a published method.
See ACCURACY_RESULTS.md for every product, ACCURACY_AND_METRICS.md for settings,
and results/highres_evaluation.json for all seeds and official metric definitions.

## Completed checks

- All 12 products, three fixed benchmark seeds, 8,659 official train normals and
  the same 2,162 official test images. Completion receipts, splits, calibration,
  predictions and banks saved. No test masks used for fitting.
- 46 Python tests passed: results/software-tests-highres.xml. One third-party
  AnyIO deprecation warning. Six frontend contract tests and both builds passed.
- 24 real API inspections covering normal/anomalous sample derivatives from all
  12 products, verified model IDs/hashes, image/heatmap/report/CSV/history paths.
  These resized sample checks are functional checks, not another accuracy test.
- Five inspection-linked assistant cases passed, including two real Qwen
  explanations, direct measurement answers and unsupported-cause abstention.
  Retrieval excluded documentation about the wrong encoder family.
- CPU inference passed alongside CUDA checks. Full traces are in
  results/highres_application_verification.json. No old latency profile is
  presented as a measured performance profile for the new detector.
- Browser verified 12 completed rows and all four overall metric cards, then
  switched between new and original profiles. Screenshot:
  screenshots/accuracy-benchmark.png. Static provenance/privacy/resource checks
  passed for the 25 original recorded examples; these retain their original
  DINOv3 predictions, clearly labeled separately from the DINOv2 benchmark.
- Original model/evaluation files verified against the earlier all12 archive.
  Private Desktop history is backed up separately and excluded from releases.
  results/highres_preservation.json records this check.

## Practical limits

Mean image AUROC improved from 85.38% to 95.13%. This is a ranking metric,
not classification accuracy. The benchmark is retrospective: earlier test
results informed development, so it is not a fresh untouched external test.
Bank-seed standard deviations are not generalization confidence intervals.

The separate deployment bank uses fixed seed 42 and a normal-only holdout.
Its conservative threshold yields macro precision 97.59%, recall 60.17%, F1
68.63% on the official test. Some anomalous samples receive Good verdicts.
Thresholds were not adjusted after test exposure. Cashew image AUROC regresses
slightly; Cashew and Pipe fryum pixel AP regress. Foreground PCA and pixel maps
remain heuristic localization, not a supervised defect segmentation model.

Supabase has not been provisioned; hosted authentication/RLS/storage remain
unverified. Docker execution, a clean dependency installation and 390px mobile
visuals also remain unverified. No public deployment was performed.

## Recovery and use

DEVELOPMENT_PROGRESS.md and the release receipts identify the latest checkpoint.
Use README.md's existing-computer launch command after restarting the old server.
The active profile is selected from models/highres/PROFILE.json. Set
DEFECTRAG_PROFILE=legacy to use the preserved DINOv3 detector.
No model fitting or frontend rebuilding is required to run the local release.

New archives: DefectRAG-local-accuracy.zip (application),
DefectRAG-static-accuracy.zip (saved-example hosting), and
DefectRAG-highres-benchmark-assets.zip (experimental banks and receipts).
Intermediate feature caches/maps remain in the workspace experiment directory;
the benchmark archive excludes these bulky reproducible caches. Earlier archives
remain intact. Git recovery: development-support/git/DefectRAG-accuracy.bundle.
