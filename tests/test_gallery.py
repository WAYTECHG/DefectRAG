"""Gallery privacy/consent tests. Software fixtures are not performance results."""
import base64
from io import BytesIO
import json

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.config import Settings
from backend.gallery import LocalGallery, SupabaseGallery, public_measurement, thumbnail
from backend.main import create_app
from tests.test_application import SoftwareDetector, SoftwareWorkflow, image_bytes


@pytest.fixture
def setup(tmp_path):
    gallery=LocalGallery(tmp_path/'public.sqlite3','a'*64)
    app=create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),gallery=gallery)
    with TestClient(app) as client:
        record=client.post('/api/inspect',data={'category':'pcb1','batch':'PRIVATE-BATCH'},
            files={'file':('private-file.png',image_bytes(),'image/png')}).json()['data']
        yield client,gallery,app,record


def publish(client,record,**kwargs):
    return client.post(f"/api/inspections/{record['id']}/publication",json={'consent':True,**kwargs})


def test_disabled_does_not_break_private_history(tmp_path):
    with TestClient(create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow())) as client:
        assert client.get('/api/gallery').json()['data']=={'enabled':False,'items':[]}
        assert client.post('/api/inspections/'+'a'*32+'/publication',json={'consent':True}).status_code==503
        assert client.get('/api/inspections').status_code==200


@pytest.mark.parametrize('body',[{}, {'consent':False},{'consent':'true'}, {'consent':True,'score':1}])
def test_explicit_strict_consent_only(setup,body):
    client,_,_,record=setup
    assert client.post(f"/api/inspections/{record['id']}/publication",json=body).status_code==422
    assert client.get('/api/gallery').json()['data']['items']==[]


def test_public_snapshot_allowlist_idempotency_and_durability(setup):
    client,gallery,app,record=setup
    assert client.get('/api/gallery').json()['data']['items']==[]
    first=publish(client,record).json()['data']; second=publish(client,record).json()['data']
    assert first==second and first['id']!=record['id']
    listing=client.get('/api/gallery').json()['data']['items']
    assert len(listing)==1 and 'image' not in listing[0]
    public=client.get('/api/gallery/'+first['id']).json()['data']
    assert public['measurement']['score']==record['score']
    serialized=json.dumps(public)
    for private in ('PRIVATE-BATCH','private-file.png',record['id'],'owner_id','image_url','conversation','request_fingerprint'):
        assert private not in serialized
    assert set(public)=={'id','created_at','measurement','image','heatmap'}
    assert Image.open(BytesIO(base64.b64decode(public['image']))).format=='JPEG'
    restarted=LocalGallery(gallery.path,'a'*64)
    assert restarted.read(first['id'])==[public]
    assert app.state.repo.get(record['id'])['batch']=='PRIVATE-BATCH'


def test_withdraw_removes_public_access_preserves_private(setup):
    client,_,app,record=setup
    published=publish(client,record).json()['data']
    assert client.post('/api/gallery/'+published['id']+'/withdraw').status_code==200
    assert client.get('/api/gallery/'+published['id']).status_code==404
    assert client.get('/api/gallery').json()['data']['items']==[]
    assert app.state.repo.get(record['id']) is not None
    assert publish(client,record).json()['data']['visible']==0


def test_other_publisher_cannot_withdraw_and_guest_cannot_moderate(setup):
    client,gallery,_,record=setup
    other=gallery.write('publish',gallery.identity('someone-else'),gallery.identity('other'),public_measurement(record),'abc','abc')
    assert client.post('/api/gallery/'+other['id']+'/withdraw').status_code==404
    assert client.post('/api/gallery/'+other['id']+'/moderate').status_code==403
    assert gallery.read(other['id'])


def test_missing_inspection_cannot_publish(setup):
    client,_,_,_=setup
    assert client.post('/api/inspections/'+'b'*32+'/publication',json={'consent':True}).status_code==404
    assert client.post('/api/inspections/../publication',json={'consent':True}).status_code in (404,405)
    assert client.get('/api/gallery?offset=-1').status_code==422
    assert client.get('/api/gallery/not-an-id').status_code==404


