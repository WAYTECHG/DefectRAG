"""Owner-only account persistence. User JWT + RLS; no privileged API credential."""
import hashlib
import json
import httpx
from urllib.parse import quote
from .supabase_repository import StaffRepository


class PersonalRepository(StaffRepository):
    table='personal_inspections'
    bucket='personal-inspections'
    notes_table='personal_notes'
    storage_type='supabase_personal'
    workspace='personal'
    workspace_stats_enabled=True

    def _raw_any(self,identifier):
        rows=self.request('GET','/rest/v1/'+self.table,params={
            'id':'eq.'+identifier,'owner_id':'eq.'+self.user['id'],'select':'*','limit':'1'})
        return rows[0] if rows else None

    def raw(self,identifier,archived=False):
        row=self._raw_any(identifier)
        return row if row and bool(row.get('archived_at'))==archived else None

    def raw_list(self,category='',verdict='',batch='',limit=100,offset=0,archived=False):
        # RLS remains the authority; an explicit owner filter adds defense in depth.
        params={'owner_id':'eq.'+self.user['id'],'select':'*','order':'created_at.desc,id.desc',
                'archived_at':'not.is.null' if archived else 'is.null','limit':str(limit),'offset':str(offset)}
        for key,value in (('category',category),('verdict',verdict),('batch',batch)):
            if value:params['payload->>'+key]='eq.'+value
        return self.request('GET','/rest/v1/'+self.table,params=params)

    def _upload(self,bucket,identifier,kind,source):
        content=source.read_bytes()
        destination=f"{self.user['id']}/{identifier}/{kind}-{hashlib.sha256(content).hexdigest()}.jpg"
        # The hash is part of the immutable object name. A replay may encounter
        # an already uploaded object after a failed row insert; never overwrite it.
        self.request('POST','/storage/v1/object/'+bucket+'/'+destination,content=content,
            headers={'Content-Type':'image/jpeg','x-upsert':'false'},ignore_conflict=True)
        return destination

    @staticmethod
    def _same(existing,record):
        previous=existing['payload']
        if previous.get('request_fingerprint') and record.get('request_fingerprint'):
            return previous['request_fingerprint']==record['request_fingerprint']
        return all(previous.get(k)==record.get(k) for k in ('id','category','batch','score','threshold','model_id'))

    def save(self,record,conversation=None):
        messages=conversation or []
        if len(json.dumps(messages).encode())>40000:raise ValueError('Saved conversation is too large to import safely.')
        existing=self._raw_any(record['id'])
        if existing:
            if existing.get('archived_at') or not self._same(existing,record):
                raise ValueError('Inspection ID already exists with different data or is archived. No overwrite occurred.')
            return self.decorate(existing)
        paths={kind+'_path':self._upload(self.bucket,record['id'],kind,self.artifacts/f"{record['id']}{suffix}.jpg")
               for kind,suffix in (('image',''),('heatmap','_heatmap'))}
        payload={k:v for k,v in record.items() if not k.endswith('_url') and k not in ('storage','workspace','owner_id')}
        row={'id':record['id'],'owner_id':self.user['id'],'created_at':record['created_at'],
             'payload':payload,'conversation':messages,'archived_at':None,**paths}
        self.request('POST','/rest/v1/'+self.table,json=row,headers={'Prefer':'return=minimal'},ignore_conflict=True)
        confirmed=self._raw_any(record['id'])
        if not confirmed or not self._same(confirmed,record):
            raise RuntimeError('Personal save could not be verified. No durable success was reported.')
        return self.decorate(confirmed)

    def add_conversation(self,identifier,question,answer):
        return self.request('POST','/rest/v1/rpc/defectrag_personal_action',json={
            'p_id':identifier,'p_action':'conversation','p_question':question,'p_answer':answer})

    def acknowledge(self,identifier):
        return bool(self.request('POST','/rest/v1/rpc/defectrag_personal_action',json={
            'p_id':identifier,'p_action':'acknowledge'}))

    def archive(self,category='',verdict='',batch=''):
        ids=[row['id'] for row in self.raw_list(category,verdict,batch,limit=500)]
        changed=self.request('POST','/rest/v1/rpc/defectrag_personal_archive',json={'p_ids':ids,'p_restore':False}) if ids else 0
        return {'archived':changed,'scope':'up to 500 matching personal records; files retained'}

    def restore(self,identifiers):
        return {'restored':self.request('POST','/rest/v1/rpc/defectrag_personal_archive',json={'p_ids':identifiers,'p_restore':True})}

    def share(self,identifier,include_conversation=False):
        row=self.raw(identifier)
        if not row:raise ValueError('An active owned personal inspection is required to share.')
        existing=self.request('GET','/rest/v1/shared_inspections',params={'id':'eq.'+identifier,'select':'id,owner_id','limit':'1'})
        if existing:
            if existing[0]['owner_id']!=self.user['id']:raise ValueError('Inspection ID conflict; nothing was shared.')
            return {'alreadyShared':True}
        paths={}
        for kind in ('image','heatmap'):
            # Copy immutable bytes with the same user JWT. Personal object reads
            # remain owner-only; other staff get only the explicit team copy.
            path=row[kind+'_path']
            with httpx.Client(timeout=25,trust_env=False) as client:
                response=client.get(self.config['url']+'/storage/v1/object/authenticated/'+self.bucket+'/'+quote(path,safe='/'),headers=self.headers)
            if not response.is_success or len(response.content)>10*1024*1024:
                raise RuntimeError('Private image could not be copied. No team success was reported.')
            digest=hashlib.sha256(response.content).hexdigest()
            target=f"{self.user['id']}/{identifier}/{kind}-{digest}.jpg"
            self.request('POST','/storage/v1/object/team-inspections/'+target,content=response.content,
                headers={'Content-Type':'image/jpeg','x-upsert':'false'},ignore_conflict=True)
            paths[kind]=target
        inserted=self.request('POST','/rest/v1/rpc/defectrag_share_personal',json={
            'p_id':identifier,'p_image_path':paths['image'],'p_heatmap_path':paths['heatmap'],
            'p_include_conversation':bool(include_conversation)})
        return {'alreadyShared':not inserted}
