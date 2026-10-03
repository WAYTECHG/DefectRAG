from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Configuration
# ============================================================

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "knowledge_base.jsonl"
)

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".jsonl",
}


# ============================================================
# Text utilities
# ============================================================

def normalize_whitespace(text: str) -> str:
    """
    Normalize excessive whitespace while preserving paragraph
    boundaries reasonably well.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing spaces.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Collapse 3+ newlines to 2.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[str]:
    """
    Character-based chunking with overlap.

    This intentionally mirrors the chunking approach you were
    experimenting with earlier, while making it reusable for
    the real knowledge ingestion pipeline.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be > 0"
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap must be >= 0"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller "
            "than chunk_size"
        )

    text = normalize_whitespace(text)

    if not text:
        return []

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        # ----------------------------------------------------
        # Try to end at a natural boundary
        # ----------------------------------------------------

        if end < text_length:

            candidate = text[
                start:end
            ]

            # Prefer paragraph/sentence boundaries.
            break_positions = [
                candidate.rfind("\n\n"),
                candidate.rfind(". "),
                candidate.rfind("? "),
                candidate.rfind("! "),
            ]

            best_break = max(
                break_positions
            )

            # Only use a natural boundary if it doesn't
            # make the chunk excessively short.
            if best_break >= int(
                chunk_size * 0.50
            ):

                end = (
                    start
                    + best_break
                    + 1
                )

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = (
            end
            - chunk_overlap
        )

    return chunks


# ============================================================
# Metadata helpers
# ============================================================

def infer_category(
    path: Path,
    text: str,
) -> str:
    """
    Infer category only when it is explicitly recognizable
    from known LOCO AD category names.

    Otherwise returns 'general'.

    This avoids inventing category assignments.
    """

    known_categories = {
        "breakfast_box",
        "juice_bottle",
        "pushpins",
        "screw_bag",
        "splicing_connectors",
    }

    parts = {
        part.lower()
        for part in path.parts
    }

    for category in known_categories:
        if category in parts:
            return category

    # Filename/content heuristic only when an exact category
    # string occurs.
    lowered = text.lower()

    for category in known_categories:
        if category in lowered:
            return category

    return "general"


def infer_anomaly_type(
    path: Path,
    text: str,
) -> str:
    """
    Infer anomaly type only from explicit terminology.

    Returns:
        logical
        structural
        general
    """

    lowered_path = str(
        path
    ).lower()

    lowered_text = text.lower()

    if (
        "logical_anomal" in lowered_path
        or "logical anomaly" in lowered_text
    ):
        return "logical"

    if (
        "structural_anomal" in lowered_path
        or "structural anomaly" in lowered_text
    ):
        return "structural"

    return "general"


def make_document_id(
    source_path: Path,
    chunk_index: int,
) -> str:

    raw = (
        f"{source_path.resolve()}"
        f"::{chunk_index}"
    )

    digest = hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()[:16]

    return (
        f"doc_{digest}"
    )


# ============================================================
# File readers
# ============================================================

def read_text_file(
    path: Path,
) -> str:

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def read_json_file(
    path: Path,
) -> list[dict[str, Any]]:
    """
    Accept:

    1. A single object:
       {"title": "...", "text": "..."}

    2. A list:
       [{"title": "...", "text": "..."}]

    3. A wrapper:
       {"documents": [...]}
    """

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    if isinstance(data, dict):

        if "documents" in data:
            data = data["documents"]

        else:
            data = [data]

    if not isinstance(
        data,
        list,
    ):
        raise ValueError(
            f"Unsupported JSON structure in {path}"
        )

    documents = []

    for item in data:

        if not isinstance(
            item,
            dict,
        ):
            continue

        documents.append(
            item
        )

    return documents


