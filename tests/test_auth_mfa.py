"""Offline boundary tests. No live Auth, email, SQL execution or model calls."""
import ast
import re
from pathlib import Path
import pytest
from deployment.space.supabase_repository import StaffRepository, _staff_cache
from deployment.space.sessions import SessionRepository, identity

CONFIG={'url':'https://fixture.invalid','key':'sb_publishable_fixture','auth_workflow_enabled':True}

def posture(**overrides):
    return dict(user_id='fixture-owner',role='staff',display_name='Staff fixture',approved=True,
                revoked=False,authorized=True,mfa_required=True,aal2=True,**overrides)


def test_new_backend_flag_off_keeps_legacy_login_without_new_rpc(monkeypatch,tmp_path):
    calls=[]
    def request(self,method,path,**kwargs):
        calls.append(path)
        if path=='/auth/v1/user':return {'id':'legacy-staff-fixture'}
        if path=='/rest/v1/staff_members':return [{'role':'staff','display_name':'Fixture'}]
        raise AssertionError('Inactive features must not contact new RPCs')
    monkeypatch.setattr(StaffRepository,'request',request)
    repo=StaffRepository({**CONFIG,'auth_workflow_enabled':False},'legacy-test-unique',tmp_path)
    assert repo.user['id']=='legacy-staff-fixture'
    assert calls==['/auth/v1/user','/rest/v1/staff_members']


@pytest.mark.parametrize('update',[
    {'approved':False}, {'revoked':True}, {'aal2':False}, {'authorized':False},
    {'role':'pending'}, {'role':None}, {'user_id':None}, {'mfa_required':None}, {'mfa_required':1},
])
def test_protected_accounts_fail_closed_for_bad_posture(monkeypatch,tmp_path,update):
    monkeypatch.setattr(StaffRepository,'request',lambda *a,**k:{**posture(),**update})
    with pytest.raises(ValueError,match='authenticator'):
        StaffRepository(CONFIG,'opaque-fixture',tmp_path)


def test_active_verified_account_passes_and_revocation_ignores_legacy_cache(monkeypatch,tmp_path):
    state=posture();calls=[]
    def request(self,method,path,**kwargs):
        assert method=='POST' and path=='/rest/v1/rpc/defectrag_auth_status' and kwargs['json']=={}
        calls.append(path);return state.copy()
    monkeypatch.setattr(StaffRepository,'request',request)
    token='revocation-software-fixture'
    _staff_cache[token]=(10**15,{'id':'stale-user'},{'role':'developer'})
    try:
        current=StaffRepository(CONFIG,token,tmp_path)
        assert current.user['id']=='fixture-owner' and current.staff['role']=='staff'
        state.update(approved=False,authorized=False,revoked=True)
        with pytest.raises(ValueError):StaffRepository(CONFIG,token,tmp_path)
        assert len(calls)==2
    finally:_staff_cache.pop(token,None)


def test_native_auth_outage_never_falls_through_to_guest(monkeypatch,tmp_path):
    def fail(*args,**kwargs):raise RuntimeError('Supabase unavailable')
    monkeypatch.setattr(StaffRepository,'request',fail)
    repo=SessionRepository(tmp_path,CONFIG,tmp_path,personal_enabled=True)
    with identity('a'*64,'expired-or-unavailable-fixture'):
        with pytest.raises(RuntimeError,match='unavailable'):repo.current()
    with identity('a'*64):
        assert repo.list()==[]  # explicit anonymous demo still works


def test_bootstrap_before_activation_accepts_approved_aal1_only_when_db_allows(monkeypatch,tmp_path):
    monkeypatch.setattr(StaffRepository,'request',lambda *a,**k:{**posture(),'aal2':False,'mfa_required':False})
    assert StaffRepository(CONFIG,'bootstrap-fixture',tmp_path).staff['role']=='staff'


def test_private_images_generate_scoped_urls_not_signed_storage_links(tmp_path):
    current=StaffRepository.__new__(StaffRepository);current.config=CONFIG
    current.request=lambda *a,**k:pytest.fail('No signed URL request permitted')
    row={'payload':{'id':'1'*32},'owner_id':'fixture-owner','image_path':'private/image','heatmap_path':'private/map'}
    result=current.decorate(row)
    assert result['image_url']=='/api/inspections/'+'1'*32+'/image'
    assert result['heatmap_url'].endswith('/heatmap') and 'token=' not in str(result)


@pytest.mark.parametrize('status,length',[(403,7),(200,0),(200,10*1024*1024+1)],ids=['denied','empty','oversized'])
def test_private_artifact_denied_empty_and_oversized_response_rejected(monkeypatch,tmp_path,status,length):
    content=b'x'*length
    class Response:
        is_success=status==200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_bytes(self,**kwargs):yield content
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,*args,**kwargs):return Response()
    monkeypatch.setattr('deployment.space.supabase_repository.httpx.Client',Client)
    current=StaffRepository.__new__(StaffRepository);current.config=CONFIG;current.headers={}
    current.raw=lambda identifier:{'image_path':'fixture-owner/id/image.jpg'}
    with pytest.raises(ValueError):current.private_artifact('1'*32,'image')