def test_capacity_and_pagination(setup):
    _,gallery,_,record=setup
    for i in range(15):gallery.write('publish',str(i),str(i),public_measurement(record),'abc','abc')
    assert len(gallery.read())==12 and len(gallery.read(offset=12))==3
    for i in range(5):gallery.write('publish','limited',str(i),public_measurement(record),'abc','abc')
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:gallery.write('publish','limited','new',public_measurement(record),'abc','abc')
    assert exc.value.status_code==429


def test_preview_strips_metadata_and_caps_dimensions():
    image=Image.new('RGB',(900,600),'red');exif=Image.Exif();exif[270]='PRIVATE DESCRIPTION';out=BytesIO()
    image.save(out,format='JPEG',exif=exif)
    public=Image.open(BytesIO(base64.b64decode(thumbnail(out.getvalue()))))
    assert max(public.size)<=512 and not public.getexif()


@pytest.mark.parametrize('value',[float('nan'),float('inf'),True,'0.3'])
def test_invalid_saved_measurement_rejected(value):
    from fastapi import HTTPException
    with pytest.raises(HTTPException):public_measurement({'category':'pcb1','verdict':'Good','score':value,'threshold':0.4})


def test_supabase_error_never_echoes_secret(monkeypatch):
    class Reply:
        is_success=False
        headers={'content-type':'application/json'}
        def json(self):return {'code':'42501','message':'PRIVATE-KEY'}
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,*args,**kwargs):return Reply()
    monkeypatch.setattr('backend.gallery.httpx.Client',Client)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:SupabaseGallery({'url':'https://example.com','key':'public'},'b'*64).read()
    assert 'PRIVATE-KEY' not in str(exc.value.detail) and 'b'*64 not in str(exc.value.detail)


def test_sql_grants_no_table_access_or_staff_mutation():
    from pathlib import Path
    sql=Path('deployment/supabase_public_gallery.sql').read_text()
    assert 'set search_path = \'\'' in sql
    assert 'key_hash=encode(sha256' in sql
    assert 'pg_advisory_xact_lock' in sql
    assert 'revoke all on public.defectrag_gallery_config' in sql
    assert 'alter table public.shared_inspections' not in sql
    assert 'service_role' not in sql


def test_guest_workspaces_share_only_opted_in_gallery(tmp_path):
    from deployment.space.sessions import SessionRepository, identity
    from backend.storage import SQLiteRepository
    shared=LocalGallery(tmp_path/'gallery.sqlite3','c'*64)
    repo=SessionRepository(tmp_path/'sessions',artifacts=tmp_path/'artifacts')
    # The middleware below models the same scoped session context as the Space.
    app=create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=repo,gallery=shared)
    @app.middleware('http')
    async def context(request,call_next):
        with identity(request.headers.get('X-DefectRAG-Session','a'*64)):
            return await call_next(request)
    with TestClient(app) as client:
        first=client.post('/api/inspect',data={'category':'pcb1'},files={'file':('guest.png',image_bytes(),'image/png')}).json()['data']
        second_headers={'X-DefectRAG-Session':'b'*64}
        assert client.get('/api/inspections',headers=second_headers).json()['data']==[]
        assert client.get('/api/gallery',headers=second_headers).json()['data']['items']==[]
        assert client.post('/api/inspections/'+first['id']+'/publication',headers=second_headers,json={'consent':True}).status_code==404
        publication=publish(client,first).json()['data']
        assert client.get('/api/gallery',headers=second_headers).json()['data']['items'][0]['id']==publication['id']
        assert client.get('/api/inspections/'+first['id'],headers=second_headers).status_code==404
        assert client.post('/api/gallery/'+publication['id']+'/withdraw',headers=second_headers).status_code==404
        assert client.post('/api/gallery/'+publication['id']+'/withdraw').status_code==200
        assert client.get('/api/gallery/'+publication['id'],headers=second_headers).status_code==404


def test_supabase_publishable_header_and_server_only_capability(monkeypatch):
    calls=[]
    class Reply:
        is_success=True
        def json(self):return []
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,*args,**kwargs):calls.append(kwargs);return Reply()
    monkeypatch.setattr('backend.gallery.httpx.Client',Client)
    remote=SupabaseGallery({'url':'https://example.com','key':'sb_publishable_example'},'d'*64)
    remote.read();remote.write('status','e'*64,'f'*64)
    assert calls[0]['headers']=={'apikey':'sb_publishable_example'}
    assert 'p_key' not in calls[0]['json']
    assert calls[1]['json']['p_key']=='d'*64
