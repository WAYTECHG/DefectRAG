"""Decision-policy integration regressions; no synthetic inference claims."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from backend.calibration import active_evaluation, calibrated_card, FILENAME
from scripts.audit_recall import metrics, quantile

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def manifests(tmp_path, monkeypatch):
    monkeypatch.delenv('DEFECTRAG_CALIBRATION', raising=False)
    directory = tmp_path / 'results'
    directory.mkdir()
    baseline = json.loads((ROOT/'results/highres_deployment_evaluation.json').read_text())
    candidate = json.loads((ROOT/'results'/FILENAME).read_text())
    (directory/'highres_deployment_evaluation.json').write_text(json.dumps(baseline))
    (directory/FILENAME).write_text(json.dumps(candidate))
    return tmp_path, baseline, candidate


def test_local_and_public_metadata_select_identical_versioned_thresholds(manifests):
    root, baseline, candidate = manifests
    before = deepcopy(baseline)
    active = active_evaluation(root, baseline)
    for category, original in baseline['categories'].items():
        card = calibrated_card(root, original)
        assert card == active['categories'][category] == candidate['categories'][category]
        assert card['threshold'] < original['threshold']
        assert card['encoder_sha256'] == original['encoder_sha256']
        assert card['bank_sha256'] == original['bank_sha256']
        assert card['model_id'].endswith('-q95-v1')
    assert baseline == before


def test_rollback_restores_original_thresholds_without_rewriting_assets(manifests, monkeypatch):
    root, baseline, _ = manifests
    monkeypatch.setenv('DEFECTRAG_CALIBRATION', 'normal-max-v1')
    assert active_evaluation(root, baseline) == baseline
    assert calibrated_card(root, baseline['categories']['pcb2']) == baseline['categories']['pcb2']


@pytest.mark.parametrize('field,value', [('bank_sha256','wrong-bank'), ('threshold',float('nan')),
    ('threshold',1.0), ('model_id','unversioned-model'), ('uncertainty_margin',0.0), ('baseline_threshold',0.0)])
def test_wrong_asset_or_invalid_threshold_fails_closed(manifests, field, value):
    root, baseline, candidate = manifests
    candidate['categories']['pcb2'][field] = value
    (root/'results'/FILENAME).write_text(json.dumps(candidate))
    with pytest.raises(ValueError):
        active_evaluation(root, baseline)


def test_missing_optional_manifest_preserves_original_behavior(manifests):
    root, baseline, _ = manifests
    (root/'results'/FILENAME).unlink()
    assert active_evaluation(root, baseline) == baseline


def test_unknown_policy_is_not_silently_accepted(manifests, monkeypatch):
    root, baseline, _ = manifests
    monkeypatch.setenv('DEFECTRAG_CALIBRATION','typo')
    with pytest.raises(ValueError,match='Unknown'):
        active_evaluation(root,baseline)


def test_binary_comparison_counts_threshold_equality_as_anomalous():
    rows = [{'label':label,'scores':[0,0,0,score]} for label,score in [(0,.1),(0,.2),(1,.2),(1,.3)]]
    assert metrics(rows,.2)['confusion_matrix'] == [[1,1],[0,2]]
    assert metrics(rows,.2)['recall'] == 1
    assert metrics(rows,.2)['precision'] == 2/3
    assert quantile([0,1,2,3],.95) == pytest.approx(2.85)


def test_evaluation_endpoint_reports_the_active_policy(manifests):
    from backend.config import Settings
    from backend.main import create_app
    from fastapi.testclient import TestClient
    root, baseline, candidate = manifests
    class Metadata:
        profile_name = 'dinov2_highres_v1'
        def cards(self):
            return [calibrated_card(root,card) for card in baseline['categories'].values()]
    with TestClient(create_app(Settings(root=root,data=root/'runtime'),detector=Metadata(),workflow=object())) as client:
        evaluation = client.get('/api/evaluation').json()['data']
        models = client.get('/api/models').json()['data']
        assert evaluation == candidate
        assert {card['category']:card['threshold'] for card in models} == {
            key:card['threshold'] for key,card in evaluation['categories'].items()}
