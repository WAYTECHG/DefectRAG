"""Explicit-consent public snapshots. Never expose private inspection identifiers."""
import base64
import hashlib
import hmac
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import threading
import uuid
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, Query
from PIL import Image
from pydantic import BaseModel, ConfigDict, StrictBool

from .config import CATEGORIES
from .storage import now

FIELDS = ('category', 'verdict', 'score', 'threshold', 'uncertainty_margin',
          'model_id', 'localization', 'scope')


def public_measurement(record):
    result = {key: record[key] for key in FIELDS if key in record}
    if result.get('category') not in CATEGORIES or result.get('verdict') not in ('Good','Anomalous','Uncertain'):
        raise HTTPException(422, 'A completed supported inspection is required.')
    for key in ('score','threshold','uncertainty_margin'):
        value=result.get(key)
        if key=='uncertainty_margin' and value is None:
            continue
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
            raise HTTPException(422, 'Inspection measurements are invalid.')
    return result


def thumbnail(content):
    with Image.open(BytesIO(content)) as source:
        image=source.convert('RGB')
        image.thumbnail((512,512))
        out=BytesIO()
        # A new JPEG drops EXIF, original filename and embedded image metadata.
        image.save(out,format='JPEG',quality=70,optimize=True)
    if len(out.getvalue())>120000:
        raise HTTPException(422,'Public preview is too large.')
    return base64.b64encode(out.getvalue()).decode('ascii')


class LocalGallery:
    """Durable on local disk only; deliberately NOT the hosted storage fallback."""
    def __init__(self,path,key):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.key=key.encode(); self.lock=threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,created_at TEXT,owner TEXT,source TEXT,payload TEXT,image TEXT,heatmap TEXT,visible INTEGER,UNIQUE(owner,source))')

    def connect(self):
        db=sqlite3.connect(self.path,timeout=20); db.row_factory=sqlite3.Row
        return db

    def identity(self,value):
        return hmac.new(self.key,value.encode(),'sha256').hexdigest()

    def read(self,identifier=None,offset=0):
        with self.connect() as db:
            if identifier:
                rows=db.execute('SELECT * FROM entries WHERE id=? AND visible=1',(identifier,)).fetchall()
            else:
                rows=db.execute('SELECT * FROM entries WHERE visible=1 ORDER BY created_at DESC,id DESC LIMIT 12 OFFSET ?',(offset,)).fetchall()
        return [dict(id=r['id'],created_at=r['created_at'],measurement=json.loads(r['payload']),
                     **({'image':r['image'],'heatmap':r['heatmap']} if identifier else {})) for r in rows]

    def write(self,action,owner,source='',payload=None,image='',heatmap='',identifier=None,moderator=False):
        with self.lock,self.connect() as db:
            if action=='status':
                row=db.execute('SELECT id,visible FROM entries WHERE owner=? AND source=?',(owner,source)).fetchone()
                return dict(row) if row else None
            if action=='remove':
                cursor=db.execute('UPDATE entries SET visible=0 WHERE id=? AND (owner=? OR ?=1)',(identifier,owner,int(moderator)))
                if not cursor.rowcount:raise HTTPException(404,'Published item is unavailable or belongs to another browser/account.')
                return {'removed':True}
            existing=db.execute('SELECT id,visible FROM entries WHERE owner=? AND source=?',(owner,source)).fetchone()
            if existing:return dict(existing)
            if db.execute('SELECT count(*) FROM entries').fetchone()[0]>=100 or db.execute('SELECT count(*) FROM entries WHERE owner=?',(owner,)).fetchone()[0]>=5:
                raise HTTPException(429,'Demo gallery capacity reached (100 total, 5 per publisher).')
            identifier=uuid.uuid4().hex
            db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,1)',(identifier,now(),owner,source,json.dumps(payload),image,heatmap))
            return {'id':identifier,'visible':True}


class SupabaseGallery:
    def __init__(self,config,key):
        if not re.fullmatch('[a-f0-9]{64}',key):
            raise ValueError('DEFECTRAG_GALLERY_KEY must be a dedicated 64-character lowercase hex secret.')
        self.config=config; self.key=key.encode()

    identity=LocalGallery.identity

    def rpc(self,name,payload):
        try:
            with httpx.Client(timeout=25,trust_env=False) as client:
                response=client.post(self.config['url']+'/rest/v1/rpc/'+name,
                    headers={'apikey':self.config['key']},json=payload)
        except httpx.HTTPError:
            raise HTTPException(503,'Gallery storage is unavailable. Private inspection remains saved.') from None
        if not response.is_success:
            # Do not forward request bodies, secret, SQL details or database exceptions.
            code=response.json().get('code') if response.headers.get('content-type','').startswith('application/json') else None
            if code=='P0001':
                raise HTTPException(409,'Gallery operation declined: item withdrawn, publisher limit or gallery capacity reached.')
            raise HTTPException(503,'Gallery setup or storage is unavailable. Private inspection remains saved.')
        return response.json()

    def read(self,identifier=None,offset=0):
        return self.rpc('defectrag_gallery_read',{'p_id':identifier,'p_offset':offset})

    def write(self,action,owner,source='',payload=None,image='',heatmap='',identifier=None,moderator=False):
        return self.rpc('defectrag_gallery_write',{'p_key':self.key.decode(),'p_action':action,
            'p_owner':owner,'p_source':source,'p_payload':payload or {},'p_image':image,
            'p_heatmap':heatmap,'p_id':identifier,'p_moderator':moderator})


