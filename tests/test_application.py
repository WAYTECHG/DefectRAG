"""Isolated software tests. Fixtures below are NOT model-performance evidence."""
from io import BytesIO
from pathlib import Path
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.config import Settings, ROOT
from backend.vision import ModelUnavailable
from backend.rag import EvidenceWorkflow

def image_bytes():
    stream=BytesIO();Image.new('RGB',(100,80),'white').save(stream,format='PNG');return stream.getvalue()

class SoftwareDetector:
    def cards(self):return []
    def predict(self,image,category):
        return {'category':category,'verdict':'Anomalous','score':.2,'threshold':.1,'uncertainty_margin':.005,
                'inference_ms':1,'model_id':'software-fixture','scope':'synthetic software fixture'},image
class SoftwareWorkflow:
    def run(self,question,inspection,history=None):
        return {'mode':'retrieval_only','answer':'Software fixture','evidence':[],'claims':[],'trace':['fixture']}

@pytest.fixture
def client(tmp_path):
    app=create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow())
    with TestClient(app) as client:yield client

def upload(client,**kwargs):
    return client.post('/api/inspect',data={'category':'pcb1','batch':'LINE-A',**kwargs},files={'file':('input.png',image_bytes(),'image/png')})

def test_save_filter_alert_report_and_followup(client):
    response=upload(client);assert response.status_code==200
    record=response.json()['data'];identifier=record['id']
    assert client.get('/api/inspections?batch=LINE-A').json()['data'][0]['id']==identifier
    assert client.get('/api/inspections?batch=other').json()['data']==[]
    assert client.get('/api/inspections?batch=%27%20OR%201=1--').json()['data']==[]
    assert client.get(record['heatmap_url']).headers['content-type']=='image/jpeg'
    assert 'score' in client.get(f'/api/inspections/{identifier}/report').text
    alert=client.get('/api/alerts').json()['data'][0]
    assert client.post(f"/api/alerts/{alert['id']}/acknowledge").status_code==200
    assert client.get('/api/alerts').json()['data'][0]['acknowledged']==1
    for question in ['Explain the result','What are its limits?']:
        assert client.post('/api/assistant',json={'inspection_id':identifier,'question':question}).status_code==200
    assert len(client.get(f'/api/inspections/{identifier}/messages').json()['data'])==4
    assert client.get('/api/stats').json()['data']['total']==1
    assert identifier in client.get('/api/export.csv').text

@pytest.mark.parametrize('category',['unknown','../pcb1',''])
def test_invalid_category(client,category):
    assert upload(client,category=category).status_code==422
    assert client.get('/api/stats').json()['data']['total']==0

def test_invalid_image_and_no_persistence(client):
    response=client.post('/api/inspect',data={'category':'pcb1'},files={'file':('bad.jpg',b'not an image','image/jpeg')})
    assert response.status_code==422 and 'error' in response.json()
    assert client.get('/api/inspections').json()['data']==[]

def test_model_failure_is_not_success(tmp_path):
    class Failed(SoftwareDetector):
        def predict(self,*args):raise ModelUnavailable('Missing model')
    with TestClient(create_app(Settings(data=tmp_path),Failed(),SoftwareWorkflow())) as client:
        assert upload(client).status_code==503
        assert client.get('/api/stats').json()['data']['failed_requests']==1
        assert client.get('/api/inspections').json()['data']==[]
        assert client.get('/api/alerts').json()['data']==[]

def test_upload_size_limit(client):
    response=client.post('/api/inspect',data={'category':'pcb1'},files={'file':('big.png',b'x'*(10*1024*1024+1),'image/png')})
    assert response.status_code==413

def test_batch_partial_failure_and_filters(client):
    response=client.post('/api/batch',data={'category':'pcb1','batch':'B-2'},files=[('files',('a.png',image_bytes(),'image/png')),('files',('b.jpg',b'bad','image/jpeg'))])
    result=response.json()['data']
    assert len(result['records'])==1 and len(result['errors'])==1
    assert len(client.get('/api/inspections?batch=B-2&verdict=Anomalous').json()['data'])==1

def test_report_escapes_metadata_and_csv_formula(client):
    record=upload(client,batch='=HYPERLINK("bad")<script>alert(1)</script>').json()['data']
    report=client.get(f"/api/inspections/{record['id']}/report").text
    assert '<script>alert(1)</script>' not in report
    assert '&lt;script&gt;' in report
    assert "'=HYPERLINK" in client.get('/api/export.csv').text

def test_missing_record_and_path_traversal(client):
    assert client.get('/api/inspections/'+'0'*32).status_code==404
    assert client.get('/api/samples/not-permitted.jpg').status_code==404