def read_jsonl_file(
    path: Path,
) -> list[dict[str, Any]]:

    documents = []

    with open(
        path,
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
                item = json.loads(
                    line
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSONL in {path}, "
                    f"line {line_number}: {exc}"
                )

            if not isinstance(
                item,
                dict,
            ):
                continue

            documents.append(
                item
            )

    return documents


# ============================================================
# Convert source into raw documents
# ============================================================

def load_source(
    path: Path,
) -> list[dict[str, Any]]:
    """
    Convert a source file into standardized records.
    """

    suffix = path.suffix.lower()

    if suffix in {
        ".txt",
        ".md",
    }:

        text = read_text_file(
            path
        )

        return [
            {
                "title": path.stem,
                "text": text,
            }
        ]

    if suffix == ".json":

        return read_json_file(
            path
        )

    if suffix == ".jsonl":

        return read_jsonl_file(
            path
        )

    raise ValueError(
        f"Unsupported file type: {path}"
    )


# ============================================================
# Standardize raw record
# ============================================================

def standardize_record(
    record: dict[str, Any],
    source_path: Path,
) -> dict[str, Any] | None:
    """
    Convert different source schemas into our internal format.
    """

    title = str(
        record.get(
            "title",
            source_path.stem,
        )
    ).strip()

    text = record.get(
        "text"
    )

    if text is None:

        text = record.get(
            "content"
        )

    if text is None:

        text = record.get(
            "description"
        )

    if text is None:
        return None

    text = str(
        text
    ).strip()

    if not text:
        return None

    metadata = record.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    category = (
        record.get(
            "category"
        )
        or metadata.get(
            "category"
        )
        or infer_category(
            source_path,
            text,
        )
    )

    anomaly_type = (
        record.get(
            "anomaly_type"
        )
        or metadata.get(
            "anomaly_type"
        )
        or infer_anomaly_type(
            source_path,
            text,
        )
    )

    source = (
        record.get(
            "source"
        )
        or metadata.get(
            "source"
        )
        or source_path.name
    )

    source_url = (
        record.get(
            "source_url"
        )
        or metadata.get(
            "source_url"
        )
        or ""
    )

    return {
        "title": title,
        "text": text,
        "category": str(
            category
        ),
        "anomaly_type": str(
            anomaly_type
        ),
        "source": str(
            source
        ),
        "source_url": str(
            source_url
        ),
    }


# ============================================================
# Chunk standardized record
# ============================================================

def chunk_record(
    record: dict[str, Any],
    source_path: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:

    chunks = chunk_text(
        record["text"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    results = []

    for index, chunk in enumerate(
        chunks
    ):

        document_id = make_document_id(
            source_path,
            index,
        )

        results.append(
            {
                "id": document_id,
                "title": record[
                    "title"
                ],
                "text": chunk,
                "category": record[
                    "category"
                ],
                "anomaly_type": record[
                    "anomaly_type"
                ],
                "source": record[
                    "source"
                ],
                "source_url": record[
                    "source_url"
                ],
                "source_file": str(
                    source_path
                ),
                "chunk_index": index,
                "chunk_size": len(
                    chunk
                ),
            }
        )

    return results


# ============================================================
# Existing knowledge base
# ============================================================

def load_existing(
    output_path: Path,
) -> list[dict[str, Any]]:

    if not output_path.exists():
        return []

    documents = []

    with open(
        output_path,
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            try:

                document = json.loads(
                    line
                )

            except json.JSONDecodeError:
                continue

            if isinstance(
                document,
                dict,
            ):
                documents.append(
                    document
                )

    return documents


# ============================================================
# Deduplication
# ============================================================

def merge_documents(
    existing: list[dict[str, Any]],
    new_documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deduplicate by document ID.
    New versions replace old versions with the same ID.
    """

    merged = {}

    for document in existing:

        if "id" not in document:
            continue

        merged[
            document["id"]
        ] = document

    for document in new_documents:

        if "id" not in document:
            continue

        merged[
            document["id"]
        ] = document

    return list(
        merged.values()
    )


# ============================================================
# Write JSONL
# ============================================================

def save_jsonl(
    documents: list[dict[str, Any]],
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        for document in documents:

            f.write(
                json.dumps(
                    document,
                    ensure_ascii=False,
                )
                + "\n"
            )


# ============================================================
# Find source files
# ============================================================

def find_source_files(
    source_dir: Path,
) -> list[Path]:

    files = []

    for path in source_dir.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in (
            SUPPORTED_EXTENSIONS
        ):
            continue

        files.append(
            path
        )

    return sorted(
        files
    )


# ============================================================
# Main ingestion
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Ingest domain knowledge into "
            "the DefectRAG JSONL knowledge base."
        )
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help=(
            "Directory containing source documents."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Output knowledge_base.jsonl path."
        ),
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Replace the existing knowledge base "
            "instead of merging."
        ),
    )

    args = parser.parse_args()

    source_dir = (
        args.source
    )

    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory does not exist:\n"
            f"{source_dir}"
        )

    # --------------------------------------------------------
    # Find files
    # --------------------------------------------------------

    source_files = find_source_files(
        source_dir
    )

    if not source_files:
        raise RuntimeError(
            f"No supported source files found in:\n"
            f"{source_dir}"
        )

    print("=" * 90)
    print("DEFECTRAG KNOWLEDGE INGESTION")
    print("=" * 90)

    print(
        f"Source directory: "
        f"{source_dir}"
    )

    print(
        f"Source files: "
        f"{len(source_files)}"
    )

    print(
        f"Chunk size: "
        f"{args.chunk_size}"
    )

    print(
        f"Chunk overlap: "
        f"{args.chunk_overlap}"
    )

    # --------------------------------------------------------
    # Ingest
    # --------------------------------------------------------

    new_documents = []

    for file_index, source_path in enumerate(
        source_files,
        start=1,
    ):

        print(
            f"\n[{file_index}/{len(source_files)}] "
            f"{source_path.name}"
        )

        try:

            raw_records = load_source(
                source_path
            )

        except Exception as exc:

            print(
                f"ERROR reading {source_path}: "
                f"{exc}"
            )

            continue

        file_chunks = 0

        for record in raw_records:

            standardized = (
                standardize_record(
                    record,
                    source_path,
                )
            )

            if standardized is None:
                continue

            chunks = chunk_record(
                record=standardized,
                source_path=source_path,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            )

            new_documents.extend(
                chunks
            )

            file_chunks += len(
                chunks
            )

        print(
            f"Generated chunks: "
            f"{file_chunks}"
        )

    if not new_documents:

        raise RuntimeError(
            "No valid documents were generated."
        )

    # --------------------------------------------------------
    # Existing
    # --------------------------------------------------------

    if args.replace:

        existing_documents = []

    else:

        existing_documents = (
            load_existing(
                args.output
            )
        )

    merged_documents = merge_documents(
        existing=existing_documents,
        new_documents=new_documents,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_jsonl(
        merged_documents,
        args.output,
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    categories = {}

    anomaly_types = {}

    for document in merged_documents:

        category = document.get(
            "category",
            "general",
        )

        anomaly_type = document.get(
            "anomaly_type",
            "general",
        )

        categories[
            category
        ] = (
            categories.get(
                category,
                0,
            )
            + 1
        )

        anomaly_types[
            anomaly_type
        ] = (
            anomaly_types.get(
                anomaly_type,
                0,
            )
            + 1
        )

    print("\n")
    print("=" * 90)
    print("INGESTION FINISHED")
    print("=" * 90)

    print(
        f"New chunks: "
        f"{len(new_documents)}"
    )

    print(
        f"Total knowledge chunks: "
        f"{len(merged_documents)}"
    )

    print(
        f"\nCategories:"
    )

    for category, count in sorted(
        categories.items()
    ):

        print(
            f"  {category}: {count}"
        )

    print(
        f"\nAnomaly types:"
    )

    for anomaly_type, count in sorted(
        anomaly_types.items()
    ):

        print(
            f"  {anomaly_type}: {count}"
        )

    print(
        f"\nSaved to:"
    )

    print(
        args.output
    )

    print("=" * 90)


if __name__ == "__main__":
    main()