def test_private_artifact_read_is_authenticated_under_correct_bucket(monkeypatch,tmp_path):
    calls=[]
    class Response:
        is_success=True
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_bytes(self,**kwargs):yield b'fixture-image'
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,*args,**kwargs):calls.append((args,kwargs));return Response()
    monkeypatch.setattr('deployment.space.supabase_repository.httpx.Client',Client)
    current=StaffRepository.__new__(StaffRepository);current.config=CONFIG;current.headers={'Authorization':'Bearer user-fixture'}
    current.raw=lambda identifier:{'image_path':'fixture-owner/id/image.jpg'}
    assert current.private_artifact('1'*32,'image')==b'fixture-image'
    assert '/object/authenticated/team-inspections/' in calls[0][0][1]
    assert calls[0][1]['headers']==current.headers


def sql_function(sql,name):
    match=re.search(r'create (?:or replace )?function public\.'+name+r'\([^$]+?\$\$(.*?)\$\$;',sql,re.S|re.I)
    assert match,name
    return match.group(1)


def test_migration_inactive_and_privilege_matrix_is_explicit():
    sql=Path('deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
    assert 'mfa_required boolean not null default false' in sql
    assert 'registration_enabled boolean not null default false' in sql
    assert not re.search(r'\b(delete|drop|truncate)\s',sql,re.I)
    assert "auth.jwt()->>'aal'='aal2'" in sql and "f.factor_type='totp' and f.status='verified'" in sql
    for name in ['defectrag_access_directory','defectrag_decide_access','defectrag_notification_status','defectrag_retry_notification']:
        assert 'if not public.defectrag_can_manage_access()' in sql_function(sql,name)
    for name in ['defectrag_claim_notifications','defectrag_finish_notification']:
        assert "auth.role() is distinct from 'service_role'" in sql_function(sql,name)
    configure=sql_function(sql,'defectrag_configure_auth')
    assert 'Enroll and verify an active developer TOTP factor before enforcement' in configure
    assert 'defectrag_configure_auth(boolean,boolean)' not in sql.split('grant execute on function')[-1]
    for grant in re.findall(r'grant execute on function (.*?);',sql,re.S):
        assert 'defectrag_configure_auth' not in grant
        if 'defectrag_claim_notifications' in grant:assert grant.rstrip().endswith('to service_role')
    assert 'create policy private_artifact_auth_guard on storage.objects as restrictive' in sql
    assert "bucket_id not in ('team-inspections','personal-inspections')" in sql
    assert 'defectrag_gallery_' not in sql


def test_sql_decisions_have_no_client_role_or_direct_browser_writes():
    sql=Path('deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
    decide=sql_function(sql,'defectrag_decide_access')
    assert "p_user_id=auth.uid()" in decide and 'p_version<>coalesce(r.version,0)' in decide
    assert "pg_advisory_xact_lock(731902461)" in decide and "for update;" in decide
    assert "values(p_user_id,r.display_name,'staff')" in decide
    assert 'The last developer cannot be revoked' in decide
    assert 'insert into public.staff_access_audit' in decide and 'insert into public.staff_notification_outbox' in decide
    request=sql_function(sql,'defectrag_request_access')
    assert 'email_confirmed_at is not null' in request and 'registration_enabled' in request
    assert 'insert into public.staff_members' not in request
    assert 'r.user_id is not null then return' in request
    assert 'grant select on public.staff_access_requests,public.staff_access_audit to authenticated' in sql
    assert not re.search(r'grant\s+(insert|update|delete|all)\b',sql,re.I)


def test_sql_outbox_claim_lease_retry_and_duplicate_constraints():
    sql=Path('deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
    assert 'unique(subject_id,version,kind,recipient_id)' in sql
    claim=sql_function(sql,'defectrag_claim_notifications')
    assert 'for update skip locked' in claim and 'r.version=o.version' in claim
    assert "status='superseded'" in claim and "status='dead'" in claim
    assert 'lease_until<now()' in claim and "interval '5 minutes'" in claim
    finish=sql_function(sql,'defectrag_finish_notification')
    assert 'lease_token=p_lease and lease_until>now()' in finish
    assert "when attempts>=8 then 'dead'" in finish and 'power(2,' in finish


def test_gradio_preflight_and_artifact_guards_remain_before_model_or_storage():
    # Parse source without importing the model-initializing host module.
    source=Path('deployment/space/app.py').read_text(encoding='utf8');tree=ast.parse(source)
    inspect=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='inspect')
    body=ast.get_source_segment(source,inspect)
    assert body.index('REPO.current()')<body.index('return inspect_one(')
    assert "os.getenv('DEFECTRAG_AUTH_WORKFLOW')=='1'" in source
    artifact=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='artifact')
    assert 'REPO.current().private_artifact' in ast.get_source_segment(source,artifact)
    sessions=Path('deployment/space/sessions.py').read_text(encoding='utf8')
    assert 'return PersonalRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)' in sessions
    assert 'current=StaffRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)' in sessions


def test_existing_privileged_workspace_rpcs_already_depend_on_new_guard():
    for filename,names in {
        'deployment/supabase.sql':['archive_team_inspections','restore_team_inspections'],
        'deployment/supabase_additive_conversations.sql':['defectrag_append_conversation','defectrag_acknowledge_review'],
        'deployment/supabase_personal_workspace.sql':['defectrag_personal_action','defectrag_personal_archive','defectrag_share_personal','defectrag_workspace_stats','defectrag_acknowledge_review'],
    }.items():
        sql=Path(filename).read_text(encoding='utf8')
        for name in names:assert re.search(r'if not public\.defectrag_is_(staff|developer)\(\)',sql_function(sql,name))
