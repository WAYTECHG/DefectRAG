"""Software integration checks; these fixtures do not measure model performance."""
import pytest
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app
from backend.reviews import parse_review,review_body
from tests.test_application import SoftwareDetector,SoftwareWorkflow,image_bytes

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow())) as value:
        yield value

def upload(client,category='pcb1',batch='QA'):
    return client.post('/api/inspect',data={'category':category,'batch':batch},files={'file':('input.png',image_bytes(),'image/png')}).json()['data']

def test_export_applies_all_filters_without_changing_all_export(client):
    first=upload(client);second=upload(client,'candle','OTHER')
    assert first['id'] in client.get('/api/export.csv?category=pcb1&batch=QA&verdict=Anomalous').text
    assert second['id'] not in client.get('/api/export.csv?category=pcb1').text
    assert first['id'] not in client.get('/api/export.csv?verdict=Good').text
    assert second['id'] in client.get('/api/export.csv').text

def test_review_audit_does_not_change_model_and_survives_report(client):
    original=upload(client);identifier=original['id']
    for status,decision in [('In review','Pending'),('Reviewed','Hold')]:
        response=client.post(f'/api/inspections/{identifier}/review',json={'status':status,'decision':decision,'note':'<script>not executable</script>'})
        assert response.status_code==200 and response.json()['data']['created_at']
    reviews=client.get(f'/api/inspections/{identifier}/reviews').json()['data']
    assert len(reviews)==2 and reviews[-1]['decision']=='Hold'
    assert client.get(f'/api/inspections/{identifier}').json()['data']==original
    report=client.get(f'/api/inspections/{identifier}/report').text
    assert 'Human review' in report and 'Hold' in report and '&lt;script&gt;' in report
    assert '<script>not executable</script>' not in report

def test_invalid_review_and_archived_target_cannot_create_decision(client):
    identifier=upload(client)['id']
    assert client.post(f'/api/inspections/{identifier}/review',json={'status':'Reviewed','decision':'Pending'}).status_code==422
    client.post('/api/history/archive',json={'confirmation':'ARCHIVE'})
    assert client.post(f'/api/inspections/{identifier}/review',json={'status':'Reviewed','decision':'Hold'}).status_code==404

def test_report_does_not_render_internal_urls_or_owner_as_measurements(client):
    record=upload(client)
    # Report uses an explicit scalar-field allowlist; image URLs still belong in img attributes.
    report=client.get(f"/api/inspections/{record['id']}/report").text
    assert '<th>image url</th>' not in report and '<th>owner id</th>' not in report
    assert '<th>report url</th>' not in report and '<img src=' in report

def test_review_notes_ignore_forged_actor_fields():
    parsed=parse_review(review_body('Reviewed','Reject','Human observation'))
    assert parsed=={'status':'Reviewed','decision':'Reject','note':'Human observation'}

def test_replayed_batch_item_reuses_saved_result_without_inference(tmp_path):
    class CountingDetector(SoftwareDetector):
        calls=0
        def predict(self,*args):
            self.calls+=1
            return super().predict(*args)
    detector=CountingDetector()
    with TestClient(create_app(Settings(data=tmp_path),detector,SoftwareWorkflow())) as client:
        def send(category='pcb1'):
            return client.post('/api/inspect',data={'category':category,'batch':'RESUME','request_id':'a'*32},files={'file':('input.png',image_bytes(),'image/png')})
        first=send();second=send()
        assert first.status_code==second.status_code==200
        assert first.json()['data']==second.json()['data'] and detector.calls==1
        assert send('candle').status_code==409 and detector.calls==1
