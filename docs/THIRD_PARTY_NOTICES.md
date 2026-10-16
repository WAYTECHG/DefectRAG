# Third-party assets

| Asset | Attribution / source | Included terms |
|---|---|---|
| DINOv3 ViT-S/16 weights and processor/config | Meta, facebook/dinov3-vits16-pretrain-lvd1689m | `models/DINOV3-LICENSE.md`; DINOv3 License, not the project MIT license |
| BGE small English v1.5 embeddings | BAAI / FlagEmbedding, staoxiao | `models/BGE-LICENSE.txt`, MIT; original model card under `models/embedding/README.md` |
| VisA sample previews and normal-bank inputs | Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang, Onkar Dabeer; Amazon Science; ECCV 2022 | CC BY 4.0; previews resized and JPEG-encoded; full dataset excluded |
| React / React DOM / Scheduler / Lucide | Their respective upstream contributors | `docs/FRONTEND_LICENSES.txt`, copied from the installed packages |
| Python dependencies | PyTorch, Transformers, sentence-transformers, FastAPI, LangChain, LangGraph and others | Installed separately by the user; see upstream packages for their licenses |

VisA: [official source](https://github.com/amazon-science/spot-diff),
[CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/).
Paper: *SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection
and Segmentation*, Zou et al., ECCV 2022. Original relative image identities and
content checksums are preserved in the split manifests; the gallery uses resized
derivatives. Fitted memory banks contain derived normal patch embeddings.

DINOv3: [official repository and license](https://github.com/facebookresearch/dinov3).
This application uses the DINOv3 materials and acknowledges Meta's work. Preserve
the included agreement when redistributing those materials. The project MIT license
does not override restrictions or terms applying to the model materials.

BGE: [model source](https://huggingface.co/BAAI/bge-small-en-v1.5),
[FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding).

Knowledge passages are short attributed summaries and project-authored screening
policy, not copied factory SOPs. `knowledge/sources.json` records source URLs and
scope. Anomalib documentation describes a comparison method; no Anomalib model
weights or published benchmark performance are represented as the shipped detector.

Qwen is an optional separately installed Ollama model and is not bundled. No raw
user history, credentials, full dataset, training cache or dependency environment
is included in the release ZIP.
