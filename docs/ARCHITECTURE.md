# Architecture

```mermaid
flowchart TD
    UI[React + Vite dashboard] -->|Image / category / batch| API[FastAPI local API]
    API --> VALID[Validate image and size]
    VALID --> DINO[Frozen DINOv3 ViT-S/16]
    DINO --> BANK[Category normal patch bank]
    BANK --> SCORE[Cosine distance / calibrated threshold / heatmap]
    SCORE --> DB[(SQLite inspections and artifacts)]
    DB --> UI
    UI -->|Question + saved inspection ID| GRAPH[LangGraph workflow]
    GRAPH --> SCOPE[Intent and document applicability checks]
    SCOPE --> RET[LangChain retriever]
    KB[Attributed source documents] --> LOAD[LangChain loader + chunking]
    LOAD --> EMB[Local BGE embeddings]
    EMB --> INDEX[(Persistent knowledge index)]
    RET --> INDEX
    RET --> QWEN[Local Ollama / Qwen]
    QWEN --> CHECK[Schema / source ID / exact quote validation]
    CHECK -->|Cited answer or explicit fallback| DB
    SCOPE -->|Unsupported claim| ABSTAIN[Abstain]
    ABSTAIN --> UI
    CHECK --> UI
```

`Detector` serializes inference and loads assets lazily. A failed model call does
not create a successful inspection. SQLite transactions store the inspection and
its local alert; conversation turns are stored together. `InspectionRepository`
defines the persistence boundary for a future isolated cloud implementation.

Training/fitting and final evaluation run outside request handling. The application
does not refit models on startup or use newly uploaded images to alter thresholds.
Knowledge fingerprints bind vectors and conversation context to source/embedding
versions. Image measurements remain separate from general documentation.

This is a local single-user deployment. Static public hosting alone cannot execute
the Python detector; a separate secured inference service is required. No model
weights, credentials or private histories are sent to an external AI API.
