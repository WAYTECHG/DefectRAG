import numpy as np
import torch
import torch.nn.functional as F
from backend.highres import foreground_mask,score_tokens,restore_map
from scripts.benchmark_highres import select_banks,save_array
from backend.rag import EvidenceWorkflow
from backend.config import Settings
from backend.vision import create_detector,Detector,ModelUnavailable
import json
import pytest


def test_foreground_pca_keeps_center_object_without_annotation():
    rng=np.random.default_rng(42);values=rng.normal(0,.01,(24,32,8))
    values[6:18,8:24,0]=40
    mask=foreground_mask(values.reshape(-1,8),(24,32)).reshape(24,32)
    assert mask[9:15,11:21].all() and not mask[:3,:3].any()


def test_scoring_ignores_background_even_when_its_distance_is_larger():
    features=torch.tensor([[1.,0.],[0.,1.],[-1.,0.]])
    bank=F.normalize(torch.tensor([[1.,0.]]),dim=-1)
    raw,score=score_tokens(features,bank,np.array([True,False,False]))
    assert score==0 and np.array_equal(raw,np.zeros(3))
    _,unmasked=score_tokens(features,bank,np.ones(3,dtype=bool))
    assert unmasked==2


def test_rectangular_map_restores_crop_to_original_coordinates():
    geometry={'grid':(2,3),'cropped':(42,28),'resized':(45,28),'original':(90,56)}
    restored=restore_map(np.ones(6,dtype='float32'),geometry)
    assert restored.shape==(56,90)
    assert restored[:,0].mean()==1 and restored[:,-1].mean()==0


def test_deployment_bank_never_contains_normal_holdout_features(tmp_path):
    files=[]
    for i in range(12):
        path=tmp_path/f'feature{i}.npz'
        values=np.eye(12,dtype='float32')[i][None].repeat(4,axis=0)
        save_array(path,features=values,mask=np.ones(4,dtype=bool));files.append(path)
    banks=select_banks(tmp_path,files,{0,10})
    assert not (banks[3].argmax(1)==0).any() and not (banks[3].argmax(1)==10).any()
    assert (banks[0].argmax(1)==0).any()
    assert not list(tmp_path.glob('*.partial'))


def test_legacy_override_is_available_and_unvalidated_candidate_fails_closed(tmp_path):
    assert isinstance(create_detector(Settings(root=tmp_path,profile='legacy')),Detector)
    path=tmp_path/'models/highres';path.mkdir(parents=True)
    (path/'PROFILE.json').write_text(json.dumps({'status':'pending'}))
    with pytest.raises(ModelUnavailable,match='not validated'):
        create_detector(Settings(root=tmp_path,profile='auto'))


def test_assistant_does_not_cite_the_wrong_model_family():
    workflow=EvidenceWorkflow(Settings(),None)
    sources=[{'id':family,'model_family':family,'chunk_id':family+'-1','url':'https://example.org','license':'test'} for family in ('dinov2','dinov3')]
    output=workflow.validate_evidence({'question':'Explain its heatmap','inspection':{'model_id':'dinov2-highres-pcb1-v1'},'evidence':sources,'trace':[]})
    assert [e['id'] for e in output['evidence']]==['dinov2']
