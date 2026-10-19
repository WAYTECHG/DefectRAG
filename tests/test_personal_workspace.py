"""Repository and scope software tests; not evidence that live RLS passed."""
import base64
import json
import httpx
from pathlib import Path
import pytest
from deployment.space.sessions import identity,SessionRepository,WORKSPACE,capability,authorize_artifact,artifact_workspace
from deployment.space.supabase_repository import StaffRepository
from deployment.space.personal_repository import PersonalRepository


def record():
    return {'id':'1'*32,'created_at':'2026-10-19T00:00:00Z','category':'pcb1','batch':'SOFTWARE',
            'verdict':'Anomalous','score':.2,'threshold':.1,'request_fingerprint':'fixture-content-hash'}


def repository(tmp_path):
    repo=PersonalRepository.__new__(PersonalRepository)
    repo.config={'url':'https://example.invalid','key':'public-fixture'}
    repo.user={'id':'owner-A'};repo.staff={'role':'staff','display_name':'Owner A'};repo.artifacts=tmp_path
    for suffix in ('','_heatmap'):(tmp_path/('1'*32+suffix+'.jpg')).write_bytes(b'fixture-'+suffix.encode())
    calls=[];rows={}
    def request(method,path,**kwargs):
        calls.append((method,path,kwargs))
        if path=='/rest/v1/personal_inspections':
            if method=='GET':
                assert kwargs['params']['owner_id']=='eq.owner-A'
                return [rows['1'*32]] if rows else []
            rows[kwargs['json']['id']]=kwargs['json'];return None
        if '/object/sign/' in path:return {'signedURL':'/object/sign/private?token=fixture'}
        return None
    repo.request=request
    return repo,calls,rows


def test_authenticated_default_personal_and_explicit_team_are_distinct(monkeypatch,tmp_path):
    def initialize(self,*args):self.user={'id':'owner'};self.staff={'role':'staff'}
    monkeypatch.setattr(StaffRepository,'__init__',initialize)
    repo=SessionRepository(tmp_path,cloud_config={'url':'https://example.invalid','key':'public'},artifacts=tmp_path,personal_enabled=True)
    with identity('a'*64,'valid-fixture-token'):
        assert isinstance(repo.current(),PersonalRepository)
    with identity('a'*64,'valid-fixture-token','team'):
        current=repo.current();assert type(current) is StaffRepository and current.workspace_stats_enabled
    with identity('a'*64,workspace='team'):
        with pytest.raises(ValueError,match='Sign in'):repo.current()


def test_capability_cannot_be_reinterpreted_in_another_scope():
    with identity('a'*64,workspace='personal'):
        token=capability('1'*32,'report')
        assert artifact_workspace(token)=='personal'
        raw=base64.urlsafe_b64decode(token+'='*(-len(token)%4)).decode().replace(':personal:',':team:')
        tampered=base64.urlsafe_b64encode(raw.encode()).decode().rstrip('=')
        with pytest.raises(ValueError):authorize_artifact(tampered,'1'*32,'report')
    assert WORKSPACE.get()=='personal'


def test_personal_save_is_verified_private_and_replay_does_not_reupload(tmp_path):
    repo,calls,rows=repository(tmp_path)
    first=repo.save(record());uploads=[c for c in calls if '/object/personal-inspections/' in c[1]]
    assert len(uploads)==2 and all(c[2]['ignore_conflict'] for c in uploads)
    assert first['storage']=='supabase_personal' and first['owner_id']=='owner-A'
    before=len(calls);second=repo.save(record())
    assert second['id']==first['id']
    assert not any('/object/personal-inspections/' in c[1] for c in calls[before:])
    assert len(rows)==1
    with pytest.raises(ValueError,match='different data'):repo.save({**record(),'request_fingerprint':'changed'})


def test_personal_storage_failure_never_inserts_or_reports_success(tmp_path):
    repo,calls,rows=repository(tmp_path);original=repo.request
    def failing(method,path,**kwargs):
        if '/storage/v1/object/personal-inspections/' in path:raise RuntimeError('Storage quota reached')
        return original(method,path,**kwargs)
    repo.request=failing
    with pytest.raises(RuntimeError,match='quota'):repo.save(record())
    assert not rows


