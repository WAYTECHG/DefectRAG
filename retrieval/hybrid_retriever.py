from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class HybridRetriever:
    """
    Dense + BM25 hybrid retriever.

    Dense:
        Qwen3-Embedding-0.6B + FAISS

    Sparse:
        BM25

    Fusion:
        Reciprocal Rank Fusion (RRF)
    """

    def __init__(
        self,
        index_dir: str | Path = (
            PROJECT_ROOT
            / "retrieval"
            / "index"
        ),
        model_name: str = (
            "Qwen/Qwen3-Embedding-0.6B"
        ),
        device: str | None = None,
    ) -> None:

        self.index_dir = Path(
            index_dir
        )

        if device is None:

            import torch

            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = device

        # ----------------------------------------------------
        # Load FAISS
        # ----------------------------------------------------

        dense_index_path = (
            self.index_dir
            / "dense.index"
        )

        metadata_path = (
            self.index_dir
            / "documents.json"
        )

        if not dense_index_path.exists():
            raise FileNotFoundError(
                f"FAISS index missing:\n"
                f"{dense_index_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata missing:\n"
                f"{metadata_path}"
            )

        self.index = faiss.read_index(
            str(dense_index_path)
        )

        index_metadata_path = self.index_dir / "index_meta.json"
        if index_metadata_path.exists():
            with index_metadata_path.open("r", encoding="utf-8") as metadata_file:
                index_metadata = json.load(metadata_file)
            indexed_model = index_metadata.get("embedding_model")
            if indexed_model and indexed_model != model_name:
                raise ValueError(
                    f"Index was built with '{indexed_model}' but runtime uses '{model_name}'. "
                    "Set EMBEDDING_MODEL to the indexed model or rebuild the index."
                )

        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as f:

            self.documents = json.load(f)

        if not self.documents:
            raise ValueError("Retrieval metadata contains no documents.")
        if int(self.index.ntotal) != len(self.documents):
            raise ValueError(
                "FAISS index and document metadata are out of sync "
                f"({self.index.ntotal} vectors, {len(self.documents)} documents). Rebuild the index."
            )

        # ----------------------------------------------------
        # Load embedding model
        # ----------------------------------------------------

        print(
            f"Loading embedding model: "
            f"{model_name}"
        )

        print(
            f"Embedding device: "
            f"{self.device}"
        )

        self.embedding_model = (
            SentenceTransformer(
                model_name,
                device=self.device,
            )
        )

        # ----------------------------------------------------
        # Build BM25
        # ----------------------------------------------------

        tokenized_documents = [
            self._tokenize(
                f"{doc['title']} {doc['text']}"
            )
            for doc in self.documents
        ]

        self.bm25 = BM25Okapi(
            tokenized_documents
        )

        print(
            f"Loaded {len(self.documents)} "
            f"knowledge documents."
        )

    # ========================================================
    # Tokenization
    # ========================================================

    @staticmethod
    def _tokenize(text: str) -> list[str]:

        return text.lower().split()

    # ========================================================
    # Dense search
    # ========================================================

    def dense_search(
        self,
        query: str,
        k: int = 5,
    ) -> list[dict]:

        embedding = self.embedding_model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        embedding = embedding.astype(
            np.float32
        )

        scores, indices = self.index.search(
            embedding,
            min(k, len(self.documents)),
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index < 0:
                continue

            document = dict(
                self.documents[index]
            )

            document[
                "dense_score"
            ] = float(score)

            document[
                "dense_rank"
            ] = len(results) + 1

            document[
                "document_index"
            ] = int(index)

            results.append(
                document
            )

        return results

    # ========================================================
    # BM25 search
    # ========================================================

    def bm25_search(
        self,
        query: str,
        k: int = 5,
    ) -> list[dict]:

        tokens = self._tokenize(
            query
        )

        scores = self.bm25.get_scores(
            tokens
        )

        ranked_indices = np.argsort(
            scores
        )[::-1][:k]

        results = []

        for rank, index in enumerate(
            ranked_indices,
            start=1,
        ):

            document = dict(
                self.documents[index]
            )

            document[
                "bm25_score"
            ] = float(scores[index])

            document[
                "bm25_rank"
            ] = rank

            document[
                "document_index"
            ] = int(index)

            results.append(
                document
            )

        return results

    # ========================================================
    # RRF
    # ========================================================

    @staticmethod
    def reciprocal_rank_fusion(
        dense_results: list[dict],
        bm25_results: list[dict],
        rrf_k: int = 60,
    ) -> list[dict]:

        fused = {}

        # ----------------------------------------------------
        # Dense contribution
        # ----------------------------------------------------

        for rank, document in enumerate(
            dense_results,
            start=1,
        ):

            doc_id = document["id"]

            if doc_id not in fused:

                fused[doc_id] = {
                    "document": document,
                    "rrf_score": 0.0,
                }

            fused[doc_id][
                "rrf_score"
            ] += 1.0 / (
                rrf_k + rank
            )

        # ----------------------------------------------------
        # BM25 contribution
        # ----------------------------------------------------

        for rank, document in enumerate(
            bm25_results,
            start=1,
        ):

            doc_id = document["id"]

            if doc_id not in fused:

                fused[doc_id] = {
                    "document": document,
                    "rrf_score": 0.0,
                }

            fused[doc_id][
                "rrf_score"
            ] += 1.0 / (
                rrf_k + rank
            )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        ranked = sorted(
            fused.values(),
            key=lambda item: item[
                "rrf_score"
            ],
            reverse=True,
        )

        results = []

        for rank, item in enumerate(
            ranked,
            start=1,
        ):

            document = dict(
                item["document"]
            )

            document[
                "rrf_score"
            ] = float(
                item["rrf_score"]
            )

            document[
                "hybrid_rank"
            ] = rank

            results.append(
                document
            )

        return results

    # ========================================================
    # Hybrid search
    # ========================================================

    def search(
        self,
        query: str,
        k: int = 5,
        candidate_k: int = 10,
        category: str | None = None,
    ) -> list[dict]:
        if category is not None:
            from knowledge.policy import PRODUCTS
            if category not in PRODUCTS and category != "general":
                raise ValueError(f"Unknown knowledge category: {category}")
            # Search broadly before filtering so an unrelated product cannot
            # displace relevant passages in a small initial candidate list.
            candidate_k = len(self.documents)
        dense_results = self.dense_search(
            query=query,
            k=candidate_k,
        )

        bm25_results = self.bm25_search(
            query=query,
            k=candidate_k,
        )

        fused_results = (
            self.reciprocal_rank_fusion(
                dense_results=dense_results,
                bm25_results=bm25_results,
            )
        )

        if category is not None:
            from knowledge.policy import permitted_category
            fused_results = [doc for doc in fused_results if permitted_category(doc, category)]
        return fused_results[:k]


# ============================================================
# CLI test
# ============================================================

def main() -> None:

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--query",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--k",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    retriever = HybridRetriever()

    results = retriever.search(
        query=args.query,
        k=args.k,
    )

    print("\n")
    print("=" * 80)
    print("HYBRID RETRIEVAL RESULTS")
    print("=" * 80)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n--- Result {rank} ---"
        )

        print(
            f"ID: {result['id']}"
        )

        print(
            f"Title: {result['title']}"
        )

        print(
            f"Hybrid score: "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"Category: "
            f"{result.get('category', 'N/A')}"
        )

        print(
            f"Anomaly type: "
            f"{result.get('anomaly_type', 'N/A')}"
        )

        print(
            f"\n{result['text']}"
        )

        print(
            f"\nSource: "
            f"{result.get('source_url', 'N/A')}"
        )


if __name__ == "__main__":
    main()
