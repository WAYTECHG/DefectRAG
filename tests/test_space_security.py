"""Software security checks, separate from live Supabase/RLS acceptance tests."""
import base64
import json
import pytest
from deployment.space.sessions import identity,namespace,SessionRepository,capability,authorize_artifact
from deployment.space.supabase_repository import StaffRepository


def record():
    return {'id':'1'*32,'created_at':'2026-10-18T00:00:00+00:00','category':'pcb1',
            'verdict':'Anomalous','batch':'software-security-fixture','score':.2,'threshold':.1}


def test_foreign_workspace_cannot_read_record_or_messages(tmp_path):
    repo=SessionRepository(tmp_path)
    with identity('a'*64):
        repo.save(record())
        repo.add_conversation('1'*32,'A question',{'answer':'Software fixture only'})
        assert repo.messages('1'*32)
    with identity('b'*64):
        assert repo.get('1'*32) is None
        assert repo.list()==[] and repo.messages('1'*32)==[]


def test_artifact_capability_binds_owner_record_and_kind():
    with identity('a'*64):
        token=capability('1'*32,'image')
        assert authorize_artifact(token,'1'*32,'image')==namespace('a'*64)
        with pytest.raises(ValueError):
            authorize_artifact(token,'2'*32,'image')
        with pytest.raises(ValueError):
            authorize_artifact(token,'1'*32,'report')
        raw=base64.urlsafe_b64decode(token+'='*(-len(token)%4)).decode().replace(':image:',':heatmap:')
        tampered=base64.urlsafe_b64encode(raw.encode()).decode().rstrip('=')
        with pytest.raises(ValueError):
            authorize_artifact(tampered,'1'*32,'heatmap')


def test_old_capability_expires(monkeypatch):
    with identity('a'*64):
        token=capability('1'*32,'image')
    import deployment.space.sessions as module
    future=module.time.time()+3601
    monkeypatch.setattr(module.time,'time',lambda:future)
    with pytest.raises(ValueError):
        authorize_artifact(token,'1'*32,'image')


def test_missing_workspace_is_rejected():
    with pytest.raises(ValueError):
        namespace('short')


def test_successful_auth_without_staff_membership_is_rejected(monkeypatch,tmp_path):
    def request(self,method,path,**kwargs):
        if path=='/auth/v1/user':
            return {'id':'nonstaff-software-fixture'}
        return []
    monkeypatch.setattr(StaffRepository,'request',request)
    with pytest.raises(ValueError,match='staff allowlist'):
        StaffRepository({'url':'https://example.invalid','key':'sb_publishable_fixture'},'nonstaff-unit-test-token',tmp_path)


def test_public_config_does_not_accept_service_role_key(tmp_path):
    from deployment.space.supabase_repository import read_public_config
    config=tmp_path/'config.js'
    config.write_text('window.DEFECTRAG_PUBLIC_CONFIG='+json.dumps({'supabaseUrl':'https://example.invalid','supabasePublishableKey':'sb_secret_invalid'}))
    with pytest.raises(ValueError):
        read_public_config(config)
