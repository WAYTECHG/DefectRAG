"""MFA-compatible public snapshots use authenticated bytes, never relative-URL fetches."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.gallery import LocalGallery
from backend.main import create_app
from tests.test_application import SoftwareDetector,SoftwareWorkflow,image_bytes


class CloudFixture:
    config={'auth_workflow_enabled':True}
    cloud_config={'url':'https://fixture.invalid'}
    staff={'role':'staff'}
    user={'id':'fixture-owner'}
    def __init__(self,owner='fixture-owner',denied=False):self.owner,self.denied,self.reads=owner,denied,[]
    def current(self):return self
    def get(self,identifier):
        return {'id':identifier,'storage':'supabase_personal','owner_id':self.owner,
                'category':'pcb1','verdict':'Anomalous','score':.2,'threshold':.1,
                'image_url':'/api/inspections/'+identifier+'/image','heatmap_url':'/api/inspections/'+identifier+'/heatmap'}
    def private_artifact(self,identifier,kind):
        self.reads.append((identifier,kind))
        if self.denied:raise HTTPException(403,'Private artifact denied')
        return image_bytes()


@pytest.mark.parametrize('owner,denied,expected',[('fixture-owner',False,200),('other-owner',False,403),('fixture-owner',True,403)])
def test_authenticated_gallery_publication_preserves_owner_and_private_read_checks(tmp_path,owner,denied,expected):
    repo=CloudFixture(owner,denied);gallery=LocalGallery(tmp_path/'gallery.sqlite3','a'*64)
    app=create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=repo,gallery=gallery)
    with TestClient(app) as client:
        response=client.post('/api/inspections/'+'1'*32+'/publication',json={'consent':True})
        assert response.status_code==expected
        if expected==200:
            assert repo.reads==[('1'*32,'image'),('1'*32,'heatmap')]
            item=client.get('/api/gallery/'+response.json()['data']['id']).json()['data']
            assert item['measurement']['score']==.2 and 'owner_id' not in item
        else:assert gallery.read()==[]
