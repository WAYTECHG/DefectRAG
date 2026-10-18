"""Protect the two-product boundary and consistency of the shipped recall policy."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from backend.calibration import active_evaluation, calibrated_card, MACARONI_FILENAME
from scripts.audit_recall import metrics, quantile

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def manifests(tmp_path,monkeypatch):
    monkeypatch.delenv('DEFECTRAG_CALIBRATION',raising=False)
    (tmp_path/'results').mkdir()
    names=['highres_deployment_evaluation.json','sensitive_deployment_evaluation.json',MACARONI_FILENAME]
    values=[]
    for name in names:
        value=json.loads((ROOT/'results'/name).read_text());values.append(value)
        (tmp_path/'results'/name).write_text(json.dumps(value))
    return tmp_path,*values


def test_default_changes_only_macaroni_cards_and_preserves_previous_manifest(manifests):
    root,baseline,previous,candidate=manifests
    before=deepcopy(previous)
    result=active_evaluation(root,baseline)
    assert result==candidate
    for category,old in previous['categories'].items():
        card=calibrated_card(root,baseline['categories'][category])
        assert card==result['categories'][category]
        if category in ('macaroni1','macaroni2'):
            assert card['threshold']<old['threshold']
            assert card['model_id'].endswith('-q80-v1')
        else:assert card==old
    assert previous==before


def test_previous_policy_can_be_selected_without_removing_files(manifests,monkeypatch):
    root,baseline,previous,_=manifests
    monkeypatch.setenv('DEFECTRAG_CALIBRATION','normal-q95-v1')
    assert active_evaluation(root,baseline)==previous


@pytest.mark.parametrize('category,field,value',[
    ('pcb1','threshold',.01),('macaroni1','bank_sha256','wrong'),
    ('macaroni1','threshold',float('nan')),('macaroni2','threshold',1.0),
    ('macaroni2','previous_model_id','unknown'),('macaroni2','uncertainty_margin',0),
])
def test_wrong_asset_or_out_of_scope_change_is_rejected(manifests,category,field,value):
    root,baseline,_,candidate=manifests
    candidate['categories'][category][field]=value
    (root/'results'/MACARONI_FILENAME).write_text(json.dumps(candidate))
    with pytest.raises(ValueError):active_evaluation(root,baseline)


def test_shipped_metrics_reproduce_from_real_cached_scores_and_normal_only_thresholds(manifests):
    root,baseline,_,candidate=manifests
    for category in ('macaroni1','macaroni2'):
        directory=ROOT/'experiments/dinov2_highres_v1'/category
        if not directory.exists():pytest.skip('Private benchmark caches are not distributed with a source-only clone')
        calibration=json.loads((directory/'normal_calibration.json').read_text())
        rows=json.loads((directory/'test_progress.json').read_text())
        card=active_evaluation(root,baseline)['categories'][category]
        threshold=quantile([r['score'] for r in calibration['predictions']],.8)
        assert threshold==card['threshold']
        actual=metrics(rows,threshold)
        for key,value in actual.items():assert value==card['metrics'][key]
        assert card['metrics']['recall']>=(.85 if category=='macaroni1' else .8)


def test_public_evaluation_and_model_cards_agree_on_the_targeted_policy(manifests):
    from backend.config import Settings
    from backend.main import create_app
    from fastapi.testclient import TestClient
    root,baseline,_,candidate=manifests
    class Metadata:
        profile_name='dinov2_highres_v1'
        def cards(self):return [calibrated_card(root,c) for c in baseline['categories'].values()]
    with TestClient(create_app(Settings(root=root,data=root/'runtime'),detector=Metadata(),workflow=object())) as client:
        assert client.get('/api/evaluation').json()['data']==candidate
        cards={c['category']:c for c in client.get('/api/models').json()['data']}
        assert cards==candidate['categories']
