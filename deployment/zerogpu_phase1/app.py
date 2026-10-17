"""Isolated Phase 1 proof: existing React, Gradio Server, real frozen DINOv2.

Only the public PCB1 fixture is accepted. No production history, RAG migration,
Supabase writes, training, or arbitrary public uploads are enabled here.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.environ.get('DEFECTRAG_PHASE1_RUNTIME', ROOT / 'runtime/zerogpu-phase1'))
os.environ['DEFECTRAG_DATA'] = str(RUNTIME)
os.environ['USE_TF'] = '0'

import spaces  # must precede torch initialization on ZeroGPU
import base64
from io import BytesIO
import json
import platform
import time
import uuid
import warnings
import importlib.metadata
import numpy as np
from PIL import Image, ImageOps
import torch
import torch.nn.functional as F
from gradio import Server
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from backend.highres import HighResolutionEncoder, foreground_mask, score_tokens, restore_map
from backend.vision import sha256, display_map

ZERO = os.environ.get('SPACES_ZERO_GPU') == '1'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
CARD = json.loads((ROOT / 'models/highres/pcb1.json').read_text())
MODEL_SOURCE = ROOT / 'models/encoder_dinov2'
assert sha256(MODEL_SOURCE / 'model.safetensors') == CARD['encoder_sha256']
assert sha256(ROOT / 'models/highres/pcb1.npz') == CARD['bank_sha256']

# Register immutable resources eagerly; perform normalization on CPU only.
ENCODER = HighResolutionEncoder(MODEL_SOURCE, device='cpu')
if DEVICE == 'cuda':
    ENCODER.model.half().to('cuda')
    ENCODER.device = torch.device('cuda')
    ENCODER.dtype = torch.float16
    ENCODER.mean = ENCODER.mean.half().to('cuda')
    ENCODER.std = ENCODER.std.half().to('cuda')
with np.load(ROOT / 'models/highres/pcb1.npz', allow_pickle=False) as saved:
    BANK = F.normalize(torch.from_numpy(saved['patches'].astype('float32')), dim=-1).to(DEVICE)


@spaces.GPU(duration=30)
@torch.inference_mode()
def compute(rgb: np.ndarray) -> dict:
    started = time.perf_counter()
    if DEVICE == 'cuda':
        torch.cuda.reset_peak_memory_stats()
    image = Image.fromarray(rgb)
    tokens, geometry = ENCODER.encode(image)
    mask = foreground_mask(tokens, geometry['grid'])
    raw, score = score_tokens(tokens, BANK, mask)
    if DEVICE == 'cuda':
        torch.cuda.synchronize()
    return {'raw': raw, 'geometry': geometry, 'score': score,
            'inference_ms': round((time.perf_counter() - started) * 1000, 2),
            'device': DEVICE, 'gpu_name': torch.cuda.get_device_name() if DEVICE == 'cuda' else None,
            'peak_gpu_mb': round(torch.cuda.max_memory_allocated() / 1024**2, 2) if DEVICE == 'cuda' else None,
            'foreground_fraction': float(mask.mean())}


# CPU routes reuse the original app in an isolated SQLite workspace. The minimal
# Space contains an explicit empty embedding directory; generation is disabled.
from backend.main import app as cpu_app
REPO = cpu_app.state.repo
ARTIFACTS = RUNTIME / 'artifacts'
ARTIFACTS.mkdir(parents=True, exist_ok=True)
server = Server(title='DefectRAG Phase 1 compatibility')


@server.api(name='phase1_ready', concurrency_limit=1)
def phase1_ready(message: str) -> dict:
    return {'message': message, 'server_mode': True, 'zero_gpu_environment': ZERO,
            'python': platform.python_version(), 'device': DEVICE,
            'versions': {name: importlib.metadata.version(name) for name in
                         ('gradio', 'spaces', 'torch', 'transformers', 'huggingface-hub', 'fastapi')}}


@server.api(name='inspect', concurrency_limit=1, concurrency_id='phase1-gpu')
def inspect(image_b64: str, filename: str, category: str, batch: str) -> dict:
    if category != 'pcb1' or len(batch) > 80 or len(image_b64) > 14 * 1024 * 1024:
        raise ValueError('Phase 1 accepts one PCB1 fixture and a batch label up to 80 characters.')
    content = base64.b64decode(image_b64, validate=True)
    import hashlib
    expected = (ROOT / 'samples/pcb1_anomalous.jpg').read_bytes()
    if hashlib.sha256(content).digest() != hashlib.sha256(expected).digest():
        raise ValueError('Compatibility test only: upload the supplied pcb1_anomalous.jpg public fixture. The working local app still accepts normal uploads.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(content)) as opened:
            if opened.width * opened.height > 25_000_000 or min(opened.size) < 32 or max(opened.size) > 4 * min(opened.size):
                raise ValueError('Image geometry exceeds the bounded Phase 1 workload.')
            image = ImageOps.exif_transpose(opened).convert('RGB')
    start = time.perf_counter()
    output = compute(np.asarray(image))
    score = output['score']
    threshold, margin = CARD['threshold'], CARD['uncertainty_margin']
    verdict = 'Uncertain' if abs(score - threshold) <= margin else 'Anomalous' if score >= threshold else 'Good'
    identifier = uuid.uuid4().hex
    preview = image.copy()
    preview.thumbnail((1000, 1000))
    heatmap = display_map(restore_map(output['raw'], output['geometry'], preview.size), preview, CARD['heatmap_scale'])
    image.thumbnail((1600, 1600))
    image.save(ARTIFACTS / f'{identifier}.jpg', quality=92)
    heatmap.save(ARTIFACTS / f'{identifier}_heatmap.jpg', quality=92)
    from backend.storage import now
    record = {key: output[key] for key in ('inference_ms', 'device', 'gpu_name', 'peak_gpu_mb', 'foreground_fraction')}
    record.update({'id': identifier, 'created_at': now(), 'category': category, 'batch': batch,
        'filename': Path(filename).name[:160], 'verdict': verdict, 'score': score,
        'threshold': threshold, 'uncertainty_margin': margin, 'defect_category': None,
        'model_id': CARD['model_id'], 'model_sha256': CARD['bank_sha256'],
        'total_model_ms': round((time.perf_counter() - start) * 1000, 2),
        'localization': f"{output['geometry']['grid'][0]} x {output['geometry']['grid'][1]} DINOv2 patch distances with PCA foreground heuristic; interpolated, not supervised segmentation",
        'scope': 'Phase 1 compatibility request using a public VisA fixture; not a new accuracy evaluation.',
        'profile': 'dinov2_highres_v1', 'calibration': CARD['calibration'],
        'phase1': {'transport': '@gradio/client', 'zero_gpu_environment': ZERO},
        'image_url': f'/api/inspections/{identifier}/image',
        'heatmap_url': f'/api/inspections/{identifier}/heatmap'})
    REPO.save(record)
    (RUNTIME / 'last-genuine-inspection.json').write_text(json.dumps(record, indent=2))
    return record


@server.get('/api/health')
def health():
    return {'data': {'status': 'ok', 'mode': 'phase1_compatibility', 'models': cpu_app.state.detector.cards(),
                     'encoder_configured': True, 'llm_model': 'unchanged; migration excluded from Phase 1'}}


# Prevent direct REST GPU execution and generation bypassing the queued proof.
BLOCKED = {'/api/inspect', '/api/batch', '/api/assistant', '/api/retrieve'}
for route in cpu_app.routes:
    path = getattr(route, 'path', '')
    if path.startswith('/api/') and path not in BLOCKED and path != '/api/health':
        server.router.routes.append(route)


@server.post('/api/{operation}')
def disabled(operation: str):
    raise HTTPException(409, 'Phase 1 only: single inspection uses the Gradio queue; batch and RAG migration are not enabled.')


UI = Path(os.environ.get('DEFECTRAG_PHASE1_UI', ROOT / 'development-support/zerogpu-phase1/ui-dist'))


@server.get('/')
def dashboard():
    return FileResponse(UI / 'index.html')


@server.get('/config.js')
def public_config():
    configured = os.environ.get('DEFECTRAG_PHASE1_CONFIG')
    if configured and not ZERO:
        return FileResponse(configured)
    return Response("window.DEFECTRAG_PUBLIC_CONFIG={supabaseUrl:'',supabasePublishableKey:''};",
                    media_type='application/javascript')


@server.get('/logo.svg')
def logo():
    return FileResponse(UI / 'logo.svg')


server.mount('/assets', StaticFiles(directory=UI / 'assets'), name='phase1-react-assets')

if __name__ == '__main__':
    server.launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', '8783')),
                  show_error=True)
