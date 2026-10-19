"""Isolate anonymous browser history; grant short-lived artifact capabilities."""
import base64
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import hmac
import os
from pathlib import Path
import re
import time
import threading
from backend.storage import SQLiteRepository

NAMESPACE = ContextVar('defectrag_namespace', default=None)
STAFF_TOKEN = ContextVar('defectrag_staff_token', default='')
WORKSPACE = ContextVar('defectrag_workspace', default='personal')
SIGNING_KEY = os.environ.get('DEFECTRAG_SIGNING_KEY', '').encode() or os.urandom(32)
_staff_sessions={}
_session_lock=threading.Lock()


def remember_staff(owner,token):
    with _session_lock:
        if token:
            if len(_staff_sessions)>=512:
                expired=[key for key,value in _staff_sessions.items() if value[0]<time.time()]
                for key in expired:
                    del _staff_sessions[key]
                if len(_staff_sessions)>=512:
                    raise ValueError('Workspace capacity reached; retry later.')
            _staff_sessions[owner]=(time.time()+3600,token)
        else:
            _staff_sessions.pop(owner,None)


def stored_staff(owner):
    with _session_lock:
        entry=_staff_sessions.get(owner)
    return entry[1] if entry and entry[0]>time.time() else ''


def namespace(session):
    if not isinstance(session, str) or not re.fullmatch('[a-f0-9]{64}', session):
        raise ValueError('A private browser workspace is required. Reload the dashboard.')
    return hashlib.sha256(session.encode()).hexdigest()


@contextmanager
def identity(session, token='', workspace='personal'):
    if workspace not in ('personal','team'):raise ValueError('Invalid workspace')
    owner=namespace(session)
    remember_staff(owner,token)
    marker = NAMESPACE.set(owner)
    staff = STAFF_TOKEN.set(token)
    scope = WORKSPACE.set(workspace)
    try:
        yield
    finally:
        WORKSPACE.reset(scope)
        STAFF_TOKEN.reset(staff)
        NAMESPACE.reset(marker)


def capability(identifier, kind):
    text = f'{NAMESPACE.get()}:{WORKSPACE.get()}:{identifier}:{kind}:{int(time.time())+3600}'
    signature = hmac.new(SIGNING_KEY, text.encode(), 'sha256').hexdigest()
    return base64.urlsafe_b64encode(f'{text}:{signature}'.encode()).decode().rstrip('=')


def authorize_artifact(access, identifier, kind):
    try:
        raw = base64.urlsafe_b64decode(access+'='*(-len(access)%4)).decode()
        owner, scope, actual_id, actual_kind, expires, signature = raw.split(':')
        text = ':'.join((owner, scope, actual_id, actual_kind, expires))
        if (not re.fullmatch('[a-f0-9]{64}', owner) or actual_id != identifier or actual_kind != kind
                or scope not in ('personal','team')
                or int(expires) < time.time() or not hmac.compare_digest(signature,
                    hmac.new(SIGNING_KEY, text.encode(), 'sha256').hexdigest())):
            raise ValueError()
        return owner
    except (ValueError, TypeError, UnicodeError):
        raise ValueError('Image or report access expired. Reopen the saved inspection.') from None


def artifact_workspace(access):
    # Call only AFTER authorize_artifact validates the signed scope.
    return base64.urlsafe_b64decode(access+'='*(-len(access)%4)).decode().split(':')[1]


