"""Software/transport fixtures only. No model, Supabase write or email calls."""
import copy
import hashlib
import json
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app
from backend.local_sync import LocalMirror,LocalSyncRepository,SyncEngine
from deployment.space.sessions import identity
from tests.test_application import SoftwareDetector,SoftwareWorkflow,image_bytes

OWNER='11111111-1111-4111-8111-111111111111'
OTHER='22222222-2222-4222-8222-222222222222'

def record(identifier='a'*32):
    return {'id':identifier,'created_at':'2026-10-22T00:00:00+00:00','category':'pcb1','verdict':'Anomalous','batch':'SYNC-QA',
            'score':.2,'threshold':.1,'model_id':'software-fixture','request_fingerprint':'fixture-'+identifier}

def mirror(tmp_path,owner=OWNER):
    local=LocalMirror(tmp_path/owner/'inspection.sqlite3',owner,tmp_path/owner/'artifacts')
    return local

def save(local,identifier='a'*32):
    for suffix in ('','_heatmap'):(local.artifacts/(identifier+suffix+'.jpg')).write_bytes(b'fixture-'+suffix.encode())
    return local.save(record(identifier))

class Cloud:
    bucket='personal-inspections'
    def __init__(self,owner=OWNER):
        self.user={'id':owner};self.staff={'role':'staff','display_name':'QA owner'}
        self.rows={};self.objects={};self.receipts={};self.calls=[];self.fail=False;self.lose_reply=False
    def _upload(self,bucket,identifier,kind,path):
        value=path.read_bytes();name=f'{self.user["id"]}/{identifier}/{kind}-{hashlib.sha256(value).hexdigest()}.jpg'
        self.objects[name]=value;return name
    def _read_private_image(self,path):return self.objects[path]
    def request(self,method,path,**kwargs):
        self.calls.append((method,path,kwargs))
        if self.fail:raise RuntimeError('Private fixture URL/token must not persist')
        if path.endswith('defectrag_personal_sync_apply'):
            p=kwargs['json'];op=p['p_operation'];identifier=p['p_id'];action=p['p_action'];data=p['p_data']
            if op in self.receipts:return self.receipts[op]
            previous=self.rows.get(identifier)
            if (action=='create' and previous) or (action!='create' and (not previous or previous['sync_version']!=p['p_base'])):return {'conflict':True}
            if action=='create':
                self.rows[identifier]={'id':identifier,'owner_id':self.user['id'],'created_at':data['record']['created_at'],'payload':data['record'],
                    'image_path':data['image_path'],'heatmap_path':data['heatmap_path'],'conversation':[],'archived_at':None,'sync_version':1,'notes':[]}
            else:
                previous['sync_version']+=1
                if action=='conversation':previous['conversation'] += [{'role':'user','question':data['question']},{'role':'assistant',**data['answer']}]
                if action=='acknowledge':previous['payload']['alert_acknowledged']=True
                if action=='archive':previous['archived_at']='2026-10-22T01:00:00Z'
                if action=='restore':previous['archived_at']=None
                if action=='review':previous['notes'].append({'id':op,'inspection_id':identifier,'author_id':self.user['id'],'created_at':'2026-10-22T01:00:00Z','body':data['body']})
            answer={'version':self.rows[identifier]['sync_version']};self.receipts[op]=answer
            if self.lose_reply:self.lose_reply=False;raise RuntimeError('Response lost after commit')
            return answer
        params=kwargs.get('params',{})
        if path.endswith('personal_inspections'):
            assert params['owner_id']=='eq.'+self.user['id']
            values=list(self.rows.values())
            if 'id' in params:
                operation,value=params['id'].split('.',1);values=[r for r in values if (r['id']==value if operation=='eq' else r['id']>value)]
            return copy.deepcopy(sorted(values,key=lambda row:row['id'])[:int(params.get('limit',100))])
        if path.endswith('personal_notes'):
            assert params['author_id']=='eq.'+self.user['id']
            offset=int(params.get('offset',0));limit=int(params.get('limit',1000))
            return copy.deepcopy(self.rows[params['inspection_id'][3:]]['notes'][offset:offset+limit])
        raise AssertionError('Unexpected/possibly shared-table request '+path)

