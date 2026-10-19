"""Use the existing Supabase schema through each staff user's JWT and RLS."""
import json
import logging
from pathlib import Path
import re
import threading
import time
from urllib.parse import quote
import httpx

log=logging.getLogger('defectrag.cloud')
_staff_cache={}
_cache_lock=threading.Lock()


def read_public_config(path):
    text=Path(path).read_text(encoding='utf8')
    output={}
    for source,key in (('supabaseUrl','url'),('supabasePublishableKey','key')):
        match=re.search(r'''["']?'''+source+r'''["']?\s*:\s*["']([^"']*)''',text)
        output[key]=match.group(1) if match else ''
    if not output['url'].startswith('https://') or not output['key'].startswith('sb_publishable_'):
        raise ValueError('Supabase public settings are not configured')
    return output


class StaffRepository:
    def __init__(self,config,token,artifacts):
        self.config,self.token,self.artifacts=config,token,Path(artifacts)
        self.headers={'apikey':config['key'],'Authorization':'Bearer '+token}
        # Do not trust decoded JWT claims. Supabase validates the token, and the
        # staff allowlist is read through its existing authenticated policies.
        with _cache_lock:
            cached=_staff_cache.get(token)
        if cached and cached[0]>time.time():
            self.user,self.staff=cached[1:]
        else:
            self.user=self.request('GET','/auth/v1/user')
            rows=self.request('GET','/rest/v1/staff_members',params={'user_id':'eq.'+self.user['id'],'select':'user_id,display_name,role','limit':'1'})
            if not rows:
                raise ValueError('Your account is not on the staff allowlist')
            self.staff=rows[0]
            with _cache_lock:
                if len(_staff_cache)>=256:
                    _staff_cache.clear()
                _staff_cache[token]=(time.time()+45,self.user,self.staff)

    def request(self,method,path,**kwargs):
        headers={**self.headers,**kwargs.pop('headers',{})}
        with httpx.Client(timeout=30,trust_env=False) as client:
            response=client.request(method,self.config['url']+path,headers=headers,**kwargs)
        if not response.is_success:
            try:
                detail=response.json()
                code=detail.get('code',detail.get('error','unknown'))
            except (ValueError,AttributeError):
                code='unexpected_response'
            if response.status_code in (401,403):
                raise ValueError('Staff session expired or access denied. Sign in again.')
            if code in ('PGRST202','PGRST205'):
                raise ValueError('Required Supabase function/table is unavailable. Apply the reviewed additive migration.')
            raise RuntimeError(f'Supabase request failed ({response.status_code}, {code}); no durable success was reported.')
        return response.json() if response.content else None

    def decorate(self,row):
        if not row:
            return None
        record=dict(row['payload'])
        record['storage']='supabase'
        record['owner_id']=row['owner_id']
        for kind in ('image','heatmap'):
            result=self.request('POST','/storage/v1/object/sign/team-inspections/'+quote(row[kind+'_path'],safe='/'),json={'expiresIn':600})
            signed=result.get('signedURL',result.get('signedUrl'))
            record[kind+'_url']=signed if signed.startswith('https://') else self.config['url']+'/storage/v1'+signed
        return record

    def raw(self,identifier,archived=False):
        rows=self.request('GET','/rest/v1/shared_inspections',params={'id':'eq.'+identifier,'select':'*','limit':'1',
            'archived_at':'not.is.null' if archived else 'is.null'})
        return rows[0] if rows else None

    def save(self,record):
        paths={}
        for kind,suffix in (('image',''),('heatmap','_heatmap')):
            source=self.artifacts/f"{record['id']}{suffix}.jpg"
            destination=f"{self.user['id']}/{record['id']}/{kind}.jpg"
            self.request('POST','/storage/v1/object/team-inspections/'+destination,
                content=source.read_bytes(),headers={'Content-Type':'image/jpeg','x-upsert':'false'})
            paths[kind+'_path']=destination
        payload={key:value for key,value in record.items() if not key.endswith('_url')}
        row={'id':record['id'],'owner_id':self.user['id'],'created_at':record['created_at'],
             'payload':payload,'conversation':[],**paths}
        self.request('POST','/rest/v1/shared_inspections',json=row,headers={'Prefer':'return=minimal'})
        return self.decorate(row)

    def get(self,identifier):
        return self.decorate(self.raw(identifier))

    def raw_list(self,category='',verdict='',batch='',limit=100,offset=0,archived=False):
        params={'select':'id,owner_id,created_at,payload,image_path,heatmap_path,archived_at','archived_at':'not.is.null' if archived else 'is.null',
                'order':'created_at.desc','limit':str(limit),'offset':str(offset)}
        for key,value in (('category',category),('verdict',verdict),('batch',batch)):
            if value:
                params['payload->>'+key]='eq.'+value
        return self.request('GET','/rest/v1/shared_inspections',params=params)

    def list(self,category='',verdict='',batch='',limit=100,offset=0,archived=False):
        # Lists need no images until a record is opened. Avoid two storage API
        # calls per row for large history pages.
        rows=[]
        while len(rows)<limit:
            count=min(1000,limit-len(rows))
            page=self.raw_list(category,verdict,batch,count,offset+len(rows),archived)
            rows.extend(page)
            if len(page)<count:
                break
        return [{**row['payload'],'storage':'supabase','owner_id':row['owner_id']} for row in rows]

    def stats(self):
        rows=self.list(limit=1000)
        counts={kind:sum(row['verdict']==kind for row in rows) for kind in ('Good','Anomalous','Uncertain')}
        batches={}
        for row in rows:
            item=batches.setdefault(row.get('batch',''),{'batch':row.get('batch',''),'total':0,'anomalous':0,'uncertain':0})
            item['total']+=1
            item['anomalous']+=row['verdict']=='Anomalous'
            item['uncertain']+=row['verdict']=='Uncertain'
        return {'total':len(rows),'counts':counts,'batches':list(batches.values()),'failed_requests':0,
                'scope':'latest 1000 active staff records; model failures are in server logs'}

    def messages(self,identifier):
        row=self.raw(identifier)
        return row['conversation'][-20:] if row else []

    def add_conversation(self,identifier,question,answer):
        self.request('POST','/rest/v1/rpc/defectrag_append_conversation',json={'p_id':identifier,'p_question':question,'p_answer':answer})

    def alerts(self):
        return [{'id':row['id'],'inspection_id':row['id'],'created_at':row['created_at'],
                 'kind':row['verdict'],'acknowledged':int(row.get('alert_acknowledged',False))}
                for row in self.list(limit=1000) if row['verdict']!='Good']

    def acknowledge(self,identifier):
        return bool(self.request('POST','/rest/v1/rpc/defectrag_acknowledge_review',json={'p_id':identifier}))

    def archive(self,category='',verdict='',batch=''):
        rows=self.raw_list(category,verdict,batch,limit=500)
        ids=[row['id'] for row in rows if self.staff['role']=='developer' or row['owner_id']==self.user['id']]
        count=self.request('POST','/rest/v1/rpc/archive_team_inspections',json={'p_ids':ids}) if ids else 0
        return {'archived':count,'archive_batch':'supabase-audit','scope':'own visible records, or developer-authorized records'}

    def restore(self,identifiers):
        return {'restored':self.request('POST','/rest/v1/rpc/restore_team_inspections',json={'p_ids':identifiers})}

    def failure(self,category,error):
        log.warning('Model failure in authenticated workspace: category=%s error=%s',category,error)

    def add_review(self,identifier,status,decision,note=''):
        from backend.reviews import review_body,validate_review
        body=review_body(status,decision,note)
        rows=self.request('POST','/rest/v1/staff_notes',json={
            'inspection_id':identifier,'author_id':self.user['id'],'body':body},
            headers={'Prefer':'return=representation'})
        return {**validate_review(status,decision,note),'reviewer':self.staff['display_name'],
                'reviewer_id':self.user['id'],'created_at':rows[0]['created_at']}

    def review_notes(self,identifier):
        rows=self.request('GET','/rest/v1/staff_notes',params={
            'inspection_id':'eq.'+identifier,'select':'body,author_id,created_at','order':'created_at.asc'})
        people=self.request('GET','/rest/v1/staff_members',params={'select':'user_id,display_name'})
        directory={row['user_id']:row['display_name'] for row in people}
        return [{**row,'reviewer':directory.get(row['author_id'],'Staff member')} for row in rows]

    def review_history(self,identifier):
        from backend.reviews import parse_review
        return [{**value,'reviewer':row['reviewer'],'reviewer_id':row['author_id'],'created_at':row['created_at']}
                for row in self.review_notes(identifier) if (value:=parse_review(row['body']))]
