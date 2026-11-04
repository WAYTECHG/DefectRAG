from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
import csv
import logging
import os
import re
import uuid
import warnings
import threading
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError
from .config import Settings, CATEGORIES
from .storage import SQLiteRepository, now
from .vision import ModelUnavailable, create_detector
from .rag import KnowledgeIndex, EvidenceWorkflow
from .routes_reference import mount_reference_routes

log = logging.getLogger("defectrag")

# Inspection IDs are 32 lowercase hex characters (uuid4().hex).
INSPECTION_ID = re.compile(r"[a-f0-9]{32}")


def require_inspection_id(identifier: str) -> None:
    """Reject anything that is not a well-formed inspection ID before it reaches storage."""
    if not INSPECTION_ID.fullmatch(identifier):
        raise HTTPException(422, "Invalid inspection ID")


def create_app(settings=None, detector=None, workflow=None, repository=None, gallery=None):
    settings = settings or Settings()
    settings.data.mkdir(parents=True, exist_ok=True)
    artifacts = settings.data / "artifacts"
    artifacts.mkdir(exist_ok=True)
    if repository is None and os.getenv("DEFECTRAG_LOCAL_SYNC") == "1":
        from .local_sync import LocalSyncRepository
        from deployment.space.supabase_repository import read_public_config

        config = read_public_config(settings.root / "frontend/public/config.js")
        config["auth_workflow_enabled"] = True
        repository = LocalSyncRepository(settings.data, config, artifacts)
    # Local, local-sync and cloud-session repositories share one duck-typed surface.
    repo: Any = repository if repository is not None else SQLiteRepository(settings.data / "inspection.sqlite3")
    # SessionRepository delegates missing instance attributes to a live account;
    # factory construction must never require an active cloud request context.
    local_sync = bool(getattr(type(repo), "local_sync_enabled", False))

    def artifact_directory():
        return repo.artifact_directory() if local_sync else artifacts

    detector = detector or create_detector(settings)
    if workflow is None:
        workflow = EvidenceWorkflow(settings, KnowledgeIndex(settings.root, settings.data / "index"))
    app = FastAPI(title="DefectRAG", version="2.1.0", description="Industrial inspection and evidence workspace")
    app.state.repo = repo
    app.state.detector = detector
    app.state.workflow = workflow
    from .gallery import LocalGallery, mount_gallery

    if (
        gallery is None
        and os.getenv("DEFECTRAG_GALLERY_ENABLED") == "1"
        and (not hasattr(repo, "current") or local_sync)
    ):
        import secrets

        key_path = settings.data / "gallery.key"
        if not key_path.exists():
            key_path.write_text(secrets.token_hex(32))
        gallery = LocalGallery(settings.data / "gallery.sqlite3", key_path.read_text().strip())
    if hasattr(repo, "current"):
        from deployment.space.sessions import NAMESPACE

        gallery_owner = lambda: NAMESPACE.get() or ""
    else:
        gallery_owner = lambda: "local-operator"
    mount_gallery(
        app,
        repo,
        artifact_directory if local_sync else artifacts,
        gallery,
        owner=gallery_owner,
        cloud_origin=(getattr(repo, "cloud_config", None) or {}).get("url", ""),
    )
    origins = [o.strip() for o in os.getenv("DEFECTRAG_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]
    if local_sync:
        origins = list(set(origins + ["http://localhost:8765", "http://127.0.0.1:8765"]))
        from .local_sync_api import mount_local_sync

        mount_local_sync(app, repo, origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization", "X-DefectRAG-Session", "X-DefectRAG-Workspace"]
        if local_sync
        else ["Content-Type"],
        expose_headers=["X-DefectRAG-Export"] if local_sync else [],
    )

    @app.middleware("http")
    async def body_limit(request: Request, call_next):
        length = request.headers.get("content-length")
        try:
            if length and int(length) > 22 * 1024 * 1024:
                return JSONResponse(
                    status_code=413,
                    content={"error": {"code": "upload_too_large", "message": "Total request limit is 22 MB."}},
                )
        except ValueError:
            return JSONResponse(
                status_code=400, content={"error": {"code": "invalid_length", "message": "Invalid content length"}}
            )
        # Bound streamed/chunked bodies too, before multipart parsing can spool them.
        if request.method == "POST":
            received = 0
            chunks = []
            async for chunk in request.stream():
                received += len(chunk)
                if received > 22 * 1024 * 1024:
                    return JSONResponse(
                        status_code=413,
                        content={"error": {"code": "upload_too_large", "message": "Total request limit is 22 MB."}},
                    )
                chunks.append(chunk)
            request._body = b"".join(chunks)
        return await call_next(request)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code, content={"error": {"code": str(exc.status_code), "message": str(exc.detail)}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation",
                    "message": "Invalid request fields",
                    "fields": [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()],
                }
            },
        )

    def require(identifier):
        record = repo.get(identifier)
        if not record:
            raise HTTPException(404, "Inspection not found")
        return record

    inspection_lock = threading.RLock()

    def inspect_bytes(*args, **kwargs):
        with inspection_lock:
            return _inspect_bytes(*args, **kwargs)

    def _inspect_bytes(content, category, batch, filename, request_id=""):
        if category not in CATEGORIES:
            raise HTTPException(422, "Choose a supported VisA product category")
        if len(batch) > 80:
            raise HTTPException(422, "Batch label is limited to 80 characters")
        if len(content) > settings.max_upload:
            raise HTTPException(413, "Image limit is 10 MB")
        from .inspection_requests import existing_request, fingerprint

        try:
            existing = existing_request(repo, request_id, content, category, batch)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if existing:
            return existing
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(content)) as opened:
                    if opened.format not in ("JPEG", "PNG", "WEBP"):
                        raise ValueError("Use JPEG, PNG or WebP")
                    if opened.width * opened.height > settings.max_pixels:
                        raise ValueError("Image limit is 25 megapixels")
                    if opened.width < 32 or opened.height < 32:
                        raise ValueError("Image must be at least 32 pixels on each side")
                    image = ImageOps.exif_transpose(opened).convert("RGB")
                    image.load()
        except (
            ValueError,
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise HTTPException(
                422,
                "This file could not be read as a supported image. Use a valid JPEG, PNG or WebP within the stated size limits.",
            ) from exc
        try:
            result, heatmap = detector.predict(image, category)
        except ModelUnavailable as exc:
            repo.failure(category, "model_unavailable")
            raise HTTPException(503, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - any model failure must become a clean 503, never a crash
            log.exception("Model inference failed")
            repo.failure(category, "inference_failed")
            raise HTTPException(503, "Model execution failed. No inspection was saved.") from exc
        identifier = request_id or uuid.uuid4().hex
        image_path = artifact_directory() / f"{identifier}.jpg"
        heatmap_path = artifact_directory() / f"{identifier}_heatmap.jpg"
        try:
            image.thumbnail((1600, 1600))
            image.save(image_path, quality=92)
            heatmap.save(heatmap_path, quality=92)
            record = {
                **result,
                "id": identifier,
                "created_at": now(),
                "batch": batch.strip(),
                "filename": Path(filename).name[:160],
                "image_url": f"/api/inspections/{identifier}/image",
                "heatmap_url": f"/api/inspections/{identifier}/heatmap",
                "request_fingerprint": fingerprint(content, category, batch),
            }
            return repo.save(record)
        except Exception:
            image_path.unlink(missing_ok=True)
            heatmap_path.unlink(missing_ok=True)
            raise

    @app.get("/api/health")
    def health():
        return {
            "data": {
                "status": "ok",
                "version": "2.1.0",
                "mode": "local_single_user",
                "models": detector.cards(),
                "encoder_configured": Path(settings.encoder).exists(),
                "llm_model": settings.ollama_model,
                "local_sync_enabled": local_sync,
                "personal_workspace_enabled": local_sync,
                "auth_workflow_enabled": local_sync,
            }
        }

    @app.get("/api/models")
    def models():
        return {"data": detector.cards()}

    mount_reference_routes(app, settings, detector)

    @app.get("/api/stats")
    def stats():
        return {"data": repo.stats()}

    @app.get("/api/workspace")
    def workspace_status():
        return {
            "data": repo.status()
            if hasattr(repo, "status")
            else {"personal_enabled": False, "workspace": "local", "storage": "local_disk", "authenticated": False}
        }

    class ShareRequest(BaseModel):
        include_conversation: bool = False

    @app.post("/api/inspections/{identifier}/share")
    def share_personal(identifier: str, body: ShareRequest):
        require_inspection_id(identifier)
        if not hasattr(repo, "share"):
            raise HTTPException(409, "Use the existing staff sharing action in this build.")
        return {"data": repo.share(identifier, body.include_conversation)}

    @app.post("/api/inspections/{identifier}/save-personal")
    def save_guest_personal(identifier: str):
        require_inspection_id(identifier)
        if not hasattr(repo, "share"):
            raise HTTPException(409, "Personal cloud storage is not enabled in this build.")
        return {"data": repo.share(identifier, personal_only=True)}

    @app.post("/api/inspect")
    def inspect(
        category: str = Form(...),
        batch: str = Form(""),
        file: UploadFile = File(...),
        request_id: str = Form("", max_length=32),
    ):
        try:
            content = file.file.read(settings.max_upload + 1)
            return {"data": inspect_bytes(content, category, batch, file.filename or "upload", request_id)}
        finally:
            file.file.close()

    @app.post("/api/batch")
    def inspect_batch(category: str = Form(...), batch: str = Form(...), files: list[UploadFile] = File(...)):
        if not 1 <= len(files) <= 20:
            raise HTTPException(422, "Upload 1–20 files per batch")
        if category not in CATEGORIES or not batch.strip() or len(batch) > 80:
            raise HTTPException(422, "Choose a valid category and batch label of 1–80 characters")
        records, errors = [], []
        for file in files:
            try:
                records.append(
                    inspect_bytes(file.file.read(settings.max_upload + 1), category, batch, file.filename or "upload")
                )
            except HTTPException as exc:
                errors.append({"filename": file.filename, "message": str(exc.detail), "status": exc.status_code})
            finally:
                file.file.close()
        return {"data": {"records": records, "errors": errors, "batch": batch}}

    @app.get("/api/inspections")
    def inspections(
        category: str = "",
        verdict: str = "",
        batch: str = "",
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ):
        return {"data": repo.list(category, verdict, batch, limit, offset)}

    class ArchiveRequest(BaseModel):
        confirmation: str = Field(pattern="^ARCHIVE$")
        category: str = Field(default="", max_length=40)
        verdict: str = Field(default="", max_length=20)
        batch: str = Field(default="", max_length=80)

    @app.post("/api/history/archive")
    def archive_history(payload: ArchiveRequest):
        return {"data": repo.archive(payload.category, payload.verdict, payload.batch)}

    @app.get("/api/archives")
    def archived_inspections():
        return {"data": repo.list(limit=500, archived=True)}

    class RestoreRequest(BaseModel):
        ids: list[str] = Field(min_length=1, max_length=500)

    @app.post("/api/history/restore")
    def restore_history(payload: RestoreRequest):
        if not all(INSPECTION_ID.fullmatch(i) for i in payload.ids):
            raise HTTPException(422, "Invalid inspection IDs")
        return {"data": repo.restore(payload.ids)}

    @app.get("/api/inspections/{identifier}")
    def inspection(identifier: str):
        return {"data": require(identifier)}

    def inspection_artifact(identifier: str, kind: str):
        """Send the saved picture of an inspection; kind is "image" or "heatmap".

        With local sync the bytes come from the account's repository and are never cached by
        the browser. Otherwise the file is read from the artifacts folder.
        """
        require(identifier)
        if local_sync:
            return Response(
                repo.artifact_bytes(identifier, kind),
                media_type="image/jpeg",
                headers={"Cache-Control": "private, no-store"},
            )
        filename = f"{identifier}.jpg" if kind == "image" else f"{identifier}_heatmap.jpg"
        return FileResponse(artifacts / filename)

    @app.get("/api/inspections/{identifier}/image")
    def inspection_image(identifier: str):
        return inspection_artifact(identifier, "image")

    @app.get("/api/inspections/{identifier}/heatmap")
    def inspection_heatmap(identifier: str):
        return inspection_artifact(identifier, "heatmap")

    class HumanReview(BaseModel):
        status: str = Field(pattern="^(Needs review|In review|Reviewed)$")
        decision: str = Field(pattern="^(Pending|Hold|Accept|Reject)$")
        note: str = Field(default="", max_length=1000)

    @app.get("/api/inspections/{identifier}/reviews")
    def review_history(identifier: str):
        require(identifier)
        return {"data": repo.review_history(identifier)}

    @app.post("/api/inspections/{identifier}/review")
    def save_review(identifier: str, payload: HumanReview):
        require(identifier)
        from .reviews import validate_review

        try:
            validate_review(payload.status, payload.decision, payload.note)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"data": repo.add_review(identifier, payload.status, payload.decision, payload.note)}

    class Question(BaseModel):
        inspection_id: str = Field(min_length=32, max_length=32, pattern="^[0-9a-f]{32}$")
        question: str = Field(min_length=3, max_length=1200)

    @app.post("/api/assistant")
    def assistant(payload: Question):
        record = require(payload.inspection_id)
        history = repo.messages(payload.inspection_id)
        # Save user and assistant turns together only after workflow completion.
        answer = workflow.run(
            payload.question,
            record,
            [
                {
                    "role": m["role"],
                    "text": m.get("question", m.get("answer", "")),
                    "knowledge_fingerprint": m.get("knowledge_fingerprint"),
                }
                for m in history
            ],
        )
        repo.add_conversation(payload.inspection_id, payload.question, answer)
        return {
            "data": {
                **answer,
                "observation": {k: record[k] for k in ("id", "category", "verdict", "score", "threshold")},
            }
        }

    @app.get("/api/inspections/{identifier}/messages")
    def messages(identifier: str):
        require(identifier)
        return {"data": repo.messages(identifier)}

    class RetrievalQuestion(BaseModel):
        question: str = Field(min_length=3, max_length=1200)

    @app.post("/api/retrieve")
    def retrieve(payload: RetrievalQuestion):
        try:
            docs = workflow.index.retriever.invoke(payload.question)
            return {"data": [{"text": d.page_content, **d.metadata} for d in docs]}
        except Exception as exc:  # noqa: BLE001 - report as 503, but keep the cause in the log
            log.exception("Knowledge retrieval failed")
            raise HTTPException(503, "Local knowledge index is unavailable") from exc

    @app.get("/api/alerts")
    def alerts():
        return {"data": repo.alerts()}

    @app.post("/api/alerts/{identifier}/acknowledge")
    def acknowledge(identifier: str):
        if not repo.acknowledge(identifier):
            raise HTTPException(404, "Alert not found")
        return {"data": {"acknowledged": True}}

    @app.get("/api/export.csv")
    def export(category: str = "", verdict: str = "", batch: str = ""):
        output = StringIO()
        fields = ["id", "created_at", "category", "batch", "verdict", "score", "threshold", "inference_ms", "model_id"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in repo.list(category=category, verdict=verdict, batch=batch, limit=10000):
            safe = {
                k: ("'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v)
                for k, v in record.items()
            }
            writer.writerow(safe)
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="defectrag-inspections.csv"'},
        )

    from .inspection_routes import mount_inspection_experience

    mount_inspection_experience(app, repo, local=local_sync or not hasattr(repo, "current"))
    dist = settings.root / "frontend" / "dist"
    if local_sync:
        from .local_frontend import mount_local_frontend

        mount_local_frontend(app, settings.root, dist)
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
    return app


app = create_app() if os.getenv("DEFECTRAG_FACTORY_ONLY") != "1" else None