def due(local):
    with local.connect() as db:db.execute("UPDATE sync_queue SET due=0 WHERE state='pending'")

def test_local_write_and_queue_are_atomic_and_account_isolated(tmp_path):
    a=mirror(tmp_path);b=mirror(tmp_path,OTHER);save(a)
    assert a.get('a'*32)['owner_id']==OWNER and b.get('a'*32) is None
    assert a.status()['pending']==1 and b.status()['pending']==0
    with a.connect() as db:
        db.execute("CREATE TRIGGER deny_queue BEFORE INSERT ON sync_queue BEGIN SELECT RAISE(ABORT,'queue unavailable'); END")
    with pytest.raises(Exception):save(a,'b'*32)
    assert a.get('b'*32) is None

def test_completed_local_inspection_uploads_privately_and_downloads_to_another_device(tmp_path):
    a=mirror(tmp_path/'device-a');save(a);cloud=Cloud();first=SyncEngine(a,cloud).cycle()
    b=mirror(tmp_path/'device-b');second=SyncEngine(b,cloud).cycle()
    assert first['pending']==0 and second['state']=='synced'
    assert b.get('a'*32)['score']==.2 and (b.artifacts/('a'*32+'.jpg')).read_bytes()==b'fixture-'
    assert not any('shared_inspections' in path or 'team-inspections' in path for _,path,_ in cloud.calls)
    assert b.status()['pending']==0,'Downloading must not enqueue its own upload'

def test_response_loss_replays_operation_without_duplicate_cloud_records(tmp_path):
    local=mirror(tmp_path);save(local);cloud=Cloud();cloud.lose_reply=True;engine=SyncEngine(local,cloud)
    assert engine.cycle()['pending']==1 and len(cloud.rows)==1
    due(local);assert engine.cycle()['pending']==0
    assert len(cloud.receipts)==1 and len(cloud.rows)==1

def test_retry_backoff_survives_restart_and_never_records_credentials(tmp_path):
    local=mirror(tmp_path);save(local);cloud=Cloud();cloud.fail=True
    result=SyncEngine(local,cloud).cycle();assert result['pending']==1
    with local.connect() as db:
        saved=dict(db.execute('SELECT * FROM sync_queue').fetchone())
        assert saved['attempts']==1 and saved['due']>0 and 'token' not in saved['error']
    reopened=mirror(tmp_path);assert reopened.status()['pending']==1
    before=len(cloud.calls);SyncEngine(reopened,cloud).cycle();assert len(cloud.calls)==before+1,'Only the pull may retry; queued operation is not due'
    cloud.fail=False;due(reopened);assert SyncEngine(reopened,cloud).cycle()['pending']==0

def test_conversations_notes_alert_ack_archive_restore_replicate_without_echo(tmp_path):
    local=mirror(tmp_path);save(local);cloud=Cloud();engine=SyncEngine(local,cloud);engine.cycle()
    local.add_conversation('a'*32,'Explain the heatmap',{'answer':'Fixture answer'})
    local.add_review('a'*32,'Reviewed','Hold','QA note')
    local.acknowledge('a'*32);local.archive();local.restore(['a'*32])
    for _ in range(6):engine.cycle()
    assert local.status()['pending']==0
    remote=cloud.rows['a'*32]
    assert len(remote['conversation'])==2 and len(remote['notes'])==1 and remote['archived_at'] is None
    assert remote['payload']['alert_acknowledged'] is True
    other=mirror(tmp_path/'second');SyncEngine(other,cloud).cycle()
    assert other.messages('a'*32)[1]['answer']=='Fixture answer'
    assert other.review_history('a'*32)[0]['decision']=='Hold'
    assert other.alerts()[0]['acknowledged']==1
    remote['archived_at']='2026-10-22T02:00:00Z';remote['sync_version']+=1
    SyncEngine(other,cloud).cycle();assert other.get('a'*32) is None and len(other.list(archived=True))==1
    assert other.status()['pending']==0,'Remote archive never becomes a local restore operation'

