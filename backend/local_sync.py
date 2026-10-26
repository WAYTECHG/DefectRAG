"""Opt-in owner-scoped local mirror. JWTs stay in memory; Supabase is authoritative.

No cloud write occurs without the current user's JWT/native MFA/owner checks.
Existing unassigned SQLite history is deliberately never imported automatically.
"""
from contextvars import ContextVar
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time
import uuid

from .storage import SQLiteRepository,now
from deployment.space.sessions import SessionRepository,STAFF_TOKEN,WORKSPACE,NAMESPACE
from deployment.space.personal_repository import PersonalRepository
from deployment.space.supabase_repository import StaffRepository

BOUND=ContextVar('defectrag_local_repository',default=None)

def filesystem_path(value):
    value=Path(value).resolve()
    if os.name=='nt' and not str(value).startswith('\\\\?\\'):
        text=str(value)
        return Path('\\\\?\\UNC\\'+text[2:] if text.startswith('\\\\') else '\\\\?\\'+text)
    return value


class LocalMirror(SQLiteRepository):
    def __init__(self,path,owner,artifacts):
        super().__init__(filesystem_path(path))
        self.user={'id':str(uuid.UUID(owner))};self.artifacts=filesystem_path(artifacts)
        self.artifacts.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sync_records(id TEXT PRIMARY KEY,version INTEGER NOT NULL DEFAULT 0,remote TEXT);
            CREATE TABLE IF NOT EXISTS sync_queue(id TEXT PRIMARY KEY,inspection_id TEXT NOT NULL,action TEXT NOT NULL,data TEXT NOT NULL,
             state TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL DEFAULT 0,error TEXT,sequence INTEGER UNIQUE);
            CREATE TABLE IF NOT EXISTS sync_notes(id TEXT PRIMARY KEY,inspection_id TEXT NOT NULL,body TEXT NOT NULL,author_id TEXT,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sync_meta(key TEXT PRIMARY KEY,value TEXT);
            CREATE TABLE IF NOT EXISTS sync_conflict_backups(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,snapshot TEXT NOT NULL);
            ''')

    def _queue(self,db,identifier,action,data):
        operation=str(uuid.uuid4())
        db.execute('INSERT INTO sync_queue(id,inspection_id,action,data,sequence) VALUES(?,?,?,?,(SELECT coalesce(max(sequence),0)+1 FROM sync_queue))',
                   (operation,identifier,action,json.dumps(data)))
        return operation

    def save(self,record):
        with self.lock,self.connect() as db:
            db.execute('INSERT INTO inspections VALUES(?,?,?,?,?,?)',(record['id'],record['created_at'],record['category'],record['verdict'],record.get('batch',''),json.dumps(record)))
            db.execute('INSERT INTO sync_records(id) VALUES(?)',(record['id'],))
            if record['verdict']!='Good':
                db.execute('INSERT INTO alerts VALUES(?,?,?,?,0)',(record['id'],record['id'],record['created_at'],record['verdict']))
            clean={k:v for k,v in record.items() if not k.endswith('_url') and k not in ('owner_id','workspace','storage','sync')}
            self._queue(db,record['id'],'create',{'record':clean})
        return self.get(record['id'])

    def get(self,identifier):
        value=super().get(identifier)
        if value:value.update(storage='local_account',workspace='personal',owner_id=self.user['id'])
        return value

    def list(self,*args,**kwargs):
        return [{**row,'storage':'local_account','workspace':'personal','owner_id':self.user['id']} for row in super().list(*args,**kwargs)]

    def add_conversation(self,identifier,question,answer):
        if not self.get(identifier):raise ValueError('Active personal inspection required')
        if not 3<=len(question)<=1200 or len(json.dumps(answer).encode())>40000:raise ValueError('Conversation exceeds the synchronization limits')
        with self.lock,self.connect() as db:
            db.executemany('INSERT INTO messages(inspection_id,created_at,role,payload) VALUES(?,?,?,?)',[
                (identifier,now(),'user',json.dumps({'question':question})),(identifier,now(),'assistant',json.dumps(answer))])
            self._queue(db,identifier,'conversation',{'question':question,'answer':answer})

    def add_review(self,identifier,status,decision,note=''):
        from .reviews import review_body,validate_review
        if not self.get(identifier):raise ValueError('Active personal inspection required')
        body=review_body(status,decision,note);created=now()
        with self.lock,self.connect() as db:
            operation=self._queue(db,identifier,'review',{'body':body})
            db.execute('INSERT INTO sync_notes VALUES(?,?,?,?,?)',(operation,identifier,body,self.user['id'],created))
        return {**validate_review(status,decision,note),'reviewer':'Authenticated local owner','reviewer_id':self.user['id'],'created_at':created}

    def review_notes(self,identifier):
        with self.connect() as db:rows=db.execute('SELECT * FROM sync_notes WHERE inspection_id=? ORDER BY created_at,id',(identifier,)).fetchall()
        return [{**dict(row),'reviewer':'Personal workspace owner'} for row in rows]

    def review_history(self,identifier):
        from .reviews import parse_review
        return [{**value,'reviewer':row['reviewer'],'reviewer_id':row['author_id'],'created_at':row['created_at']}
                for row in self.review_notes(identifier) if (value:=parse_review(row['body']))]

    def acknowledge(self,identifier):
        if not self.get(identifier):return False
        with self.lock,self.connect() as db:
            changed=db.execute('UPDATE alerts SET acknowledged=1 WHERE id=?',(identifier,)).rowcount
            if changed:self._queue(db,identifier,'acknowledge',{})
        return bool(changed)

    def archive(self,category='',verdict='',batch=''):
        rows=self.list(category,verdict,batch,limit=10000)
        with self.lock,self.connect() as db:
            for row in rows:
                db.execute('INSERT OR IGNORE INTO inspection_archives VALUES(?,?,?)',(row['id'],now(),'personal-sync'))
                self._queue(db,row['id'],'archive',{})
        return {'archived':len(rows),'scope':'owner-only local mirror; cloud synchronization pending'}

    def restore(self,identifiers):
        changed=0
        with self.lock,self.connect() as db:
            for identifier in identifiers:
                if db.execute('DELETE FROM inspection_archives WHERE id=?',(identifier,)).rowcount:
                    self._queue(db,identifier,'restore',{});changed+=1
        return {'restored':changed}

    def status(self):
        with self.connect() as db:
            counts={row['state']:row['n'] for row in db.execute('SELECT state,count(*) n FROM sync_queue GROUP BY state')}
            conflicts=[dict(row) for row in db.execute("SELECT DISTINCT inspection_id FROM sync_queue WHERE state='conflict'")]
            meta=dict(db.execute('SELECT key,value FROM sync_meta'))
        return {'workspace':'personal','storage':'local_account','pending':counts.get('pending',0),
                'conflicts':conflicts,'last_synchronized':meta.get('last_synchronized'),
                'last_backup':meta.get('last_backup'),
                'scan_in_progress':bool(meta.get('cursor')),'state':'conflict' if conflicts else 'pending' if counts.get('pending') else 'synced' if meta.get('last_synchronized') else 'not_synchronized'}

    def _snapshot(self,db,identifier):
        return {table:[dict(row) for row in db.execute('SELECT * FROM '+table+' WHERE '+key+'=?',(identifier,))]
                for table,key in [('inspections','id'),('messages','inspection_id'),('alerts','inspection_id'),('inspection_archives','id'),('sync_notes','inspection_id'),('sync_queue','inspection_id')]}

    def install(self,row,notes):
        """Called only after immutable artifact hashes have been verified."""
        identifier=row['id'];record=dict(row['payload'])
        if record.get('id')!=identifier or row['owner_id']!=self.user['id']:raise ValueError('Cloud ownership mismatch')
        from .config import CATEGORIES
        if (record.get('category') not in CATEGORIES or record.get('verdict') not in ('Good','Anomalous','Uncertain')
            or type(row.get('sync_version')) is not int or row['sync_version']<1
            or not isinstance(row.get('conversation',[]),list)
            or any(message.get('role') not in ('user','assistant') for message in row.get('conversation',[]))
            or any(note.get('author_id')!=self.user['id'] or note.get('inspection_id')!=identifier for note in notes)):
            raise ValueError('Invalid personal synchronization snapshot')
        with self.lock,self.connect() as db:
            if db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND state IN ('pending','conflict')",(identifier,)).fetchone():return False
            db.execute('INSERT OR REPLACE INTO inspections VALUES(?,?,?,?,?,?)',(identifier,row['created_at'],record['category'],record['verdict'],record.get('batch',''),json.dumps(record)))
            db.execute('INSERT OR REPLACE INTO sync_records VALUES(?,?,?)',(identifier,row['sync_version'],json.dumps(row)))
            db.execute('DELETE FROM messages WHERE inspection_id=?',(identifier,))
            for message in row.get('conversation',[]):
                payload={k:v for k,v in message.items() if k not in ('role','created_at')}
                db.execute('INSERT INTO messages(inspection_id,created_at,role,payload) VALUES(?,?,?,?)',(identifier,message.get('created_at',row['created_at']),message['role'],json.dumps(payload)))
            db.execute('DELETE FROM alerts WHERE inspection_id=?',(identifier,))
            if record['verdict']!='Good':db.execute('INSERT INTO alerts VALUES(?,?,?,?,?)',(identifier,identifier,row['created_at'],record['verdict'],int(bool(record.get('alert_acknowledged')))))
            if row.get('archived_at'):db.execute('INSERT OR REPLACE INTO inspection_archives VALUES(?,?,?)',(identifier,row['archived_at'],'cloud'))
            else:db.execute('DELETE FROM inspection_archives WHERE id=?',(identifier,))
            db.execute('DELETE FROM sync_notes WHERE inspection_id=?',(identifier,))
            for note in notes:db.execute('INSERT INTO sync_notes VALUES(?,?,?,?,?)',(note['id'],identifier,note['body'],note['author_id'],note['created_at']))
        return True


class SyncEngine:
    def __init__(self,local,cloud):self.local,self.cloud=local,cloud

    def _notes(self,identifier):
        result=[];offset=0
        while True:
            page=self.cloud.request('GET','/rest/v1/personal_notes',params={
                'inspection_id':'eq.'+identifier,'author_id':'eq.'+self.local.user['id'],
                'select':'*','order':'created_at.asc,id.asc','limit':'200','offset':str(offset)})
            result.extend(page)
            if len(page)<200:return result
            offset+=len(page)

    def _download(self,row):
        identifier=row['id'];owner=self.local.user['id']
        if row['owner_id']!=owner or not re.fullmatch('[a-f0-9]{32}',identifier):raise ValueError('Invalid cloud inspection ownership')
        for kind,suffix in (('image',''),('heatmap','_heatmap')):
            source=row[kind+'_path']
            match=re.fullmatch(re.escape(owner+'/'+identifier+'/'+kind)+r'-([a-f0-9]{64})\.jpg',source)
            if not match:raise ValueError('Invalid immutable personal artifact path')
            target=self.local.artifacts/(identifier+suffix+'.jpg');digest=match.group(1)
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==digest:continue
            if shutil.disk_usage(self.local.artifacts).free<50*1024*1024:raise RuntimeError('Local disk space is insufficient')
            content=self.cloud._read_private_image(source)
            if hashlib.sha256(content).hexdigest()!=digest:raise RuntimeError('Cloud artifact checksum mismatch')
            temporary=target.with_suffix('.part');temporary.write_bytes(content);temporary.replace(target)

    def cycle(self,budget=12,maximum=5):
        if not self.local.lock.acquire(blocking=False):return {**self.local.status(),'state':'syncing'}
        deadline=time.monotonic()+budget;error=None
        try:
            with self.local.connect() as db:
                pending=[dict(row) for row in db.execute("""SELECT q.* FROM sync_queue q WHERE q.state='pending' AND q.due<=?
                 AND NOT EXISTS(SELECT 1 FROM sync_queue earlier WHERE earlier.inspection_id=q.inspection_id
                  AND earlier.sequence<q.sequence AND earlier.state IN ('pending','conflict')) ORDER BY q.sequence LIMIT ?""",(time.time(),maximum))]
            if any(operation['action']=='create' for operation in pending):
                # Fail before uploading any objects if the reviewed additive SQL
                # is absent. PostgREST validates selected columns even on no rows.
                try:
                    self.cloud.request('GET','/rest/v1/personal_inspections',params={
                        'owner_id':'eq.'+self.local.user['id'],'select':'id,sync_version','limit':'1'})
                except (RuntimeError,ValueError):
                    with self.local.connect() as db:
                        for operation in pending:
                            attempts=operation['attempts']+1
                            db.execute('UPDATE sync_queue SET attempts=?,due=?,error=? WHERE id=?',
                                (attempts,time.time()+min(900,2**min(attempts,9)),'Cloud schema/account check unconfirmed; retry pending',operation['id']))
                    raise RuntimeError('Cloud schema/account check unavailable') from None
            blocked=set()
            for operation in pending:
                if time.monotonic()>deadline:break
                identifier=operation['inspection_id']
                if identifier in blocked:continue
                with self.local.connect() as db:
                    if db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND state='conflict'",(identifier,)).fetchone():continue
                    version=db.execute('SELECT version FROM sync_records WHERE id=?',(identifier,)).fetchone()[0]
                if operation['due']>time.time():blocked.add(identifier);continue
                data=json.loads(operation['data'])
                try:
                    if operation['action']=='create':
                        for kind,suffix in (('image',''),('heatmap','_heatmap')):
                            data[kind+'_path']=self.cloud._upload(self.cloud.bucket,identifier,kind,self.local.artifacts/(identifier+suffix+'.jpg'))
                    answer=self.cloud.request('POST','/rest/v1/rpc/defectrag_personal_sync_apply',json={
                        'p_operation':operation['id'],'p_id':identifier,'p_base':version,'p_action':operation['action'],'p_data':data})
                    with self.local.connect() as db:
                        if answer.get('conflict'):
                            db.execute("UPDATE sync_queue SET state='conflict',error='Cloud changed; review required' WHERE id=?",(operation['id'],));blocked.add(identifier)
                        else:
                            db.execute("UPDATE sync_queue SET state='sent',error=NULL WHERE id=?",(operation['id'],))
                            db.execute('UPDATE sync_records SET version=? WHERE id=?',(answer['version'],identifier))
                except (RuntimeError,ValueError):
                    # Raw errors may contain URLs/data; persist only a fixed status.
                    attempts=operation['attempts']+1
                    with self.local.connect() as db:db.execute('UPDATE sync_queue SET attempts=?,due=?,error=? WHERE id=?',
                        (attempts,time.time()+min(900,2**min(attempts,9)),'Cloud save unconfirmed; retry pending',operation['id']))
                    blocked.add(identifier);error='Some local changes are queued. Cloud save has not been confirmed.'
            if time.monotonic()<deadline:
                with self.local.connect() as db:
                    row=db.execute("SELECT value FROM sync_meta WHERE key='cursor'").fetchone();cursor=row[0] if row else ''
                params={'owner_id':'eq.'+self.local.user['id'],'select':'*','order':'id.asc','limit':str(maximum)}
                if cursor:params['id']='gt.'+cursor
                rows=self.cloud.request('GET','/rest/v1/personal_inspections',params=params)
                for row in rows:
                    if 'sync_version' not in row:raise ValueError('Reviewed personal synchronization migration is not installed')
                    if time.monotonic()>deadline:break
                    with self.local.connect() as db:
                        dirty=db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND state IN ('pending','conflict')",(row['id'],)).fetchone()
                    if not dirty:
                        self._download(row)
                        notes=self._notes(row['id'])
                        self.local.install(row,notes)
                    cursor=row['id']
                    with self.local.connect() as db:db.execute("INSERT OR REPLACE INTO sync_meta VALUES('cursor',?)",(cursor,))
                complete=not rows or (len(rows)<maximum and cursor==rows[-1]['id'])
                if complete:
                    with self.local.connect() as db:
                        db.execute("INSERT OR REPLACE INTO sync_meta VALUES('cursor','')")
                        db.execute("INSERT OR REPLACE INTO sync_meta VALUES('last_synchronized',?)",(now(),))
        except (RuntimeError,ValueError):error='Cloud synchronization is unavailable or its reviewed migration is pending. Local records remain saved.'
        finally:self.local.lock.release()
        result=self.local.status()
        if error:
            result['message']=error
            if not result['conflicts']:result['state']='pending' if result['pending'] else 'unavailable'
        return result

    def resolve(self,identifier,choice):
        if choice not in ('cloud','retry_local'):raise ValueError('Choose cloud or retry_local')
        rows=self.cloud.request('GET','/rest/v1/personal_inspections',params={'id':'eq.'+identifier,'owner_id':'eq.'+self.local.user['id'],'select':'*','limit':'1'})
        if not rows:raise ValueError('Owned cloud inspection unavailable; local copy was retained')
        row=rows[0]
        with self.local.lock,self.local.connect() as db:
            if not db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND state='conflict'",(identifier,)).fetchone():raise ValueError('No pending conflict for this record')
            backup=self.local._snapshot(db,identifier)
            backup_id=str(uuid.uuid4())
            db.execute('INSERT INTO sync_conflict_backups VALUES(?,?,?)',(backup_id,now(),json.dumps(backup)))
            db.execute("INSERT OR REPLACE INTO sync_meta VALUES('last_backup',?)",(backup_id,))
            if choice=='cloud':db.execute("UPDATE sync_queue SET state='discarded' WHERE inspection_id=? AND state IN ('pending','conflict')",(identifier,))
            else:
                # A different original immutable inspection is never overwritten.
                if db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND action='create' AND state='conflict'",(identifier,)).fetchone():raise ValueError('Inspection ID conflict cannot be rebased')
                db.execute("UPDATE sync_queue SET state='pending',due=0,error=NULL WHERE inspection_id=? AND state='conflict'",(identifier,))
                db.execute('UPDATE sync_records SET version=? WHERE id=?',(row['sync_version'],identifier))
        if choice=='cloud':
            self._download(row)
            notes=self._notes(identifier)
            self.local.install(row,notes)
        return self.local.status()


class LocalSyncRepository(SessionRepository):
    local_sync_enabled=True
    def __init__(self,directory,cloud_config,artifacts):
        super().__init__(Path(directory)/'local-sync',cloud_config,artifacts,personal_enabled=True)
        self.legacy=SQLiteRepository(Path(directory)/'inspection.sqlite3')
        self.mirrors={};self.mirror_lock=threading.Lock()

    def prepare(self):
        if STAFF_TOKEN.get():
            remote=PersonalRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts)
            if WORKSPACE.get()=='team':
                remote=StaffRepository(self.cloud_config,STAFF_TOKEN.get(),self.artifacts);remote.workspace_stats_enabled=True
                current=remote
            else:
                owner=str(uuid.UUID(remote.user['id']))
                with self.mirror_lock:
                    if owner not in self.mirrors:self.mirrors[owner]=LocalMirror(self.directory/'accounts'/owner/'inspection.sqlite3',owner,self.directory/'accounts'/owner/'artifacts')
                    current=self.mirrors[owner]
                current.staff=remote.staff
        else:
            if WORKSPACE.get()=='team':raise ValueError('Approved staff sign-in required')
            current=self.legacy;remote=None
        return current,remote

    @contextmanager
    def bind(self,prepared=None):
        marker=BOUND.set(prepared if prepared is not None else self.prepare())
        try:yield
        finally:BOUND.reset(marker)

    def current(self):
        if BOUND.get() is None:raise ValueError('Local account context is missing')
        return BOUND.get()[0]

    def get(self,identifier):return self.decorate(self.current().get(identifier))
    def messages(self,identifier):return self.current().messages(identifier)
    def add_conversation(self,*args):return self.current().add_conversation(*args)
    def review_repository(self,identifier):return self.current()
    def artifact_directory(self):return getattr(self.current(),'artifacts',self.artifacts)
    def artifact_bytes(self,identifier,kind):
        current=self.current()
        if isinstance(current,StaffRepository):return current.private_artifact(identifier,kind)
        return (self.artifact_directory()/(identifier+('_heatmap' if kind=='heatmap' else '')+'.jpg')).read_bytes()
    def status(self):
        current=self.current();staff=getattr(current,'staff',None)
        return {'personal_enabled':True,'workspace':WORKSPACE.get(),'authenticated':bool(staff),'role':staff.get('role') if staff else None,
                'storage':'local_account' if isinstance(current,LocalMirror) else 'supabase' if staff else 'local_disk','poll_seconds':15}
    def engine(self):
        local,remote=BOUND.get() or (None,None)
        if not isinstance(local,LocalMirror) or not remote:raise ValueError('Sign in with required MFA in Personal Workspace before synchronization')
        return SyncEngine(local,remote)

    def import_legacy(self,identifiers):
        local=self.engine().local;imported=0
        for identifier in identifiers:
            record=self.legacy.get(identifier)
            if not record:raise ValueError('An active local-only inspection is required')
            with local.lock,local.connect() as db:
                if db.execute('SELECT 1 FROM inspections WHERE id=?',(identifier,)).fetchone():continue
                record={k:v for k,v in record.items() if not k.endswith('_url') and k not in ('owner_id','workspace','storage')}
                record['import_provenance']='Explicit import from unassigned local history; original operator identity unverified'
                for suffix in ('','_heatmap'):
                    source=self.artifacts/(identifier+suffix+'.jpg');target=local.artifacts/source.name
                    if not source.is_file() or not 0<source.stat().st_size<=10*1024*1024:raise ValueError('Bounded local artifacts required')
                    if target.exists() and hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():raise ValueError('Local artifact conflict; no overwrite permitted')
                    if not target.exists():shutil.copy2(source,target)
                with self.legacy.connect() as old:
                    messages=[dict(row) for row in old.execute('SELECT * FROM messages WHERE inspection_id=? ORDER BY id',(identifier,))]
                if len(messages)>2000:raise ValueError('Conversation import exceeds the reviewed bound')
                db.execute('INSERT INTO inspections VALUES(?,?,?,?,?,?)',(identifier,record['created_at'],record['category'],record['verdict'],record.get('batch',''),json.dumps(record)))
                db.execute('INSERT INTO sync_records(id) VALUES(?)',(identifier,))
                local._queue(db,identifier,'create',{'record':record})
                if record['verdict']!='Good':db.execute('INSERT INTO alerts VALUES(?,?,?,?,0)',(identifier,identifier,record['created_at'],record['verdict']))
                for i in range(0,len(messages),2):
                    pair=messages[i:i+2]
                    if len(pair)!=2 or [m['role'] for m in pair]!=['user','assistant']:raise ValueError('Unpaired legacy conversation needs manual review')
                    question=json.loads(pair[0]['payload'])['question'];answer=json.loads(pair[1]['payload'])
                    if not 3<=len(question)<=1200 or len(json.dumps(answer).encode())>40000:raise ValueError('Legacy conversation exceeds cloud limits')
                    for message in pair:db.execute('INSERT INTO messages(inspection_id,created_at,role,payload) VALUES(?,?,?,?)',(identifier,message['created_at'],message['role'],message['payload']))
                    local._queue(db,identifier,'conversation',{'question':question,'answer':answer})
                for review in self.legacy.review_history(identifier):
                    body='Imported local review (original identity unverified): '+json.dumps(review)
                    if len(body)>2000:raise ValueError('Legacy review exceeds cloud limits')
                    operation=local._queue(db,identifier,'review',{'body':body})
                    db.execute('INSERT INTO sync_notes VALUES(?,?,?,?,?)',(operation,identifier,body,local.user['id'],review['created_at']))
                imported+=1
        return {'imported':imported,'status':local.status()}
    def share(self,identifier,include_conversation=False,personal_only=False):
        engine=self.engine();engine.cycle()
        with engine.local.connect() as db:
            if db.execute("SELECT 1 FROM sync_queue WHERE inspection_id=? AND state IN ('pending','conflict')",(identifier,)).fetchone():raise ValueError('Confirm private cloud synchronization before sharing with the team')
        if personal_only:return {'saved':True}
        return engine.cloud.share(identifier,include_conversation)
