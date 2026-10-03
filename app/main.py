from __future__ import annotations

import asyncio
import io
import json
import logging
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from app.config import EMBEDDING_MODEL, INDEX_DIR, MAX_UPLOAD_MB, REFERENCE_DIR, RESULTS_DIR, UPLOAD_DIR
from app.rag_service import generate_answer, llm_status
from knowledge.policy import PRODUCTS, evidence_status, has_topic_overlap
from app.cloud_store import aura_store, cloud_health, persist_inspection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("defectrag")
_retriever: Any = None
_retriever_lock = threading.Lock()


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)
    category: str = "general"


class ContactRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    topic: str = Field(default="General support", min_length=2, max_length=120)
    message: str = Field(min_length=10, max_length=4000)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("DefectRAG API started; retrieval and LLM clients load on first request.")
    yield
    aura_store.close()


app = FastAPI(title="DefectRAG", version="1.0.0", description="Grounded document retrieval and defect knowledge assistant", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=RESULTS_DIR), name="artifacts")
app.mount("/references", StaticFiles(directory=REFERENCE_DIR), name="references")


def get_retriever():
    global _retriever
    if _retriever is None:
        with _retriever_lock:
            if _retriever is None:
                from retrieval.hybrid_retriever import HybridRetriever
                # Ollama and DINOv3 share an 8 GB laptop GPU; keep text retrieval on CPU.
                _retriever = HybridRetriever(index_dir=INDEX_DIR, model_name=EMBEDDING_MODEL, device="cpu")
    return _retriever


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
def health():
    metadata_path = INDEX_DIR / "documents.json"
    try:
        count = len(json.loads(metadata_path.read_text(encoding="utf-8"))) if metadata_path.exists() else 0
    except Exception:
        count = 0
    ready = (INDEX_DIR / "dense.index").exists() and metadata_path.exists() and count > 0
    from app.inspection_service import available_categories
    categories = available_categories()
    methods = [name for name in ("baseline", "trained", "fusion") if any(name in item["methods"] for item in categories if item["ready"])]
    return {
        "status": "ok" if ready else "degraded",
        "retrieval_ready": ready,
        "document_chunks": count,
        "llm": llm_status(),
        "inspection_categories": categories,
        "inspection_ready": any(item["ready"] for item in categories),
        "scoring_methods": methods,
        "cloud": cloud_health(),
    }


@app.get("/api/categories")
def categories():
    from app.inspection_service import available_categories
    return {"categories": available_categories()}


@app.post("/api/inspect")
async def inspect(category: str, file: UploadFile = File(...), method: Literal["baseline", "trained", "fusion"] = "baseline"):
    if (file.content_type or "").lower() not in {"image/jpeg", "image/png", "image/webp", "image/bmp"}:
        raise HTTPException(415, "Upload a JPG, PNG, WebP, or BMP image.")
    content = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Image exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "The uploaded file is not a valid image.") from exc
    if image.width < 64 or image.height < 64:
        raise HTTPException(400, "Image dimensions must be at least 64 × 64 pixels.")
    if image.width * image.height > 40_000_000:
        raise HTTPException(413, "Image dimensions are too large.")
    inspection_upload_dir = UPLOAD_DIR / "images"
    inspection_upload_dir.mkdir(parents=True, exist_ok=True)
    image_path = inspection_upload_dir / f"{uuid.uuid4().hex}.png"
    image.save(image_path, format="PNG")
    try:
        from app.inspection_service import inspect_image
        result = await asyncio.to_thread(inspect_image, image_path, category, get_retriever, method)
        logger.info("Saving optional inspection media and metadata: job_id=%s", result["job_id"])
        result = await asyncio.to_thread(persist_inspection, result, image_path)
        logger.info("Inspection response ready: job_id=%s persistence=%s", result["job_id"], result.get("persistence"))
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception("Image inspection failed")
        raise HTTPException(500, "Image inspection failed. Check API logs for details.") from exc
    finally:
        image_path.unlink(missing_ok=True)
    return result


@app.post("/api/contact", status_code=201)
async def contact(request: ContactRequest):
    try:
        message_id = await asyncio.to_thread(
            aura_store.save_contact,
            request.name.strip(),
            request.email.strip().lower(),
            request.topic.strip(),
            request.message.strip(),
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception("Support message persistence failed")
        raise HTTPException(503, "The support message could not be stored. Please try again later.") from exc
    return {"status": "received", "message_id": message_id}


@app.post("/api/ask")
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(422, "Question cannot be blank.")
    if request.category not in PRODUCTS and request.category != "general":
        raise HTTPException(422, "Unsupported knowledge category.")
    try:
        results = get_retriever().search(question, k=request.top_k, candidate_k=max(request.top_k * 2, 10), category=request.category)
        if not results or not has_topic_overlap(question, results):
            results = []
            answer = "The approved knowledge index has no relevant passage for this category. I cannot verify an answer."
        elif request.category != "general" and not evidence_status(results, request.category)["product_rules_available"]:
            answer = "The index has general anomaly information, but no reviewed rule for this product. I cannot verify its expected configuration or a product-specific defect."
        else:
            answer = generate_answer(question, results)
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Search index is not ready: {exc}. Build it with `python -m retrieval.build_index`.") from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception("RAG request failed")
        raise HTTPException(500, "The RAG request failed. Check API logs for details.") from exc
    return {"answer": answer, "question": question, "sources": [
        {"rank": i, "id": doc.get("id"), "title": doc.get("title"), "source": doc.get("source"),
         "source_url": doc.get("source_url"), "category": doc.get("category"),
         "anomaly_type": doc.get("anomaly_type"), "score": doc.get("rrf_score"), "text": doc.get("text")}
        for i, doc in enumerate(results, 1)
    ]}


@app.post("/api/documents", include_in_schema=False)
async def upload_document_disabled():
    raise HTTPException(403, "Public document ingestion is disabled. Only the developer can review and rebuild the knowledge index offline.")