def test_conflict_retains_local_changes_until_explicit_resolution_with_backup(tmp_path):
    local=mirror(tmp_path);save(local);cloud=Cloud();engine=SyncEngine(local,cloud);engine.cycle()
    local.add_conversation('a'*32,'Keep this local question',{'answer':'Local draft'})
    cloud.rows['a'*32]['sync_version']+=1
    result=engine.cycle();assert result['state']=='conflict'
    assert local.messages('a'*32)[0]['question']=='Keep this local question'
    engine.resolve('a'*32,'cloud')
    assert local.messages('a'*32)==[] and local.status()['conflicts']==[]
    with local.connect() as db:
        backup=json.loads(db.execute('SELECT snapshot FROM sync_conflict_backups').fetchone()[0])
        assert 'Local draft' in json.dumps(backup)

def test_explicit_local_retry_can_rebase_but_cannot_replace_an_immutable_id_collision(tmp_path):
    local=mirror(tmp_path);save(local);cloud=Cloud();engine=SyncEngine(local,cloud);engine.cycle()
    local.add_conversation('a'*32,'Question after cloud edit',{'answer':'Kept'})
    cloud.rows['a'*32]['sync_version']+=1;engine.cycle();engine.resolve('a'*32,'retry_local');engine.cycle()
    assert cloud.rows['a'*32]['conversation'][1]['answer']=='Kept'
    fresh=mirror(tmp_path/'collision');save(fresh);collision=SyncEngine(fresh,cloud);collision.cycle()
    with pytest.raises(ValueError,match='cannot be rebased'):collision.resolve('a'*32,'retry_local')
    assert fresh.status()['conflicts']

def test_cloud_artifact_corruption_or_wrong_owner_never_enters_local_database(tmp_path):
    first=mirror(tmp_path/'a');save(first);cloud=Cloud();SyncEngine(first,cloud).cycle()
    cloud.objects[cloud.rows['a'*32]['image_path']]=b'corrupted'
    other=mirror(tmp_path/'b');assert SyncEngine(other,cloud).cycle()['state']=='unavailable'
    assert other.get('a'*32) is None
    cloud.rows['a'*32]['owner_id']=OTHER
    assert SyncEngine(other,cloud).cycle()['state']=='unavailable' and other.get('a'*32) is None

def test_pagination_is_resumable_and_covers_more_than_one_page(tmp_path):
    first=mirror(tmp_path/'a');cloud=Cloud();engine=SyncEngine(first,cloud)
    for i in range(7):save(first,f'{i:032x}')
    for _ in range(3):engine.cycle(maximum=3)
    other=mirror(tmp_path/'b');pull=SyncEngine(other,cloud)
    assert pull.cycle(maximum=3)['scan_in_progress'];assert len(other.list())==3
    pull.cycle(maximum=3);assert len(other.list())==6
    assert not pull.cycle(maximum=3)['scan_in_progress'];assert len(other.list())==7

def test_failing_earlier_record_does_not_starve_other_pending_inspections(tmp_path):
    local=mirror(tmp_path);save(local);save(local,'b'*32);cloud=Cloud();cloud.fail=True
    SyncEngine(local,cloud).cycle(maximum=1);cloud.fail=False
    SyncEngine(local,cloud).cycle(maximum=1)
    assert 'b'*32 in cloud.rows and 'a'*32 not in cloud.rows

