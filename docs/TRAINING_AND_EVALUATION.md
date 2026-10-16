# DefectRAG: understand and reproduce the model process

This app uses a frozen pretrained DINOv3 ViT-S/16 encoder plus a fitted normal
patch memory. It does **not** fine-tune DINOv3, train a YOLO detector, or implement
Dinomaly. A pretrained/frozen pipeline is a legitimate anomaly-detection approach;
the exact architecture and protocol must be named honestly.

## Two experiments, preserved separately

| Setting | Compact application baseline | Official-split benchmark |
|---|---|---|
| Training images | 64 normal images per category | Every normal in official `1cls.csv` training partition |
| Encoder | Frozen DINOv3 ViT-S/16 | Same bundled encoder and preprocessing |
| Memory | Up to 8,192 normal patch vectors | Up to 8,192 patch vectors sampled across all official training normals |
| Test | Modified official test; 20 anomalies reserved for validation | Entire original official test: normal test images and all 100 anomalies per category |
| Threshold | Max-F1 on separate 32-normal/20-anomalous validation | Not needed for benchmark AUROC/AU-PR |
| Randomness | Seed 42 | Seeds 42, 43, 44; report all runs and mean/sample standard deviation |
| Pixel evaluation | 64×64 maps, including normals | 224×224 maps, including normals; reference VisA 200-threshold integration |
| Storage | `models/`, `results/evaluation.json` | `experiments/official_visa_v1/`; summary `results/official_evaluation.json` |

The supplied `split_csv/1cls.csv` is authoritative. VisA one-class training uses
about 90% of normal images, while the remaining normals plus all anomalies are
test data. This is not a random 70/20/10 split over all images. The exact number
of normal images differs by product.

## Operational calibration is a separate profile

Each official experiment also fits a separate fourth bank. Seed 42 holds out
10% of the **official training normals**, grouping by image content hash so
duplicates cannot straddle fitting and calibration. The remaining training
normals fit that bank. The deployment threshold is the maximum held-out normal
score, following a documented normal-only calibration rule. No test anomaly or
ground-truth test mask chooses it. The ±5% review band remains an operational
heuristic, not statistical confidence. This profile is saved separately and
is **not silently substituted for the current app detector**.

Strict full-training benchmark results and the holdout calibration profile must
not be mixed in one performance claim. They use different normal reference banks.

## Settings you can understand

| Parameter | Value | Purpose |
|---|---|---|
| Learning rate / optimizer / epochs | Not applicable | No gradient updates occur |
| Encoder weights | Bundled DINOv3 ViT-S/16 | Fixed feature extractor |
| Input preprocessing | Bundled processor; default 224 input | Fixed before evaluation |
| Spatial features | 14×14 patch grid | Coarse anomaly localization |
| Normal memory limit | 8,192 patch features per bank | Bounds storage/inference cost |
| Patch distance | Cosine distance to nearest normal feature | Measures deviation from normal appearance |
| Image score | Mean of highest 1% patch distances | Fixed scoring rule |
| Benchmark seeds | 42, 43, 44 | Measures random-bank variability |
| Ground-truth masks | Evaluation only | Compare localization against true anomaly pixels |

## Run or resume the already configured official experiment

The current workstation runtime is already installed; do not reinstall the
original environment or rerun a completed experiment merely to start the app.
In PowerShell, from the workspace source directory:

```powershell
$env:PYTHONPATH="C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\.test-deps"
$env:USE_TF="0"
& "C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe" -u -m scripts.benchmark_official --dataset "C:\Users\User\Downloads\VisA_20220922"
```

Completed category receipts are hash-checked and skipped. Each category saves
its split manifest, four banks, normal calibration, predictions and metrics.
Do not modify the protocol or tune settings from final-test results. Use a new
versioned output directory for a genuinely new experiment and state its settings
before looking at test outcomes.

## What constitutes an honest performance report

- Include all 12 categories and their equal-weight macro average.
- Image AUROC and **trapezoidal AU-PR** match the official classification metric
  definitions. Average precision is also provided, separately labelled.
- Pixel AUROC/AU-PR follows the official sampled-threshold integration. The
  224×224 evaluation map size and coarse 14×14 source grid are explicit adaptations.
- Masks are nearest-neighbour resized; normal images receive all-zero masks.
- Report mean and sample standard deviation over all three fixed seeds; do not
  choose whichever run performed best.
- These are retrospective benchmark results: some test identities/results were
  seen during earlier development. They are not a new untouched external test.
- A matching dataset split does not make this a reproduction of Dinomaly or
  AnomalyDINO, nor establish factory acceptance or medical/product safety.

## If you later want actual fine-tuning

That is a separate model experiment. A trainable reconstruction model such as
Dinomaly has encoder/decoder, optimizer, learning-rate, batch-size and training
duration settings; this memory-bank implementation does not. The existing
`scripts/train_anomalib.py` is an **unverified legacy prototype**, uses the old
modified split and is not the official benchmark recipe. Do not use it to claim
the current 12-category result or automatically replace the application banks.
Start from the chosen implementation's supported backbone and published recipe,
profile VRAM, freeze validation rules, and evaluate the complete official test set.
No training recipe guarantees improved macaroni2 performance.

## Primary references

- VisA protocol, Section 4.2: https://arxiv.org/html/2207.14315
- Official assignments/preparation: https://github.com/amazon-science/spot-diff
- Reference metric implementation: https://github.com/amazon-science/spot-diff/blob/main/utils/metrics.py
- Related frozen-feature research (different method/backbone): https://arxiv.org/html/2405.14529v2
- Normal-only threshold handling: https://anomalib.readthedocs.io/en/latest/markdown/guides/how_to/models/post_processor.html
