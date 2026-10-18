from contextlib import asynccontextmanager
from io import BytesIO, StringIO
from pathlib import Path
import csv
import html
import json
import logging
import re
import uuid
import warnings
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError
from .config import Settings, CATEGORIES
from .storage import SQLiteRepository, now
from .vision import Detector, ModelUnavailable, create_detector
from .rag import KnowledgeIndex, EvidenceWorkflow

log=logging.getLogger('defectrag')

def create_app(settings=None, detector=None, workflow=None, repository=None):
    settings=settings or Settings()
    settings.data.mkdir(parents=True,exist_ok=True)
    artifacts=settings.data/'artifacts'; artifacts.mkdir(exist_ok=True)
    repo=repository if repository is not None else SQLiteRepository(settings.data/'inspection.sqlite3')
    detector=detector or create_detector(settings)
    if workflow is None:
        workflow=EvidenceWorkflow(settings,KnowledgeIndex(settings.root,settings.data/'index'))
    app=FastAPI(title='DefectRAG',version='2.1.0',description='Industrial inspection and evidence workspace')
    app.state.repo=repo; app.state.detector=detector; app.state.workflow=workflow
    import os
    origins=[o.strip() for o in os.getenv('DEFECTRAG_CORS','http://localhost:5173,http://127.0.0.1:5173').split(',')]
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

    @app.middleware('http')
    async def body_limit(request:Request,call_next):
        length=request.headers.get('content-length')
        try:
            if length and int(length)>22*1024*1024:
                return JSONResponse(status_code=413,content={'error':{'code':'upload_too_large','message':'Total request limit is 22 MB.'}})
        except ValueError:
            return JSONResponse(status_code=400,content={'error':{'code':'invalid_length','message':'Invalid content length'}})
        # Bound streamed/chunked bodies too, before multipart parsing can spool them.
        if request.method=='POST':
            received=0
            chunks=[]
            async for chunk in request.stream():
                received+=len(chunk)
                if received>22*1024*1024:
                    return JSONResponse(status_code=413,content={'error':{'code':'upload_too_large','message':'Total request limit is 22 MB.'}})
                chunks.append(chunk)
            request._body=b''.join(chunks)
        return await call_next(request)

    @app.exception_handler(HTTPException)
    async def http_error(request,exc):
        return JSONResponse(status_code=exc.status_code,content={'error':{'code':str(exc.status_code),'message':str(exc.detail)}})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        return JSONResponse(status_code=422,content={'error':{'code':'validation','message':'Invalid request fields','fields':[{'field':'.'.join(map(str,e['loc'])),'message':e['msg']} for e in exc.errors()]}})

    def require(identifier):
        record=repo.get(identifier)
        if not record: raise HTTPException(404,'Inspection not found')
        return record

    def inspect_bytes(content,category,batch,filename):
        if category not in CATEGORIES: raise HTTPException(422,'Choose a supported VisA product category')
        if len(batch)>80: raise HTTPException(422,'Batch label is limited to 80 characters')
        if len(content)>settings.max_upload: raise HTTPException(413,'Image limit is 10 MB')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(BytesIO(content)) as opened:
                    if opened.format not in ('JPEG','PNG','WEBP'): raise ValueError('Use JPEG, PNG or WebP')
                    if opened.width*opened.height>settings.max_pixels: raise ValueError('Image limit is 25 megapixels')
                    if opened.width<32 or opened.height<32: raise ValueError('Image must be at least 32 pixels on each side')
                    image=ImageOps.exif_transpose(opened).convert('RGB')
                    image.load()
        except (ValueError,UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
            raise HTTPException(422,'Invalid image: '+str(exc))
        try:
            result,heatmap=detector.predict(image,category)
        except ModelUnavailable as exc:
            repo.failure(category,'model_unavailable')
            raise HTTPException(503,str(exc))
        except Exception:
            log.exception('Model inference failed')
            repo.failure(category,'inference_failed')
            raise HTTPException(503,'Model execution failed. No inspection was saved.')
        identifier=uuid.uuid4().hex
        image_path=artifacts/f'{identifier}.jpg'; heatmap_path=artifacts/f'{identifier}_heatmap.jpg'
        try:
            image.thumbnail((1600,1600)); image.save(image_path,quality=92)
            heatmap.save(heatmap_path,quality=92)
            record={**result,'id':identifier,'created_at':now(),'batch':batch.strip(),'filename':Path(filename).name[:160],
                    'image_url':f'/api/inspections/{identifier}/image','heatmap_url':f'/api/inspections/{identifier}/heatmap'}
            return repo.save(record)
        except Exception:
            image_path.unlink(missing_ok=True); heatmap_path.unlink(missing_ok=True)
            raise

    @app.get('/api/health')
    def health():
        return {'data':{'status':'ok','version':'2.1.0','mode':'local_single_user','models':detector.cards(),
                        'encoder_configured':Path(settings.encoder).exists(),'llm_model':settings.ollama_model}}
    @app.get('/api/models')
    def models(): return {'data':detector.cards()}
    @app.get('/api/evaluation')
    def evaluation():
        active=getattr(detector,'profile_name','legacy')=='dinov2_highres_v1'
        path=settings.root/'results'/('highres_deployment_evaluation.json' if active else 'evaluation.json')
        result=json.loads(path.read_text()) if path.exists() else {'status':'unverified'}
        if active and 'categories' in result:
            from .calibration import active_evaluation
            result=active_evaluation(settings.root,result)
        profile=settings.root/'results'/'serving_profile.json'
        if profile.exists() and not active:result['serving_profile']=json.loads(profile.read_text())
        return {'data':result}
    @app.get('/api/stats')
    def stats(): return {'data':repo.stats()}
    @app.get('/api/samples')
    def samples():
        return {'data':[{'name':p.stem,'category':p.stem.rsplit('_',1)[0],'url':'/api/samples/'+p.name,
                         'attribution':'VisA, Zou et al., ECCV 2022; CC BY 4.0; resized preview','source':'https://github.com/amazon-science/spot-diff'} for p in sorted((settings.root/'samples').glob('*.jpg'))]}
    @app.get('/api/samples/{name}')
    def sample(name:str):
        if name not in {f'{category}_{kind}.jpg' for category in CATEGORIES for kind in ('good','anomalous')}: raise HTTPException(404,'Sample not found')
        path=settings.root/'samples'/name
        if not path.exists(): raise HTTPException(404,'Sample not available')
        return FileResponse(path)
    @app.post('/api/inspect')
    def inspect(category:str=Form(...),batch:str=Form(''),file:UploadFile=File(...)):
        try:
            content=file.file.read(settings.max_upload+1)
            return {'data':inspect_bytes(content,category,batch,file.filename or 'upload')}
        finally: file.file.close()
    @app.post('/api/batch')
    def inspect_batch(category:str=Form(...),batch:str=Form(...),files:list[UploadFile]=File(...)):
        if not 1<=len(files)<=20: raise HTTPException(422,'Upload 1–20 files per batch')
        if category not in CATEGORIES or not batch.strip() or len(batch)>80: raise HTTPException(422,'Choose a valid category and batch label of 1–80 characters')
        records,errors=[],[]
        for file in files:
            try:
                records.append(inspect_bytes(file.file.read(settings.max_upload+1),category,batch,file.filename or 'upload'))
            except HTTPException as exc:
                errors.append({'filename':file.filename,'message':str(exc.detail),'status':exc.status_code})
            finally: file.file.close()
        return {'data':{'records':records,'errors':errors,'batch':batch}}
    @app.get('/api/inspections')
    def inspections(category:str='',verdict:str='',batch:str='',limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
        return {'data':repo.list(category,verdict,batch,limit,offset)}
    class ArchiveRequest(BaseModel):
        confirmation:str=Field(pattern='^ARCHIVE$')
        category:str=Field(default='',max_length=40)
        verdict:str=Field(default='',max_length=20)
        batch:str=Field(default='',max_length=80)
    @app.post('/api/history/archive')
    def archive_history(payload:ArchiveRequest):
        return {'data':repo.archive(payload.category,payload.verdict,payload.batch)}
    @app.get('/api/archives')
    def archived_inspections():
        return {'data':repo.list(limit=500,archived=True)}
    class RestoreRequest(BaseModel):
        ids:list[str]=Field(min_length=1,max_length=500)
    @app.post('/api/history/restore')
    def restore_history(payload:RestoreRequest):
        if not all(re.fullmatch('[a-f0-9]{32}',i) for i in payload.ids):raise HTTPException(422,'Invalid inspection IDs')
        return {'data':repo.restore(payload.ids)}
    @app.get('/api/benchmark/official')
    def official_benchmark():
        path=settings.root/'results/official_evaluation.json'
        progress=settings.root/'experiments/official_visa_v1/evaluation.json'
        source=path if path.exists() else progress
        report=json.loads(source.read_text()) if source.exists() else {'categories':{},'status':'not_run'}
        candidate=settings.root/'results/highres_evaluation.json'
        candidate_progress=settings.root/'experiments/dinov2_highres_v1/evaluation.json'
        candidate_source=candidate if candidate.exists() else candidate_progress
        if candidate_source.exists():report['candidate']=json.loads(candidate_source.read_text())
        return {'data':report}
    @app.get('/api/inspections/{identifier}')
    def inspection(identifier:str): return {'data':require(identifier)}
    @app.get('/api/inspections/{identifier}/image')
    def inspection_image(identifier:str):
        require(identifier); return FileResponse(artifacts/f'{identifier}.jpg')
    @app.get('/api/inspections/{identifier}/heatmap')
    def inspection_heatmap(identifier:str):
        require(identifier); return FileResponse(artifacts/f'{identifier}_heatmap.jpg')
    @app.get('/api/inspections/{identifier}/report')
    def report(identifier:str):
        record=require(identifier)
        esc=lambda v:html.escape(str(v))
        rows=''.join(f'<tr><th>{esc(k.replace("_"," "))}</th><td>{esc(v)}</td></tr>' for k,v in record.items() if not isinstance(v,(dict,list)))
        messages=repo.messages(identifier)
        evidence=''.join(f'<p>{esc(m.get("answer",m.get("question","")))}</p>' for m in messages) or '<p>No saved conversation yet. Ask the Evidence Assistant a question for this inspection, then refresh this report.</p>'
        sources={s['chunk_id']:s for m in messages for s in m.get('evidence',[])}
        source_html=''.join('<article><h3>'+esc(k)+' · '+esc(s['title'])+'</h3><p>'+esc(s['text'])+'</p><p>'+esc(s['url'])+' · '+esc(s['scope'])+'</p></article>' for k,s in sources.items()) or '<p>No document passages saved. Measurement-only answers come directly from the saved inspection and do not require a document citation.</p>'
        return HTMLResponse('<!doctype html><html lang="en"><meta charset="utf-8"><title>DefectRAG inspection report</title><style>body{font:15px system-ui;max-width:900px;margin:40px auto;color:#17292c}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #ddd;padding:8px}img{width:46%}article{border-top:1px solid #ddd}@media print{button{display:none}}</style><h1>DefectRAG inspection report</h1><p>Benchmark screening evidence · model score is not a probability</p><button onclick="window.print()">Print / save PDF</button><table>'+rows+'</table><h2>Image and localization</h2><img src="'+record['image_url']+'"><img src="'+record['heatmap_url']+'"><h2>Evidence conversation</h2>'+evidence+'<h2>Retrieved documentation</h2>'+source_html+'</html>')
    class Question(BaseModel):
        inspection_id:str=Field(min_length=32,max_length=32,pattern='^[0-9a-f]{32}$')
        question:str=Field(min_length=3,max_length=1200)
    @app.post('/api/assistant')
    def assistant(payload:Question):
        record=require(payload.inspection_id)
        history=repo.messages(payload.inspection_id)
        # Save user and assistant turns together only after workflow completion.
        answer=workflow.run(payload.question,record,[{'role':m['role'],'text':m.get('question',m.get('answer','')),
            'knowledge_fingerprint':m.get('knowledge_fingerprint')} for m in history])
        repo.add_conversation(payload.inspection_id,payload.question,answer)
        return {'data':{**answer,'observation':{k:record[k] for k in ('id','category','verdict','score','threshold')}}}
    @app.get('/api/inspections/{identifier}/messages')
    def messages(identifier:str): require(identifier); return {'data':repo.messages(identifier)}
    class RetrievalQuestion(BaseModel):
        question:str=Field(min_length=3,max_length=1200)
    @app.post('/api/retrieve')
    def retrieve(payload:RetrievalQuestion):
        try:
            docs=workflow.index.retriever.invoke(payload.question)
            return {'data':[{'text':d.page_content,**d.metadata} for d in docs]}
        except Exception: raise HTTPException(503,'Local knowledge index is unavailable')
    @app.get('/api/alerts')
    def alerts(): return {'data':repo.alerts()}
    @app.post('/api/alerts/{identifier}/acknowledge')
    def acknowledge(identifier:str):
        if not repo.acknowledge(identifier): raise HTTPException(404,'Alert not found')
        return {'data':{'acknowledged':True}}
    @app.get('/api/export.csv')
    def export():
        output=StringIO(); fields=['id','created_at','category','batch','verdict','score','threshold','inference_ms','model_id']
        writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore'); writer.writeheader()
        for record in repo.list(limit=10000):
            safe={k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in record.items()}
            writer.writerow(safe)
        return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="defectrag-inspections.csv"'})
    dist=settings.root/'frontend'/'dist'
    if dist.exists(): app.mount('/',StaticFiles(directory=dist,html=True),name='dashboard')
    return app

import os
app=create_app() if os.getenv('DEFECTRAG_FACTORY_ONLY')!='1' else None