def test_live_auth_boundary_never_trusts_owner_from_browser_or_reuses_other_accounts(monkeypatch,tmp_path):
    def authorize(self,config,token,artifacts):
        if token in ('pending','aal1','revoked'):raise ValueError('Denied')
        if token=='outage':raise RuntimeError('Account server unavailable')
        self.user={'id':OWNER if token=='owner' else OTHER};self.staff={'role':'staff','display_name':'QA'}
    monkeypatch.setattr('deployment.space.personal_repository.PersonalRepository.__init__',authorize)
    repo=LocalSyncRepository(tmp_path,{'url':'https://fixture.invalid','key':'public','auth_workflow_enabled':True},tmp_path/'legacy-artifacts')
    repo.artifacts.mkdir()
    with identity('a'*64,'owner'),repo.bind():
        save(repo.current());assert len(repo.list())==1
    with identity('a'*64,'other'),repo.bind():assert repo.get('a'*32) is None
    with identity('a'*64),repo.bind():assert repo.get('a'*32) is None,'No fallback from personal account to unassigned legacy history'
    for token in ('pending','aal1','revoked','outage'):
        with identity('a'*64,token),pytest.raises((ValueError,RuntimeError)):
            with repo.bind():pytest.fail('Unauthorized repository exposed')

def test_loopback_adapter_preserves_default_and_denies_untrusted_origins(monkeypatch,tmp_path):
    monkeypatch.delenv('DEFECTRAG_LOCAL_SYNC',raising=False)
    repo=LocalSyncRepository(tmp_path,{'url':'https://fixture.invalid','key':'public'},tmp_path/'artifacts')
    with TestClient(create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=repo)) as client:
        assert client.get('/api/health').json()['data']['local_sync_enabled'] is True
        headers={'X-DefectRAG-Session':'a'*64,'Origin':'https://untrusted.invalid'}
        assert client.post('/api/local-sync/run',headers=headers).status_code==403
        assert client.post('/api/local-sync/run',headers={'X-DefectRAG-Session':'a'*64}).status_code==403
        assert client.get('/api/stats').status_code==401
        assert client.get('/api/batch-name?name=QA').status_code==401
        assert client.get('/api/batch-name?name=QA',headers={'X-DefectRAG-Session':'a'*64,'X-DefectRAG-Workspace':'team'}).status_code==403
        assert client.get('/api/batch-name?name=QA',headers={'X-DefectRAG-Session':'a'*64}).json()['data']=={'available':True}
        response=client.get('/api/stats',headers={'X-DefectRAG-Session':'a'*64})
        assert response.status_code==200 and response.headers['Cache-Control']=='private, no-store'

def test_legacy_history_requires_explicit_import_and_preserves_unverified_review_provenance(monkeypatch,tmp_path):
    def authorize(self,config,token,artifacts):self.user={'id':OWNER};self.staff={'role':'staff','display_name':'Owner'}
    monkeypatch.setattr('deployment.space.personal_repository.PersonalRepository.__init__',authorize)
    repo=LocalSyncRepository(tmp_path,{'url':'https://fixture.invalid'},tmp_path/'artifacts');repo.artifacts.mkdir()
    for suffix in ('','_heatmap'):(repo.artifacts/('a'*32+suffix+'.jpg')).write_bytes(b'legacy-fixture')
    repo.legacy.save(record());repo.legacy.add_conversation('a'*32,'Old local question',{'answer':'Old answer'})
    repo.legacy.add_review('a'*32,'Reviewed','Hold','Original operator unknown')
    with identity('a'*64,'owner'),repo.bind():
        assert repo.get('a'*32) is None
        assert repo.import_legacy(['a'*32])['imported']==1
        assert repo.import_legacy(['a'*32])['imported']==0
        assert repo.get('a'*32)['import_provenance'].startswith('Explicit import')
        assert repo.messages('a'*32)[1]['answer']=='Old answer'
        assert repo.review_history('a'*32)==[],'Do not turn an unverified imported review into an authenticated decision'
        assert 'original identity unverified' in repo.review_notes('a'*32)[0]['body']
        assert repo.current().status()['pending']==3
    assert repo.legacy.get('a'*32) is not None