def test_archived_or_conflicting_record_never_silently_overwritten(tmp_path):
    repo,_,rows=repository(tmp_path);repo.save(record());rows['1'*32]['archived_at']='2026-10-19T01:00:00Z'
    with pytest.raises(ValueError,match='archived'):repo.save(record())


def test_personal_conversations_and_ack_use_owner_action_rpc(tmp_path):
    repo,calls,_=repository(tmp_path)
    repo.add_conversation('1'*32,'Explain this result',{'answer':'software fixture'})
    repo.acknowledge('1'*32)
    assert all(c[1]=='/rest/v1/rpc/defectrag_personal_action' for c in calls)
    assert calls[0][2]['json']['p_action']=='conversation' and calls[1][2]['json']['p_action']=='acknowledge'


def test_personal_archive_restore_and_aggregate_stats_stay_in_scope(tmp_path):
    repo,calls,_=repository(tmp_path);repo.raw_list=lambda *a,**k:[{'id':'1'*32}]
    repo.archive();repo.restore(['1'*32]);repo.stats()
    assert calls[0][2]['json']=={'p_ids':['1'*32],'p_restore':False}
    assert calls[1][2]['json']['p_restore'] is True
    assert calls[2][2]['json']=={'p_scope':'personal'}


def test_expired_account_never_falls_back_to_guest(monkeypatch,tmp_path):
    def expired(*args):raise ValueError('Staff session expired')
    monkeypatch.setattr(StaffRepository,'__init__',expired)
    repo=SessionRepository(tmp_path,cloud_config={'url':'https://example.invalid'},artifacts=tmp_path,personal_enabled=True)
    with identity('a'*64,'expired-token'):
        with pytest.raises(ValueError,match='expired'):repo.current()


def test_owner_privacy_migration_has_no_developer_bypass_or_gallery_changes():
    sql=Path('deployment/supabase_personal_workspace.sql').read_text(encoding='utf-8')
    assert 'owner_id=auth.uid()' in sql and 'personal-inspections' in sql
    assert 'grant select,insert on public.personal_inspections' in sql
    assert 'grant update' not in sql.lower() and 'drop ' not in sql.lower()
    assert 'defectrag_gallery_' not in sql
    assert 'for update;' in sql and 'defectrag_is_developer()' not in sql
    assert "set search_path=''" in sql


@pytest.mark.parametrize('status,code,ignored',[(400,'Duplicate',True),(409,'23505',True),(400,'InvalidRequest',False),(403,'AccessDenied',False)])
def test_only_real_duplicate_conflicts_are_safe_to_replay(monkeypatch,status,code,ignored):
    class Reply:
        is_success=False
        status_code=status
        def json(self):return {'code':code}
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def request(self,*args,**kwargs):return Reply()
    monkeypatch.setattr('deployment.space.supabase_repository.httpx.Client',Client)
    repo=StaffRepository.__new__(StaffRepository);repo.headers={};repo.config={'url':'https://invalid.example'}
    if ignored:assert repo.request('POST','/storage/v1/object/test',ignore_conflict=True) is None
    else:
        with pytest.raises((RuntimeError,ValueError)):repo.request('POST','/storage/v1/object/test',ignore_conflict=True)


def test_guest_save_is_explicit_and_preserves_review_provenance(monkeypatch,tmp_path):
    saved={};notes=[];shares=[]
    class Personal:
        def __init__(self,*args):self.user={'id':'approved-owner'}
        def raw(self,identifier):return saved.get(identifier)
        def save(self,value,conversation=None):saved[value['id']]=value
        def request(self,*args,**kwargs):notes.append(kwargs['json'])
        def share(self,identifier,include):shares.append((identifier,include));return {'alreadyShared':False}
    monkeypatch.setattr('deployment.space.personal_repository.PersonalRepository',Personal)
    repo=SessionRepository(tmp_path,cloud_config={'url':'https://invalid.example'},artifacts=tmp_path,personal_enabled=True)
    with identity('a'*64):
        repo.save(record());repo.add_review('1'*32,'Reviewed','Hold','Guest review')
        assert not saved and not shares
    with identity('a'*64,'fixture-approved-token'):
        assert repo.share('1'*32,personal_only=True)=={'saved':True}
        assert not shares and notes[0]['author_id']=='approved-owner'
        assert 'original identity unverified' in notes[0]['body'] and 'Hold' in notes[0]['body']
        repo.share('1'*32,personal_only=True);assert notes[0]['id']==notes[1]['id']
        repo.share('1'*32);assert shares==[('1'*32,False)]
        assert repo.local().review_history('1'*32)[0]['decision']=='Hold'


