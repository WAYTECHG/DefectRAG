"""Read-only reference routes: evaluation reports, benchmark results and sample images.

These routes only read files from the project folder. They never touch the inspection
database, so they are kept apart from the inspection and assistant routes in main.py.
"""

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .config import CATEGORIES


def mount_reference_routes(app: FastAPI, settings, detector) -> None:
    @app.get("/api/evaluation")
    def evaluation():
        active = getattr(detector, "profile_name", "legacy") == "dinov2_highres_v1"
        path = settings.root / "results" / ("highres_deployment_evaluation.json" if active else "evaluation.json")
        result = json.loads(path.read_text()) if path.exists() else {"status": "unverified"}
        if active and "categories" in result:
            from .calibration import active_evaluation

            result = active_evaluation(settings.root, result)
        profile = settings.root / "results" / "serving_profile.json"
        if profile.exists() and not active:
            result["serving_profile"] = json.loads(profile.read_text())
        return {"data": result}

    @app.get("/api/samples")
    def samples():
        return {
            "data": [
                {
                    "name": p.stem,
                    "category": p.stem.rsplit("_", 1)[0],
                    "url": "/api/samples/" + p.name,
                    "attribution": "VisA, Zou et al., ECCV 2022; CC BY 4.0; resized preview",
                    "source": "https://github.com/amazon-science/spot-diff",
                }
                for p in sorted((settings.root / "samples").glob("*.jpg"))
            ]
        }

    @app.get("/api/samples/{name}")
    def sample(name: str):
        if name not in {f"{category}_{kind}.jpg" for category in CATEGORIES for kind in ("good", "anomalous")}:
            raise HTTPException(404, "Sample not found")
        path = settings.root / "samples" / name
        if not path.exists():
            raise HTTPException(404, "Sample not available")
        return FileResponse(path)

    @app.get("/api/benchmark/official")
    def official_benchmark():
        path = settings.root / "results/official_evaluation.json"
        progress = settings.root / "experiments/official_visa_v1/evaluation.json"
        source = path if path.exists() else progress
        report = json.loads(source.read_text()) if source.exists() else {"categories": {}, "status": "not_run"}
        candidate = settings.root / "results/highres_evaluation.json"
        candidate_progress = settings.root / "experiments/dinov2_highres_v1/evaluation.json"
        candidate_source = candidate if candidate.exists() else candidate_progress
        if candidate_source.exists():
            report["candidate"] = json.loads(candidate_source.read_text())
        return {"data": report}
