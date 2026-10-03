from __future__ import annotations

import asyncio
import io
import logging
import shutil
import tempfile
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

from app.cloud_store import aura_store, cloud_health, persist_inspection
from app.config import HF_SPACE_ID, HF_TOKEN, MAX_UPLOAD_MB, REFERENCE_DIR, RESULTS_DIR
from app.inspection_service import CATEGORIES, CATEGORY_THRESHOLDS

logger = logging.getLogger("defectrag.render")
_client: Any = None
_client_lock = threading.Lock()


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)
    category: Literal["general", "breakfast_box", "juice_bottle", "pushpins", "screw_bag", "splicing_connectors"] = "general"


class ContactRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    topic: str = Field(default="General support", min_length=2, max_length=120)
    message: str = Field(min_length=10, max_length=4000)


def _space_client():
    global _client
    if not HF_SPACE_ID:
        raise RuntimeError("HF_SPACE_ID is not configured on Render.")
    if _client is None:
        with _client_lock:
            if _client is None:
                from gradio_client import Client

                _client = Client(HF_SPACE_ID, token=HF_TOKEN or None, verbose=False)
    return _client


def _copy_artifact(source: str | Path, destination: Path) -> str:
    source_path = Path(source)
    if not source_path.is_file():
        raise RuntimeError(f"The inference service did not return a valid artifact: {source_path.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return str(destination)


def _run_remote_inspection(image_path: Path, category: str, method: str = "baseline") -> dict[str, Any]:
    from gradio_client import handle_file

    outputs = _space_client().predict(
        image=handle_file(str(image_path)),
        category=category,
        method=method,
        api_name="/inspect_method",
    )
    if not isinstance(outputs, (tuple, list)) or len(outputs) != 7:
        raise RuntimeError("The Hugging Face Space API is out of date. Deploy the included cloud/space app before using Render.")
    _, location_source, heatmap_source, reference_source, _, _, payload = outputs
    if not isinstance(payload, dict):
        raise RuntimeError("The inference service returned an invalid inspection payload.")

    job_id = str(payload.get("job_id") or uuid.uuid4().hex)
    destination = RESULTS_DIR / job_id
    location_path = destination / "location.jpg"
    heatmap_path = destination / "heatmap.jpg"
    _copy_artifact(location_source, location_path)
    _copy_artifact(heatmap_source, heatmap_path)
    payload["job_id"] = job_id
    payload["artifacts"] = {
        "location": f"/artifacts/{job_id}/location.jpg",
        "heatmap": f"/artifacts/{job_id}/heatmap.jpg",
    }

    if reference_source:
        reference_path = REFERENCE_DIR / category / "normal_reference.jpg"
        _copy_artifact(reference_source, reference_path)
        payload.setdefault("reference_example", {})["url"] = f"/references/{category}/normal_reference.jpg"
        payload["reference_example"]["available"] = True

    return persist_inspection(payload, image_path)


def _run_remote_question(question: str, category: str = "general") -> dict[str, Any]:
    response = _space_client().predict(question=question, category=category, api_name="/ask")
    if isinstance(response, dict):
        return response
    return {"question": question, "answer": str(response), "sources": []}


@asynccontextmanager
async def lifespan(_: FastAPI):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    aura_store.close()


app = FastAPI(
    title="DefectRAG Cloud Gateway",
    version="3.0.0",
    description="Render gateway for ZeroGPU anomaly inference and cloud-persisted inspection records.",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
def health():
    configured = bool(HF_SPACE_ID)
    return {
        "status": "ok" if configured else "degraded",
        "retrieval_ready": configured,
        "document_chunks": None,
        "llm": {"available": configured, "provider": "Hugging Face ZeroGPU"},
        "inspection_categories": [
            {
                "id": category,
                "label": category.replace("_", " ").title(),
                "ready": configured,
                "threshold": CATEGORY_THRESHOLDS[category],
                "reference_ready": configured,
            }
            for category in CATEGORIES
        ],
        "inspection_ready": configured,
        "scoring_methods": ["baseline", "trained", "fusion"],
        "cloud": cloud_health(),
        "deployment": "render-gateway",
    }


@app.post("/api/inspect")
async def inspect(category: str, file: UploadFile = File(...), method: Literal["baseline", "trained", "fusion"] = "baseline"):
    if category not in CATEGORIES:
        raise HTTPException(422, f"Unsupported category: {category}")
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

    with tempfile.TemporaryDirectory() as temporary:
        image_path = Path(temporary) / "upload.png"
        image.save(image_path, "PNG")
        try:
            return await asyncio.to_thread(_run_remote_inspection, image_path, category, method)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        except Exception as exc:
            logger.exception("Remote inspection failed")
            raise HTTPException(503, "The inference service is unavailable or has reached its free GPU quota. Try again later.") from exc


@app.post("/api/ask")
async def ask(request: AskRequest):
    try:
        return await asyncio.to_thread(_run_remote_question, request.question.strip(), request.category)
    except Exception as exc:
        logger.exception("Remote knowledge request failed")
        raise HTTPException(503, "The knowledge service is unavailable. Try again later.") from exc


@app.post("/api/documents")
async def documents_disabled():
    raise HTTPException(403, "Public document ingestion is disabled. Only the developer can review and rebuild the knowledge index offline.")


@app.post("/api/contact", status_code=201)
async def contact(request: ContactRequest):
    try:
        message_id = await asyncio.to_thread(
            aura_store.save_contact,
            request.name.strip(), request.email.strip().lower(), request.topic.strip(), request.message.strip(),
        )
        return {"status": "received", "message_id": message_id}
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception("Support message persistence failed")
        raise HTTPException(503, "The support message could not be stored. Please try again later.") from exc


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/artifacts", StaticFiles(directory=RESULTS_DIR), name="artifacts")
app.mount("/references", StaticFiles(directory=REFERENCE_DIR), name="references")
