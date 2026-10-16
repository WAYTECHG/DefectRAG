# Reconstruction anomaly detection
Anomalib Dinomaly uses frozen DINOv2 encoder representations and trains a bottleneck and decoder on normal images. Reconstruction differences support anomaly scoring and spatial localization. Its documented backbone interface uses DINOv2 variants. This does not establish an interchangeable DINOv3 adapter.

# Interpretation
A feature reconstruction discrepancy indicates departure from learned normal appearance. Evaluation on labelled images is required to measure its usefulness. A spatial anomaly map alone does not establish a named physical defect or a manufacturing root cause. DefectRAG's compact nearest-normal fallback uses cosine patch distances rather than Dinomaly's reconstruction decoder, so published Dinomaly benchmark numbers do not describe this application.
