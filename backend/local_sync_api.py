"""Loopback-only adapter for the optional private mirror; no privileged key."""
import re
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field
from starlette.concurrency import run_in_threadpool
from deployment.space.sessions import NAMESPACE,STAFF_TOKEN,WORKSPACE,namespace,remember_staff,stored_staff,authorize_artifact,artifact_workspace,capability


def mount_local_sync(app,repo,origins):
    @app.middleware('http')
    async def local_identity(request,call_next):
        path=request.url.path
        if path in ('/','/index.html','/config.js'):
            response=await call_next(request);response.headers['Cache-Control']='no-store';return response
        public=path in ('/api/health','/api/models','/api/evaluation','/api/benchmark/official','/api/samples') or path.startswith('/api/samples/') or (request.method=='GET' and (path=='/api/gallery' or re.fullmatch('/api/gallery/[a-f0-9-]{36}',path)))
        if not path.startswith('/api/') or public or request.method=='OPTIONS':return await call_next(request)
        # Never expose this account mirror as a LAN/public server. The existing
        # local-only workspace remains available with the feature disabled.
        if request.client and request.client.host not in ('127.0.0.1','::1','localhost','testclient'):
            return JSONResponse({'error':{'message':'Private local synchronization requires a loopback connection'}},status_code=403)
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/') not in origins:
            return JSONResponse({'error':{'message':'Untrusted local request origin'}},status_code=403)
        try:
            scope=request.headers.get('X-DefectRAG-Workspace','personal')
            if scope not in ('personal','team'):raise ValueError('Invalid workspace')
            artifact=re.fullmatch(r'/api/inspections/([a-f0-9]{32})/(image|heatmap|report)',path)
            if artifact and 'access' in request.query_params:
                owner=authorize_artifact(request.query_params['access'],*artifact.groups());scope=artifact_workspace(request.query_params['access'])
            elif path=='/api/export.csv' and 'access' in request.query_params:
                owner=authorize_artifact(request.query_params['access'],'workspace','csv');scope=artifact_workspace(request.query_params['access'])
            else:owner=namespace(request.headers.get('X-DefectRAG-Session',''))
            bearer=request.headers.get('authorization','').removeprefix('Bearer ')
            if request.headers.get('X-DefectRAG-Session'):remember_staff(owner,bearer)
            markers=[(NAMESPACE,NAMESPACE.set(owner)),(STAFF_TOKEN,STAFF_TOKEN.set(bearer or stored_staff(owner))),(WORKSPACE,WORKSPACE.set(scope))]
        except ValueError as error:return JSONResponse({'error':{'message':str(error)}},status_code=401)
        try:
            prepared=await run_in_threadpool(repo.prepare)
            with repo.bind(prepared):response=await call_next(request)
            response.headers['Cache-Control']='private, no-store'
            response.headers['X-DefectRAG-Export']='/api/export.csv?access='+capability('workspace','csv')
            return response
        except ValueError:
            return JSONResponse({'error':{'message':'Approved account, required MFA and Personal Workspace are needed. Open Staff workspace.','code':'authorization'}},status_code=403)
        except RuntimeError:
            return JSONResponse({'error':{'message':'Account verification or cloud connection is unavailable. Local records remain saved.'}},status_code=503)
        finally:
            for variable,marker in reversed(markers):variable.reset(marker)

    @app.post('/api/local-sync/run')
    def run():return {'data':repo.engine().cycle()}

    @app.get('/api/local-sync/status')
    def status():return {'data':repo.engine().local.status()}

    class Resolution(BaseModel):
        inspection_id:str=Field(pattern='^[a-f0-9]{32}$')
        choice:str=Field(pattern='^(cloud|retry_local)$')

    @app.post('/api/local-sync/resolve')
    def resolve(body:Resolution):return {'data':repo.engine().resolve(body.inspection_id,body.choice)}

    @app.get('/api/local-sync/backups/{identifier}')
    def recovery_backup(identifier:str):
        import json,uuid
        try:uuid.UUID(identifier)
        except ValueError:raise HTTPException(422,'Invalid backup ID') from None
        with repo.engine().local.connect() as db:row=db.execute('SELECT snapshot FROM sync_conflict_backups WHERE id=?',(identifier,)).fetchone()
        if not row:raise HTTPException(404,'Owned recovery backup unavailable')
        return {'data':json.loads(row[0])}

    @app.get('/api/local-sync/importable')
    def importable():
        repo.engine()  # Fresh account/MFA gate, never a guest history export.
        return {'data':[{'id':row['id'],'category':row['category'],'created_at':row['created_at']} for row in repo.legacy.list(limit=500)]}

    class ImportLegacy(BaseModel):
        ids:list[str]=Field(min_length=1,max_length=10)
        confirmation:str=Field(pattern='^IMPORT_PRIVATE$')

    @app.post('/api/local-sync/import')
    def import_legacy(body:ImportLegacy):
        if any(not re.fullmatch('[a-f0-9]{32}',value) for value in body.ids):raise HTTPException(422,'Invalid inspection ID')
        return {'data':repo.import_legacy(body.ids)}
