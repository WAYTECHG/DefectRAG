from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", KNOWLEDGE_DIR / "knowledge_base.jsonl"))
SOURCE_DIR = Path(os.getenv("SOURCE_DIR", ROOT / "knowledge" / "sources"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", ROOT / "retrieval" / "index"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", DATA_DIR / "uploads"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
FEATURES_DIR = Path(os.getenv("FEATURES_DIR", ROOT / "features"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", ROOT / "results" / "runtime"))
REFERENCE_DIR = Path(os.getenv("REFERENCE_DIR", ROOT / "cloud" / "references"))
CLOUD_MEMORY_DIR = Path(os.getenv("CLOUD_MEMORY_DIR", ROOT / "cloud" / "space" / "assets"))
HEAD_DIR = Path(os.getenv("HEAD_DIR", RESULTS_DIR / "training" / "seed42"))
OLLAMA_VISION_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_VISION_TIMEOUT_SECONDS", "120"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
NEO4J_URI = os.getenv("NEO4J_URI", "").strip()
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j").strip()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j").strip()
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "").strip()
STORE_ORIGINAL_UPLOADS = os.getenv("STORE_ORIGINAL_UPLOADS", "false").lower() in {"1", "true", "yes"}
HF_SPACE_ID = os.getenv("HF_SPACE_ID", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
