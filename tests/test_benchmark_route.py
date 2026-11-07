"""The Official benchmark route serves the VisA reports and, when present, the MVTec AD summary."""

import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.routes_reference import mount_reference_routes


def client(root):
    app = FastAPI()
    mount_reference_routes(app, Settings(root=root), SimpleNamespace(profile_name="dinov2_tuned_v1"))
    return TestClient(app)


def test_the_mvtec_summary_is_served_when_it_exists(tmp_path):
    (tmp_path / "results").mkdir()
    summary = {"dataset": "MVTec AD", "products": 15, "macro_mean": {"A_random_frozen": {"auroc": 0.986}}}
    (tmp_path / "results" / "mvtec_summary.json").write_text(json.dumps(summary))
    data = client(tmp_path).get("/api/benchmark/official").json()["data"]
    assert data["mvtec"] == summary


def test_the_route_still_works_without_the_mvtec_summary(tmp_path):
    data = client(tmp_path).get("/api/benchmark/official").json()["data"]
    assert "mvtec" not in data and data["status"] == "not_run"
