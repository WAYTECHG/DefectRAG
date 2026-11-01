"""Shared pytest setup.

A fresh GitHub clone (and the GitHub Actions CI run) has no model weights: they
are large and are downloaded separately with `python -m scripts.fetch_public_assets`.
Tests that build the full app need the local text-embedding model, so on such a
checkout they are skipped with a printed reason instead of failing. On a full
installation (models/embedding present) every test runs as before.
"""
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
HAS_MODELS = (ROOT / 'models' / 'embedding').is_dir()

# Test files that create the whole application at import time.
NEEDS_MODELS = [
    'test_application.py', 'test_auth_gallery.py', 'test_gallery.py', 'test_history_archive.py',
    'test_inspection_ux.py', 'test_local_sync.py', 'test_workflow_fixes.py',
]
# Single tests elsewhere that start the app.
NEEDS_MODELS_TESTS = {
    'test_calibration_policy.py::test_evaluation_endpoint_reports_the_active_policy',
    'test_macaroni_policy.py::test_public_evaluation_and_model_cards_agree_on_the_targeted_policy',
}

collect_ignore = [] if HAS_MODELS else NEEDS_MODELS


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