class SessionRepository:
    def __init__(self, directory, cloud_config=None, artifacts=None, personal_enabled=False):
        self.directory = Path(directory)
        self.cloud_config=cloud_config
        self.artifacts=artifacts
        self.personal_enabled=personal_enabled

    def current(self):
        owner = NAMESPACE.get()
        if not owner:
            raise ValueError('Workspace authorization is missing')
        if self.cloud_config and STAFF_TOKEN.get():
            from deployment.space.supabase_repository import StaffRepository
            if self.personal_enabled and WORKSPACE.get()=='personal':
                from deployment.space.personal_repository import PersonalRepository
                return PersonalRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)
            current=StaffRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)
            current.workspace_stats_enabled=self.personal_enabled
            return current
        if self.personal_enabled and WORKSPACE.get()=='team':
            raise ValueError('Sign in with an approved staff account for Team workspace.')
        return SQLiteRepository(self.directory / owner / 'inspection.sqlite3')

    def local(self):
        return SQLiteRepository(self.directory / NAMESPACE.get() / 'inspection.sqlite3')

    def decorate(self, record):
        if record is None:
            return None
        result = dict(record)
        result.setdefault('storage','browser_session')
        for kind in ('image', 'heatmap', 'report'):
            if kind!='report' and result.get('storage','').startswith('supabase') and result.get(kind+'_url','').startswith('https://'):
                continue
            result[kind+'_url'] = f"/api/inspections/{record['id']}/{kind}?access={capability(record['id'], kind)}"
        return result

    def save(self, record):
        return self.decorate(self.current().save(record))

    def guest_fallback(self,current,identifier):
        if not self.cloud_config or not STAFF_TOKEN.get():return False
        if self.personal_enabled and WORKSPACE.get()!='personal':return False
        if current.raw(identifier) is not None:return False
        # An archived cloud record must not reappear through its old guest copy.
        if self.personal_enabled and hasattr(current,'_raw_any') and current._raw_any(identifier) is not None:return False
        return True

    def get(self, identifier):
        current=self.current()
        record=current.get(identifier)
        # Signing in must not invalidate this browser's earlier anonymous upload
        # before its explicit Share with staff operation has copied it durably.
        if record is None and self.guest_fallback(current,identifier):
            record=self.local().get(identifier)
        return self.decorate(record)

    def messages(self,identifier):
        current=self.current()
        if self.guest_fallback(current,identifier):
            return self.local().messages(identifier)
        return current.messages(identifier)

    def add_conversation(self,identifier,question,answer):
        current=self.current()
        if self.guest_fallback(current,identifier):
            return self.local().add_conversation(identifier,question,answer)
        return current.add_conversation(identifier,question,answer)

    def list(self, *args, **kwargs):
        return [self.decorate(row) for row in self.current().list(*args, **kwargs)]

    def review_repository(self,identifier):
        current=self.current()
        if self.guest_fallback(current,identifier):
            return self.local()
        return current

    def add_review(self,identifier,*args,**kwargs):
        return self.review_repository(identifier).add_review(identifier,*args,**kwargs)

    def review_history(self,identifier):
        return self.review_repository(identifier).review_history(identifier)

    def review_notes(self,identifier):
        return self.review_repository(identifier).review_notes(identifier)

    def status(self):
        current=self.current()
        staff=getattr(current,'staff',None)
        return {'personal_enabled':self.personal_enabled,'workspace':WORKSPACE.get() if self.personal_enabled else 'team' if staff else 'guest',
                'authenticated':bool(staff),'role':staff.get('role') if staff else None,
                'storage':'supabase' if staff else 'temporary_browser','poll_seconds':15}

    def share(self,identifier,include_conversation=False,personal_only=False):
        if not self.personal_enabled or not self.cloud_config or not STAFF_TOKEN.get():
            raise ValueError('Sign in to the configured Personal workspace before saving or sharing.')
        from deployment.space.personal_repository import PersonalRepository
        personal=PersonalRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)
        if personal.raw(identifier) is None:
            guest=self.local().get(identifier)
            if guest is None:
                raise ValueError('An owned personal inspection or this browser’s guest inspection is required.')
            personal.save(guest,conversation=self.local().messages(identifier))
        # Retain guest review provenance as imported notes, never pretend a guest
        # decision was a newly authenticated human decision. Stable IDs make a
        # retry after a partial import append-safe. These notes are NOT team-shared.
        if self.local().get(identifier):
            import json
            import uuid
            for review in self.local().review_history(identifier):
                note_id=str(uuid.uuid5(uuid.NAMESPACE_URL,personal.user['id']+':'+identifier+':'+review['created_at']))
                body='Imported guest review (original identity unverified): '+json.dumps(review,ensure_ascii=False)
                personal.request('POST','/rest/v1/personal_notes',json={'id':note_id,'inspection_id':identifier,
                    'author_id':personal.user['id'],'body':body[:2000]},ignore_conflict=True)
        if personal_only:return {'saved':True}
        return personal.share(identifier,include_conversation)

    def __getattr__(self, name):
        return getattr(self.current(), name)