class PublishConsent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    consent: StrictBool


def mount_gallery(app,repo,artifacts,gallery=None,owner=lambda:'local-operator',cloud_origin=''):
    def ready():
        if gallery is None:raise HTTPException(503,'Community gallery is awaiting its separate Supabase setup. Private inspections are unaffected.')
        return gallery

    def principal():
        current=repo.current() if hasattr(repo,'current') else repo
        staff=getattr(current,'staff',None)
        user=getattr(current,'user',None)
        return ('staff:'+user['id'] if user else 'browser:'+owner()), bool(staff)

    def keys(identifier):
        actor,staff=principal()
        return ready().identity(actor),ready().identity('inspection:'+identifier),staff

    def saved(identifier):
        if not re.fullmatch('[a-f0-9]{32}',identifier):raise HTTPException(404,'Inspection not found')
        record=repo.get(identifier)
        if not record:raise HTTPException(404,'Inspection not found')
        return record

    @app.get('/api/gallery')
    def listing(offset:int=Query(0,ge=0,le=100)):
        if gallery is None:return {'data':{'enabled':False,'items':[]}}
        return {'data':{'enabled':True,'items':gallery.read(offset=offset)}}

    @app.get('/api/gallery/{identifier}')
    def detail(identifier:str):
        try:uuid.UUID(identifier)
        except ValueError:raise HTTPException(404,'Gallery item not found') from None
        rows=ready().read(identifier)
        if not rows:raise HTTPException(404,'Gallery item not found or withdrawn')
        return {'data':rows[0]}

    @app.get('/api/inspections/{identifier}/publication')
    def publication(identifier:str):
        if gallery is None:return {'data':{'enabled':False,'publication':None}}
        saved(identifier);actor,source,_=keys(identifier)
        return {'data':{'enabled':True,'publication':gallery.write('status',actor,source)}}

    @app.post('/api/inspections/{identifier}/publication')
    def publish(identifier:str,body:PublishConsent):
        ready()
        if body.consent is not True:raise HTTPException(422,'Explicit public publication consent is required.')
        record=saved(identifier);actor,source,_=keys(identifier)
        if record.get('storage','').startswith('supabase'):
            current=repo.current()
            if record.get('owner_id')!=current.user['id']:
                raise HTTPException(403,'Only the original staff uploader can publish this inspection.')
        measurement=public_measurement(record)
        previews=[]
        for kind,suffix in (('image',''),('heatmap','_heatmap')):
            path=Path(artifacts)/f'{identifier}{suffix}.jpg'
            if not record.get('storage','').startswith('supabase'):
                if not path.is_file():raise HTTPException(409,'Saved image is unavailable. Nothing was published.')
                content=path.read_bytes()
            else:
                url=record.get(kind+'_url','')
                if not cloud_origin or urlparse(url).netloc!=urlparse(cloud_origin).netloc or not url.startswith('https://'):
                    raise HTTPException(403,'Saved image origin is not authorized.')
                try:
                    with httpx.Client(timeout=20,trust_env=False,follow_redirects=False) as client:
                        with client.stream('GET',url) as response:
                            response.raise_for_status(); chunks=[];size=0
                            for chunk in response.iter_bytes():
                                size+=len(chunk)
                                if size>5*1024*1024:raise HTTPException(413,'Saved image exceeds gallery limit.')
                                chunks.append(chunk)
                            content=b''.join(chunks)
                except httpx.HTTPError:raise HTTPException(503,'Saved image is temporarily unavailable.') from None
            previews.append(thumbnail(content))
        return {'data':gallery.write('publish',actor,source,measurement,*previews)}

    @app.post('/api/gallery/{identifier}/withdraw')
    def withdraw(identifier:str):
        try:uuid.UUID(identifier)
        except ValueError:raise HTTPException(404,'Gallery item not found') from None
        actor,_,_=keys('withdraw')
        return {'data':gallery.write('remove',actor,identifier=identifier)}

    @app.post('/api/gallery/{identifier}/moderate')
    def moderate(identifier:str):
        try:uuid.UUID(identifier)
        except ValueError:raise HTTPException(404,'Gallery item not found') from None
        actor,_,staff=keys('moderate')
        if not staff:raise HTTPException(403,'Approved staff access is required for gallery moderation.')
        return {'data':gallery.write('remove',actor,identifier=identifier,moderator=True)}