def test_persistence_across_application_restarts(tmp_path):
    settings=Settings(data=tmp_path)
    with TestClient(create_app(settings,SoftwareDetector(),SoftwareWorkflow())) as first:
        identifier=upload(first).json()['data']['id']
    with TestClient(create_app(settings,SoftwareDetector(),SoftwareWorkflow())) as second:
        assert second.get('/api/inspections/'+identifier).status_code==200

def test_graph_scope_gate_without_llm():
    class NeverRetrieve:
        @property
        def retriever(self):raise AssertionError('Unsupported intent must not call retrieval or generation')
    workflow=EvidenceWorkflow(Settings(),NeverRetrieve())
    answer=workflow.run('What root cause caused this anomaly?',{'category':'pcb1'})
    assert answer['mode']=='abstained' and answer['trace']==['route','abstain']

def test_graph_rejects_fabricated_citation():
    workflow=EvidenceWorkflow(Settings(),None)
    state={'mode':'llm','trace':[], 'raw_claims':[{'text':'invented','source_id':'missing','quote':'a made up quote'}],
           'evidence':[{'chunk_id':'real','text':'This is real supporting evidence.'}]}
    result=workflow.validate_answer(state)
    assert result['mode']=='retrieval_only' and result['claims']==[]

def test_graph_accepts_traceable_claim():
    workflow=EvidenceWorkflow(Settings(),None)
    text='The anomaly score is not a defect probability.'
    result=workflow.validate_answer({'mode':'llm','trace':[],'evidence':[{'chunk_id':'real','text':text}],
                                   'raw_claims':[{'text':text,'source_id':'real','quote':text}]})
    assert result['mode']=='llm' and len(result['claims'])==1

def test_qwen_claim_schema_requires_supporting_quote():
    from backend.rag import GeneratedAnswer
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        GeneratedAnswer.model_validate({'claims':[{'text':'A claim without evidence','source_id':'screening-2'}]})

@pytest.mark.parametrize('raw',['not-json','[]','{"claims": "invalid"}'])
def test_invalid_local_generation_returns_visible_fallback(monkeypatch,raw):
    import httpx
    import backend.rag as rag
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,json):
            assert isinstance(json['format'],dict)
            return httpx.Response(200,json={'response':raw},request=httpx.Request('POST',url))
    monkeypatch.setattr(rag.httpx,'Client',Client)
    workflow=EvidenceWorkflow(Settings(),None)
    answer=workflow.generate({'inspection':{},'question':'Explain anomaly score','evidence':[{'chunk_id':'screening-2'}],'trace':[]})
    assert answer['mode']=='retrieval_only' and answer['error']

def test_missing_llm_keeps_retrieved_evidence(monkeypatch):
    import httpx
    import backend.rag as rag
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,*args,**kwargs):raise httpx.ConnectError('Ollama offline')
    monkeypatch.setattr(rag.httpx,'Client',Client)
    workflow=EvidenceWorkflow(Settings(),None)
    state={'inspection':{},'question':'Explain score','evidence':[{'chunk_id':'s','text':'The score is not a probability.'}],'trace':[]}
    generated=workflow.generate(state)
    answer=workflow.validate_answer({**state,**generated})
    assert answer['mode']=='retrieval_only' and answer['error']

def test_malformed_raw_claims_do_not_crash_validation():
    workflow=EvidenceWorkflow(Settings(),None)
    answer=workflow.validate_answer({'mode':'llm','trace':[],'evidence':[],'raw_claims':{'unexpected':'object'}})
    assert answer['mode']=='retrieval_only'

def test_quoted_passage_cannot_license_invented_number():
    workflow=EvidenceWorkflow(Settings(),None)
    quote='Calibration uses 32 normal validation images.'
    answer=workflow.validate_answer({'mode':'llm','trace':[],'evidence':[{'chunk_id':'real','text':quote}],
        'raw_claims':[{'quote':quote,'source_id':'real','text':'Calibration uses 500 images.'}]})
    assert answer['claims']==[]

def test_graph_retrieval_failure_is_visible():
    class Broken:
        class retriever:
            @staticmethod
            def invoke(question):raise RuntimeError('offline')
    answer=EvidenceWorkflow(Settings(),Broken()).run('Explain this threshold',{'category':'pcb1'})
    assert answer['mode']=='abstained' and 'unavailable' in answer['answer']

def test_final_manifest_has_no_cross_split_identities():
    for category in ('pcb1','capsules','cashew'):
        manifest=json.loads((ROOT/'results'/f'{category}_splits.json').read_text())
        sets={k:{r['sha256'] for r in v} for k,v in manifest.items()}
        assert not sets['train']&sets['validation'] and not sets['train']&sets['test'] and not sets['validation']&sets['test']
        assert all(r['label']=='normal' for r in manifest['train'])
