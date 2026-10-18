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
def identity(session, token=''):
    owner=namespace(session)
    remember_staff(owner,token)
    marker = NAMESPACE.set(owner)
    staff = STAFF_TOKEN.set(token)
    try:
        yield
    finally:
        STAFF_TOKEN.reset(staff)
        NAMESPACE.reset(marker)


def capability(identifier, kind):
    text = f'{NAMESPACE.get()}:{identifier}:{kind}:{int(time.time())+3600}'
    signature = hmac.new(SIGNING_KEY, text.encode(), 'sha256').hexdigest()
    return base64.urlsafe_b64encode(f'{text}:{signature}'.encode()).decode().rstrip('=')


def authorize_artifact(access, identifier, kind):
    try:
        raw = base64.urlsafe_b64decode(access+'='*(-len(access)%4)).decode()
        owner, actual_id, actual_kind, expires, signature = raw.split(':')
        text = ':'.join((owner, actual_id, actual_kind, expires))
        if (not re.fullmatch('[a-f0-9]{64}', owner) or actual_id != identifier or actual_kind != kind
                or int(expires) < time.time() or not hmac.compare_digest(signature,
                    hmac.new(SIGNING_KEY, text.encode(), 'sha256').hexdigest())):
            raise ValueError()
        return owner
    except (ValueError, TypeError, UnicodeError):
        raise ValueError('Image or report access expired. Reopen the saved inspection.') from None


class SessionRepository:
    def __init__(self, directory, cloud_config=None, artifacts=None):
        self.directory = Path(directory)
        self.cloud_config=cloud_config
        self.artifacts=artifacts

    def current(self):
        owner = NAMESPACE.get()
        if not owner:
            raise ValueError('Workspace authorization is missing')
        if self.cloud_config and STAFF_TOKEN.get():
            from deployment.space.supabase_repository import StaffRepository
            return StaffRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)
        return SQLiteRepository(self.directory / owner / 'inspection.sqlite3')

    def decorate(self, record):
        if record is None:
            return None
        result = dict(record)
        for kind in ('image', 'heatmap', 'report'):
            if kind!='report' and result.get('storage')=='supabase' and result.get(kind+'_url','').startswith('https://'):
                continue
            result[kind+'_url'] = f"/api/inspections/{record['id']}/{kind}?access={capability(record['id'], kind)}"
        return result

    def save(self, record):
        return self.decorate(self.current().save(record))

    def get(self, identifier):
        return self.decorate(self.current().get(identifier))

    def list(self, *args, **kwargs):
        return [self.decorate(row) for row in self.current().list(*args, **kwargs)]

    def __getattr__(self, name):
        return getattr(self.current(), name)
