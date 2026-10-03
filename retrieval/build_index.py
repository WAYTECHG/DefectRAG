from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Configuration
# ============================================================

KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", PROJECT_ROOT / "data" / "knowledge" / "knowledge_base.jsonl"))

INDEX_DIR = Path(os.getenv("INDEX_DIR", PROJECT_ROOT / "retrieval" / "index"))

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")


# ============================================================
# Load documents
# ============================================================

def load_documents() -> list[dict]:

    if not KNOWLEDGE_PATH.exists():
        raise FileNotFoundError(
            f"Knowledge base not found:\n{KNOWLEDGE_PATH}"
        )

    documents = []

    with open(
        KNOWLEDGE_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        for line_number, line in enumerate(
            f,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                document = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line "
                    f"{line_number}: {exc}"
                )

            required_fields = [
                "id",
                "title",
                "text",
            ]

            for field in required_fields:

                if field not in document:
                    raise ValueError(
                        f"Missing '{field}' "
                        f"on line {line_number}"
                    )

            documents.append(document)

    if not documents:
        raise RuntimeError(
            "Knowledge base contains no documents."
        )

    return documents


# ============================================================
# Main
# ============================================================

def build_index(model_name: str = MODEL_NAME, device: str | None = None) -> dict[str, object]:

    print("=" * 80)
    print("BUILDING DEFECTRAG KNOWLEDGE INDEX")
    print("=" * 80)

    documents = load_documents()

    print(
        f"Documents: {len(documents)}"
    )

    print(
        f"Embedding model: {model_name}"
    )

    # --------------------------------------------------------
    # Load Qwen3 embedding model
    # --------------------------------------------------------

    if device is None:
        device = "cuda" if __import__("torch").cuda.is_available() else "cpu"

    print(
        f"Embedding device: {device}"
    )

    model = SentenceTransformer(
        model_name,
        device=device,
    )

    # --------------------------------------------------------
    # Build embedding text
    # --------------------------------------------------------
    #
    # Including the title helps retrieval distinguish
    # similar knowledge entries.

    embedding_texts = [
        f"{doc['title']}\n{doc['text']}"
        for doc in documents
    ]

    print(
        "Generating embeddings..."
    )

    embeddings = model.encode(
        embedding_texts,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    embeddings = embeddings.astype(
        np.float32
    )

    print(
        f"Embedding shape: "
        f"{embeddings.shape}"
    )

    # --------------------------------------------------------
    # FAISS inner-product index
    # --------------------------------------------------------
    #
    # Because embeddings are normalized:
    #
    # inner product == cosine similarity

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    faiss_path = (
        INDEX_DIR
        / "dense.index"
    )

    metadata_path = (
        INDEX_DIR
        / "documents.json"
    )

    temporary_index = faiss_path.with_suffix(".index.tmp")
    faiss.write_index(index, str(temporary_index))
    temporary_index.replace(faiss_path)

    temporary_metadata = metadata_path.with_suffix(".json.tmp")
    with open(temporary_metadata, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    temporary_metadata.replace(metadata_path)

    index_metadata = {
        "embedding_model": model_name,
        "dimensions": int(dimension),
        "document_count": len(documents),
        "normalized": True,
        "similarity": "cosine (FAISS inner product)",
    }
    (INDEX_DIR / "index_meta.json").write_text(
        json.dumps(index_metadata, indent=2), encoding="utf-8"
    )

    print("\nIndex created:")
    print(
        f"FAISS:    {faiss_path}"
    )
    print(
        f"Metadata: {metadata_path}"
    )

    print("=" * 80)

    return index_metadata


def main() -> None:
    build_index()


if __name__ == "__main__":
    main()