def test_cloud_archive_cannot_resurface_through_old_guest_copy(tmp_path):
    repo=SessionRepository(tmp_path,cloud_config={'url':'https://invalid.example'},artifacts=tmp_path,personal_enabled=True)
    class ArchivedPersonal:
        def raw(self,identifier):return None
        def _raw_any(self,identifier):return {'id':identifier,'archived_at':'2026-10-19'}
        def get(self,identifier):return None
    with identity('a'*64):repo.save(record())
    with identity('a'*64,'valid-test-token'):
        repo.current=lambda:ArchivedPersonal()
        assert repo.get('1'*32) is None


def test_guest_conversation_import_limit_preserves_content_and_precedes_uploads(tmp_path):
    repo,calls,rows=repository(tmp_path)
    messages=[{'question':'a'*39982}]
    assert len(json.dumps(messages).encode())==40000
    repo.save(record(),messages)
    assert rows['1'*32]['conversation']==messages
    calls.clear()
    with pytest.raises(ValueError,match='too large'):
        repo.save(record(),[{'question':'a'*39983}])
    assert calls==[]


@pytest.mark.parametrize('failure',['denied','empty','oversize','network','interrupted'])
def test_private_image_copy_failure_never_uploads_or_calls_share_rpc(monkeypatch,tmp_path,failure):
    repo,calls,_=repository(tmp_path);repo.headers={'Authorization':'Bearer software-fixture'}
    repo.raw=lambda identifier:{'image_path':'owner-A/source.jpg'}
    class Reply:
        is_success=failure!='denied'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_bytes(self,**kwargs):
            if failure=='interrupted':
                yield b'partial'
                raise httpx.ReadError('sensitive upstream URL must not be returned')
            if failure=='oversize':yield b'a'*(10*1024*1024+1)
    class Client:
        def __init__(self,**kwargs):assert kwargs['trust_env'] is False
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,*args,**kwargs):
            if failure=='network':raise httpx.ConnectError('sensitive upstream URL must not be returned')
            return Reply()
    monkeypatch.setattr('deployment.space.personal_repository.httpx.Client',Client)
    with pytest.raises(RuntimeError) as error:repo.share('1'*32)
    assert 'sensitive' not in str(error.value)
    assert all(method=='GET' for method,_,_ in calls)


def test_explicit_team_copy_sends_only_authorized_bytes_and_conversation_choice(monkeypatch,tmp_path):
    repo,calls,_=repository(tmp_path);repo.headers={'Authorization':'Bearer software-fixture'}
    repo.raw=lambda identifier:{'image_path':'owner-A/image.jpg','heatmap_path':'owner-A/heatmap.jpg'}
    reads=[]
    class Reply:
        is_success=True
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_bytes(self,**kwargs):yield b'image';yield b'-bytes'
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,method,url,**kwargs):
            assert kwargs['headers']==repo.headers
            reads.append(url);return Reply()
    monkeypatch.setattr('deployment.space.personal_repository.httpx.Client',Client)
    repo.share('1'*32,include_conversation=True)
    assert len(reads)==2 and all('/authenticated/personal-inspections/owner-A/' in url for url in reads)
    uploads=[c for c in calls if '/object/team-inspections/' in c[1]]
    assert len(uploads)==2 and all(c[2]['content']==b'image-bytes' and c[2]['ignore_conflict'] for c in uploads)
    assert calls[-1][1]=='/rest/v1/rpc/defectrag_share_personal'
    assert calls[-1][2]['json']['p_include_conversation'] is True


def test_already_shared_record_never_downloads_or_changes_team_copy(tmp_path):
    repo,_,_=repository(tmp_path);repo.raw=lambda identifier:{'id':identifier}
    calls=[]
    def request(method,path,**kwargs):
        calls.append((method,path));return [{'id':'1'*32,'owner_id':'owner-A'}]
    repo.request=request
    repo._read_private_image=lambda path:pytest.fail('A repeated share must not download images')
    assert repo.share('1'*32)=={'alreadyShared':True}
    assert calls==[('GET','/rest/v1/shared_inspections')]