def test_local_authenticated_api_inference_routes_artifacts_to_owner_folder(monkeypatch,tmp_path):
    def authorize(self,config,token,artifacts):
        if token!='approved':raise ValueError('MFA denied')
        self.user={'id':OWNER};self.staff={'role':'staff','display_name':'Owner'}
    monkeypatch.setattr('deployment.space.personal_repository.PersonalRepository.__init__',authorize)
    repo=LocalSyncRepository(tmp_path,{'url':'https://fixture.invalid'},tmp_path/'artifacts')
    headers={'X-DefectRAG-Session':'b'*64,'Authorization':'Bearer approved'}
    with TestClient(create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=repo)) as client:
        result=client.post('/api/inspect',headers=headers,data={'category':'pcb1'},files={'file':('fixture.png',image_bytes(),'image/png')})
        assert result.status_code==200
        row=result.json()['data'];assert row['owner_id']==OWNER and 'access=' in row['image_url']
        assert client.get(row['image_url']).status_code==200
        assert (tmp_path/'local-sync/accounts'/OWNER/'artifacts'/(row['id']+'.jpg')).exists()
        assert client.get('/api/inspections',headers={'X-DefectRAG-Session':'c'*64}).json()['data']==[]
        denied={**headers,'Authorization':'Bearer aal1'}
        assert client.get('/api/inspections',headers=denied).status_code==403

def test_migration_is_additive_owner_mfa_checked_and_has_revision_idempotency():
    sql=Path('deployment/supabase_personal_sync.sql').read_text()
    assert 'defectrag_is_staff()' in sql and 'auth.uid()' in sql and 'security definer set search_path' in sql
    assert 'r.owner_id<>auth.uid()' in sql and 'r.sync_version<>p_base' in sql
    assert 'request_hash<>fingerprint' in sql and 'pg_advisory_xact_lock' in sql
    assert 'alter table public.personal_inspections add column' in sql
    assert not any(value in sql.lower() for value in ('delete from','drop table','disable row level','shared_inspections','notification_automation'))

def test_existing_cloud_factory_does_not_resolve_an_account_during_startup(monkeypatch,tmp_path):
    from deployment.space.sessions import SessionRepository
    monkeypatch.delenv('DEFECTRAG_LOCAL_SYNC',raising=False)
    cloud=SessionRepository(tmp_path/'sessions',cloud_config={'url':'https://fixture.invalid'},artifacts=tmp_path/'artifacts',personal_enabled=True)
    app=create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=cloud)
    with TestClient(app) as client:assert client.get('/api/health').json()['data']['local_sync_enabled'] is False

def test_personal_note_history_download_is_paginated_not_silently_truncated(tmp_path):
    first=mirror(tmp_path/'a');save(first);cloud=Cloud();SyncEngine(first,cloud).cycle()
    cloud.rows['a'*32]['notes']=[{'id':str(uuid.uuid4()),'inspection_id':'a'*32,'author_id':OWNER,'body':'Fixture note '+str(i),'created_at':'2026-10-22T00:00:00Z'} for i in range(201)]
    other=mirror(tmp_path/'b');SyncEngine(other,cloud).cycle()
    assert len(other.review_notes('a'*32))==201
    assert any(call[2].get('params',{}).get('offset')=='200' for call in cloud.calls)

def test_opt_in_local_mirror_preserves_enabled_local_community_gallery(monkeypatch,tmp_path):
    monkeypatch.setenv('DEFECTRAG_GALLERY_ENABLED','1')
    repo=LocalSyncRepository(tmp_path,{'url':'https://fixture.invalid'},tmp_path/'artifacts')
    with TestClient(create_app(Settings(data=tmp_path),SoftwareDetector(),SoftwareWorkflow(),repository=repo)) as client:
        assert client.get('/api/gallery').json()['data']=={'enabled':True,'items':[]}
