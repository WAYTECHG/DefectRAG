"""Shared pytest setup.

A fresh GitHub clone (and the GitHub Actions CI run) has no model weights: they
are large and are downloaded separately with `python -m scripts.fetch_public_assets`.
Tests that build the full app need the local text-embedding model, so on such a
checkout they are skipped with a printed reason instead of failing. On a full
installation (models/embedding present) every test runs as before.
"""
from pathlib import Path
import os
import sys
import pytest

# `import backend.main` normally builds the real application (detector and knowledge
# index) at import time. Tests build their own app with fakes through create_app(),
# so importing the module must not load model files.
os.environ.setdefault('DEFECTRAG_FACTORY_ONLY', '1')

ROOT = Path(__file__).resolve().parents[1]
# DEFECTRAG_SIMULATE_CI=1 pretends the model files are absent, to reproduce the CI run locally.
HAS_MODELS = (ROOT / 'models' / 'embedding').is_dir() and os.getenv('DEFECTRAG_SIMULATE_CI') != '1'

# Test files that create the whole application at import time.
NEEDS_MODELS = []
# Single tests elsewhere that start the app.
NEEDS_MODELS_TESTS = {
    'test_calibration_policy.py::test_evaluation_endpoint_reports_the_active_policy',
    'test_macaroni_policy.py::test_public_evaluation_and_model_cards_agree_on_the_targeted_policy',
}

collect_ignore = [] if HAS_MODELS else NEEDS_MODELS


@pytest.fixture
def client(tmp_path):
    """A test client for an app that uses software fixtures instead of real models."""
    from fastapi.testclient import TestClient
    from backend.config import Settings
    from backend.main import create_app
    from tests.test_application import SoftwareDetector, SoftwareWorkflow
    app = create_app(Settings(data=tmp_path), SoftwareDetector(), SoftwareWorkflow())
    with TestClient(app) as test_client:
        yield test_client


def pytest_report_header(config):
    if not HAS_MODELS:
        return 'models/embedding not found: %d app-level test files skipped (fresh clone / CI).' % len(NEEDS_MODELS)


# The Desktop sync script is a Windows operator tool (it defaults to a C:\ path).
WINDOWS_ONLY = {'test_desktop_sync.py'}


def pytest_collection_modifyitems(config, items):
    no_models = pytest.mark.skip(reason='needs local model files (models/embedding); run on a full installation')
    not_windows = pytest.mark.skip(reason='Windows-only Desktop sync tool')
    for item in items:
        name = item.nodeid.split('/')[-1]
        if not HAS_MODELS and name in NEEDS_MODELS_TESTS:
            item.add_marker(no_models)
        if sys.platform != 'win32' and name.split('::')[0] in WINDOWS_ONLY:
            item.add_marker(not_windows)
