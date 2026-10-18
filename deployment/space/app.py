"""Incremental Gradio/ZeroGPU host for the existing DefectRAG React dashboard."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.getenv('DEFECTRAG_SPACE_RUNTIME', ROOT/'runtime/space-development'))
os.environ['DEFECTRAG_DATA'] = str(RUNTIME)
os.environ['DEFECTRAG_FACTORY_ONLY'] = '1'
os.environ['USE_TF'] = '0'
import spaces
import base64
from io import BytesIO
import importlib.metadata
import json
import platform
import re
import time
import uuid
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import torch
import torch.nn.functional as F
from gradio import Server
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from backend.config import CATEGORIES, Settings
from backend.highres import HighResolutionEncoder, foreground_mask, score_tokens, restore_map
from backend.vision import sha256, display_map
from backend.storage import now
from deployment.space.sessions import SessionRepository, identity, namespace, NAMESPACE, STAFF_TOKEN, authorize_artifact, capability, remember_staff, stored_staff

ZERO = os.getenv('SPACES_ZERO_GPU') == '1'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
CARDS = {category: json.loads((ROOT/f'models/highres/{category}.json').read_text()) for category in CATEGORIES}
ENCODER = HighResolutionEncoder(ROOT/'models/encoder_dinov2', device='cpu')
encoder_digest = sha256(ROOT/'models/encoder_dinov2/model.safetensors')
assert all(card['encoder_sha256'] == encoder_digest for card in CARDS.values())
if DEVICE == 'cuda':
    ENCODER.model.half().to('cuda')
    ENCODER.device = torch.device('cuda')
    ENCODER.dtype = torch.float16
    ENCODER.mean = ENCODER.mean.half().to('cuda')
    ENCODER.std = ENCODER.std.half().to('cuda')
BANKS = {}
for category, card in CARDS.items():
    file = ROOT/f'models/highres/{category}.npz'
    assert sha256(file) == card['bank_sha256'], f'Invalid bank checksum: {category}'
    with np.load(file, allow_pickle=False) as saved:
        BANKS[category] = F.normalize(torch.from_numpy(saved['patches'].astype('float32')), dim=-1).to(DEVICE)


@spaces.GPU(duration=20)
@torch.inference_mode()
def compute(rgb: np.ndarray, category: str) -> dict:
    start = time.perf_counter()
    if DEVICE == 'cuda':
        torch.cuda.reset_peak_memory_stats()
    tokens, geometry = ENCODER.encode(Image.fromarray(rgb))
    mask = foreground_mask(tokens, geometry['grid'])
    raw, score = score_tokens(tokens, BANKS[category], mask)
    if DEVICE == 'cuda':
        torch.cuda.synchronize()
    return {'raw': raw, 'geometry': geometry, 'score': score,
            'foreground_fraction': float(mask.mean()), 'device': DEVICE,
            'gpu_name': torch.cuda.get_device_name() if DEVICE == 'cuda' else None,
            'peak_gpu_mb': round(torch.cuda.max_memory_allocated()/1024**2, 2) if DEVICE == 'cuda' else None,
            'inference_ms': round((time.perf_counter()-start)*1000, 2)}


class MetadataDetector:
    profile_name = 'dinov2_highres_v1'
    def cards(self):
        return list(CARDS.values())


ARTIFACTS = RUNTIME/'artifacts'
ARTIFACTS.mkdir(parents=True, exist_ok=True)
UI = Path(os.getenv('DEFECTRAG_SPACE_UI', ROOT/'development-support/space/ui-dist'))
CLOUD_CONFIG=None
if os.getenv('DEFECTRAG_STAFF_BACKEND')=='1':
    from deployment.space.supabase_repository import read_public_config
    CLOUD_CONFIG=read_public_config(UI/'config.js')
REPO = SessionRepository(RUNTIME/'sessions',cloud_config=CLOUD_CONFIG,artifacts=ARTIFACTS)
from backend.main import create_app
from backend.rag import KnowledgeIndex, EvidenceWorkflow
if os.getenv('DEFECTRAG_LIVE_RAG')=='1':
    from deployment.space.generation import CpuBGE, generate_text
    INDEX=KnowledgeIndex(ROOT,RUNTIME/'index',embeddings_factory=CpuBGE)
    # Retrieval initializes on its first CPU request, not during the ZeroGPU
    # fork snapshot. Eager CPU attention avoids CUDA/SDPA capability probing.
    WORKFLOW=EvidenceWorkflow(Settings(),INDEX,generator=generate_text if ZERO else None)
else:
    WORKFLOW=None
cpu_app = create_app(Settings(), detector=MetadataDetector(), repository=REPO,workflow=WORKFLOW)
server = Server(title='DefectRAG')


@server.middleware('http')
async def workspace_access(request, call_next):
    path = request.url.path
    public = path in ('/api/health', '/api/models', '/api/evaluation', '/api/benchmark/official', '/api/samples') or path.startswith('/api/samples/')
    if not path.startswith('/api/') or public:
        return await call_next(request)
    try:
        match = re.fullmatch(r'/api/inspections/([a-f0-9]{32})/(image|heatmap|report)', path)
        if match and 'access' in request.query_params:
            owner = authorize_artifact(request.query_params['access'], *match.groups())
        elif path == '/api/export.csv' and 'access' in request.query_params:
            owner = authorize_artifact(request.query_params['access'],'workspace','csv')
        else:
            owner = namespace(request.headers.get('X-DefectRAG-Session',''))
        context = NAMESPACE.set(owner)
        bearer=request.headers.get('authorization','').removeprefix('Bearer ')
        if request.headers.get('X-DefectRAG-Session'):
            remember_staff(owner,bearer)
        token = STAFF_TOKEN.set(bearer or stored_staff(owner))
    except ValueError as exc:
        return JSONResponse({'error': {'message': str(exc)}}, status_code=401)
    try:
        response = await call_next(request)
        response.headers['X-DefectRAG-Export'] = '/api/export.csv?access='+capability('workspace','csv')
        response.headers['Cache-Control'] = 'private, no-store'
        return response
    finally:
        STAFF_TOKEN.reset(token)
        NAMESPACE.reset(context)


@server.api(name='ready', concurrency_limit=1)
def ready(message: str) -> dict:
    return {'message': message, 'zero_gpu_environment': ZERO, 'python': platform.python_version(),
            'device': DEVICE, 'categories': list(CARDS), 'versions': {name: importlib.metadata.version(name)
             for name in ('gradio','spaces','torch','transformers','huggingface-hub')}}


def inspect_one(image_b64, filename, category, batch):
    if category not in CARDS or len(batch)>80 or len(image_b64)>14*1024*1024:
        raise ValueError('Choose a supported category, image up to 10 MB and batch label up to 80 characters.')
    try:
        content = base64.b64decode(image_b64, validate=True)
        if len(content)>10*1024*1024:
            raise ValueError('Image limit is 10 MB')
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as opened:
                if opened.format not in ('JPEG','PNG','WEBP') or opened.width*opened.height>25_000_000 or min(opened.size)<32 or max(opened.size)>4*min(opened.size):
                    raise ValueError('Use JPEG, PNG or WebP, 32px minimum, up to 25 MP and 4:1 aspect ratio.')
                image = ImageOps.exif_transpose(opened).convert('RGB')
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError(f'Invalid image: {exc}') from None
    start = time.perf_counter()
    output = compute(np.asarray(image), category)
    card = CARDS[category]
    threshold, margin, score = card['threshold'], card['uncertainty_margin'], output['score']
    verdict = 'Uncertain' if abs(score-threshold)<=margin else 'Anomalous' if score>=threshold else 'Good'
    identifier = uuid.uuid4().hex
    preview = image.copy()
    preview.thumbnail((1000,1000))
    heatmap = display_map(restore_map(output['raw'],output['geometry'],preview.size),preview,card['heatmap_scale'])
    image.thumbnail((1600,1600))
    image.save(ARTIFACTS/f'{identifier}.jpg', quality=92)
    heatmap.save(ARTIFACTS/f'{identifier}_heatmap.jpg', quality=92)
    record = {key:output[key] for key in ('inference_ms','device','gpu_name','peak_gpu_mb','foreground_fraction')}
    record.update(id=identifier,created_at=now(),category=category,batch=batch.strip(),filename=Path(filename).name[:160],
        verdict=verdict,score=score,threshold=threshold,uncertainty_margin=margin,defect_category=None,
        model_id=card['model_id'],model_sha256=card['bank_sha256'],profile='dinov2_highres_v1',calibration=card['calibration'],
        total_model_ms=round((time.perf_counter()-start)*1000,2),
        localization=f"{output['geometry']['grid'][0]} x {output['geometry']['grid'][1]} DINOv2 patch distances with PCA foreground heuristic; interpolated, not supervised segmentation",
        scope='VisA appearance anomaly screening; operator-selected category is not verified; foreground heuristic can fail.',
        deployment={'transport':'@gradio/client','zero_gpu_environment':ZERO},
        image_url=f'/api/inspections/{identifier}/image',heatmap_url=f'/api/inspections/{identifier}/heatmap')
    return REPO.save(record)


@server.api(name='inspect',concurrency_limit=1,concurrency_id='model-work')
def inspect(image_b64: str, filename: str, category: str, batch: str, session: str, token: str='') -> dict:
    with identity(session,token):
        REPO.current()  # Validate signed-in staff membership before consuming GPU.
        return inspect_one(image_b64,filename,category,batch)


@server.api(name='assistant',concurrency_limit=1,concurrency_id='model-work')
def assistant(inspection_id: str, question: str, session: str, token: str='') -> dict:
    if not 3<=len(question)<=1200 or not re.fullmatch('[a-f0-9]{32}',inspection_id):
        raise ValueError('Use a saved inspection and a question of 3–1200 characters.')
    if WORKFLOW is None:
        raise ValueError('Live evidence generation is not enabled in this deployment yet.')
    with identity(session,token):
        record=REPO.get(inspection_id)
        if record is None:
            raise ValueError('Inspection is unavailable in your workspace')
        history=[{'role':row['role'],'text':row.get('question',row.get('answer','')),
                  'knowledge_fingerprint':row.get('knowledge_fingerprint')} for row in REPO.messages(inspection_id)]
        answer=WORKFLOW.run(question,record,history)
        REPO.add_conversation(inspection_id,question,answer)
        return {**answer,'observation':{key:record[key] for key in ('id','category','verdict','score','threshold')}}


@server.get('/api/health')
def health():
    return {'data':{'status':'ok','mode':'cloud_session_workspace','models':list(CARDS.values()),
        'encoder_configured':True,'llm_model':'Qwen3-4B-Instruct-2507' if WORKFLOW and ZERO else 'Qwen2.5:3b (local Ollama)' if WORKFLOW else 'generation migration in progress','zero_gpu':ZERO,
        'history':'anonymous browser history is temporary; staff workspace uses Supabase'}}


def artifact(identifier: str,kind: str):
    record=REPO.get(identifier)
    if record is None:
        raise HTTPException(404,'Inspection not found')
    if record.get('storage')=='supabase':
        return RedirectResponse(record[kind+'_url'],status_code=307)
    return FileResponse(ARTIFACTS/f"{identifier}{'_heatmap' if kind=='heatmap' else ''}.jpg")


@server.get('/api/inspections/{identifier}/image')
def original_image(identifier: str):
    return artifact(identifier,'image')


@server.get('/api/inspections/{identifier}/heatmap')
def heatmap_image(identifier: str):
    return artifact(identifier,'heatmap')


for route in cpu_app.routes:
    path = getattr(route,'path','')
    if path.startswith('/api/') and path not in {'/api/health','/api/inspect','/api/batch','/api/assistant'}:
        server.router.routes.append(route)


@server.post('/api/{operation}')
def queued_only(operation: str):
    raise HTTPException(409,'Use the dashboard Gradio queue for model execution.')


@server.get('/')
def dashboard():
    return FileResponse(UI/'index.html')
@server.get('/config.js')
def public_config():
    return FileResponse(UI/'config.js')
@server.get('/logo.svg')
def logo():
    return FileResponse(UI/'logo.svg')
server.mount('/assets',StaticFiles(directory=UI/'assets'),name='react-assets')

if __name__ == '__main__':
    server.launch(server_name='0.0.0.0',server_port=int(os.getenv('PORT','8784')),show_error=True,ssr_mode=False,run_history=False)
