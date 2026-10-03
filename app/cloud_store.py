from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from app.config import (
    CLOUDINARY_URL,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
    RESULTS_DIR,
    STORE_ORIGINAL_UPLOADS,
)

logger = logging.getLogger("defectrag.cloud")


class AuraStore:
    """Small Neo4j Aura persistence adapter with a disabled-safe default."""

    def __init__(self) -> None:
        self.enabled = bool(NEO4J_URI and NEO4J_PASSWORD)
        self._driver = None

    def _get_driver(self):
        if not self.enabled:
            return None
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
                max_connection_pool_size=10,
                connection_timeout=10,
            )
        return self._driver

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"configured": False, "available": False}
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            return {"configured": True, "available": True, "database": NEO4J_DATABASE}
        except Exception as exc:
            logger.warning("AuraDB health check failed: %s", exc)
            return {"configured": True, "available": False, "database": NEO4J_DATABASE}

    def save_inspection(self, result: dict[str, Any], input_asset_url: str | None = None) -> None:
        driver = self._get_driver()
        if driver is None:
            return
        visual = result.get("visual_reasoning") or {}
        artifacts = result.get("artifacts") or {}
        sources = result.get("sources") or []
        parameters = {
            "id": result["job_id"],
            "category": result.get("category", "unknown"),
            "verdict": result.get("verdict", "unknown"),
            "score": float(result.get("anomaly_score", 0.0)),
            "threshold": float(result.get("threshold", 0.0)),
            "patch_row": int((result.get("max_patch") or {}).get("row", -1)),
            "patch_column": int((result.get("max_patch") or {}).get("column", -1)),
            "bounding_box_json": json.dumps(result.get("bounding_box") or {}, ensure_ascii=False),
            "visual_json": json.dumps(visual, ensure_ascii=False),
            "explanation": result.get("explanation", ""),
            "input_url": input_asset_url,
            "location_url": artifacts.get("location"),
            "heatmap_url": artifacts.get("heatmap"),
            "reference_url": (result.get("reference_example") or {}).get("url"),
            "sources": [
                {
                    "rank": int(source.get("rank", index + 1)),
                    "source_id": str(source.get("id") or f"{result['job_id']}:{index + 1}"),
                    "title": str(source.get("title") or "Untitled evidence"),
                    "origin": str(source.get("source") or "unknown"),
                    "text": str(source.get("text") or ""),
                    "score": float(source.get("score") or 0.0),
                }
                for index, source in enumerate(sources)
            ],
        }
        query = """
        MERGE (category:ProductCategory {id: $category})
        CREATE (inspection:Inspection {
          id: $id, verdict: $verdict, anomaly_score: $score,
          operating_threshold: $threshold, patch_row: $patch_row,
          patch_column: $patch_column, bounding_box_json: $bounding_box_json,
          visual_reasoning_json: $visual_json, explanation: $explanation,
          input_asset_url: $input_url, location_asset_url: $location_url,
          heatmap_asset_url: $heatmap_url, reference_asset_url: $reference_url,
          created_at: datetime()
        })
        CREATE (inspection)-[:INSPECTED_AS]->(category)
        WITH inspection
        UNWIND $sources AS source
        MERGE (evidence:Evidence {id: source.source_id})
        ON CREATE SET evidence.title = source.title, evidence.source = source.origin, evidence.text = source.text
        CREATE (inspection)-[:SUPPORTED_BY {rank: source.rank, score: source.score}]->(evidence)
        """
        driver.execute_query(query, parameters_=parameters, database_=NEO4J_DATABASE)

    def save_contact(self, name: str, email: str, topic: str, message: str) -> str:
        import uuid

        driver = self._get_driver()
        if driver is None:
            raise RuntimeError("Cloud contact storage is not configured.")
        message_id = uuid.uuid4().hex
        driver.execute_query(
            """
            CREATE (:SupportMessage {
              id: $id, name: $name, email: $email, topic: $topic,
              message: $message, status: 'new', created_at: datetime()
            })
            """,
            id=message_id,
            name=name,
            email=email,
            topic=topic,
            message=message,
            database_=NEO4J_DATABASE,
        )
        return message_id

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None


class CloudMediaStore:
    def __init__(self) -> None:
        self.enabled = bool(CLOUDINARY_URL)

    def upload(self, path: str | Path, *, job_id: str, kind: str) -> str:
        if not self.enabled:
            raise RuntimeError("Cloud media storage is not configured.")
        import cloudinary.uploader

        response = cloudinary.uploader.upload(
            str(path),
            folder=f"defectrag/{job_id}",
            public_id=kind,
            overwrite=True,
            resource_type="image",
        )
        return str(response["secure_url"])


aura_store = AuraStore()
media_store = CloudMediaStore()


def cloud_health(*, verify_database: bool = False) -> dict[str, Any]:
    return {
        "database": aura_store.health() if verify_database else {"configured": aura_store.enabled, "available": None},
        "media": {"configured": media_store.enabled},
    }


def persist_inspection(result: dict[str, Any], input_path: str | Path) -> dict[str, Any]:
    """Upload durable media, then store inspection metadata and evidence in AuraDB."""
    stored = copy.deepcopy(result)
    status = {"database": "disabled", "media": "disabled"}
    input_asset_url = None

    if media_store.enabled:
        try:
            job_id = stored["job_id"]
            artifacts = stored.get("artifacts") or {}
            if STORE_ORIGINAL_UPLOADS:
                input_asset_url = media_store.upload(input_path, job_id=job_id, kind="original")
            for key in ("location", "heatmap"):
                local_url = artifacts.get(key)
                if local_url and local_url.startswith("/artifacts/"):
                    local_path = RESULTS_DIR / "/".join(local_url.split("/")[2:])
                    if local_path.exists():
                        artifacts[key] = media_store.upload(local_path, job_id=job_id, kind=key)
            status["media"] = "stored"
        except Exception as exc:
            logger.exception("Cloud media persistence failed")
            status["media"] = "error"
            status["media_error"] = str(exc)

    if aura_store.enabled:
        try:
            aura_store.save_inspection(stored, input_asset_url=input_asset_url)
            status["database"] = "stored"
        except Exception as exc:
            logger.exception("AuraDB inspection persistence failed")
            status["database"] = "error"
            status["database_error"] = str(exc)

    stored["persistence"] = status
    return stored
