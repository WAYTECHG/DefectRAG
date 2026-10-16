"""Frozen DINOv3 patch features + normal-only fitted nearest-neighbour banks.

This is a compact fallback detector, NOT Dinomaly and NOT a defect classifier.
"""
from pathlib import Path
import hashlib
import json
import time
import threading
import numpy as np
from PIL import Image, ImageFilter
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoImageProcessor
from .config import CATEGORIES

class ModelUnavailable(RuntimeError):
    pass

def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

class Encoder:
    def __init__(self, source, device='auto'):
        self.device = torch.device(('cuda' if torch.cuda.is_available() else 'cpu') if device == 'auto' else device)
        torch.set_num_threads(min(4, torch.get_num_threads()))
        self.processor = AutoImageProcessor.from_pretrained(str(source), local_files_only=True)
        self.model = AutoModel.from_pretrained(str(source), local_files_only=True).eval().to(self.device)
        self.model.requires_grad_(False)
        if self.device.type == 'cuda':
            self.model.half()
        self.dtype = next(self.model.parameters()).dtype

    @torch.inference_mode()
    def patches(self, image):
        inputs = self.processor(images=image.convert('RGB'), return_tensors='pt')
        inputs = {k: v.to(self.device, dtype=self.dtype) if v.is_floating_point() else v.to(self.device) for k,v in inputs.items()}
        output = self.model(**inputs).last_hidden_state
        skip = 1 + self.model.config.num_register_tokens
        patches = F.normalize(output[:, skip:].float(), dim=-1)[0]
        side = int(patches.shape[0] ** 0.5)
        if side * side != patches.shape[0]:
            raise ModelUnavailable('Encoder returned a non-square spatial grid')
        return patches, side

def distances(patches, bank):
    # Chunk bank to keep peak allocations bounded on CPU and GPU.
    best = torch.full((len(patches),), -1.0, device=patches.device)
    for chunk in bank.split(2048):
        best = torch.maximum(best, (patches @ chunk.T).amax(dim=1))
    return (1 - best).clamp_min(0)

def map_and_score(encoder, bank, image):
    patches, side = encoder.patches(image)
    raw = distances(patches, bank).reshape(side, side).cpu().numpy()
    # Fixed before validation: mean of top 1% spatial patch distances.
    score = float(np.sort(raw.ravel())[-max(1, int(np.ceil(raw.size * .01))):].mean())
    return raw, score

def display_map(raw, image, scale):
    intensity = Image.fromarray(np.clip(raw / max(scale, 1e-8) * 255, 0, 255).astype('uint8'))
    intensity = intensity.resize(image.size, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(max(image.size) / 160))
    t = np.asarray(intensity).astype('float32') / 255
    colors = np.stack([np.clip(2*t, 0, 1), np.clip(2-abs(4*t-2), 0, 1), np.clip(2-2*t, 0, 1)], axis=-1)
    base = np.asarray(image.convert('RGB')).astype('float32') / 255
    overlay = (base * .60 + colors * .40) * 255
    return Image.fromarray(overlay.astype('uint8'))

class Detector:
    def __init__(self, settings):
        self.settings = settings
        self.encoder = None
        self.banks = {}
        self.lock = threading.Lock()

    def cards(self):
        cards = []
        for category in CATEGORIES:
            path = self.settings.root / 'models' / f'{category}.json'
            cards.append(json.loads(path.read_text()) if path.exists() else {'category': category, 'available': False})
        return cards

    def load(self, category):
        if category not in CATEGORIES:
            raise ValueError('Unsupported product category')
        card_path = self.settings.root / 'models' / f'{category}.json'
        bank_path = self.settings.root / 'models' / f'{category}.npz'
        if not card_path.exists() or not bank_path.exists():
            raise ModelUnavailable('No calibrated model for this category. Run the training pipeline first.')
        card = json.loads(card_path.read_text())
        if self.encoder is None:
            try:
                self.encoder = Encoder(self.settings.encoder, self.settings.device)
            except Exception as exc:
                raise ModelUnavailable('DINOv3 encoder could not load. Configure DEFECTRAG_ENCODER with an authorized local checkpoint.') from exc
            source = Path(self.settings.encoder)
            if not source.is_dir():
                from huggingface_hub import snapshot_download
                source = Path(snapshot_download(self.settings.encoder, local_files_only=True))
            fingerprint = sha256(source / 'model.safetensors')
            if fingerprint != card['encoder_sha256']:
                self.encoder = None
                raise ModelUnavailable('Encoder checksum differs from the calibrated model')
        if category not in self.banks:
            if sha256(bank_path) != card['bank_sha256']:
                raise ModelUnavailable('Normal memory bank checksum mismatch')
            bank = np.load(bank_path, allow_pickle=False)['patches'].astype('float32')
            self.banks[category] = F.normalize(torch.from_numpy(bank).to(self.encoder.device), dim=-1)
        return card, self.banks[category]

    def predict(self, image, category):
        with self.lock:
            start = time.perf_counter()
            card, bank = self.load(category)
            if self.encoder.device.type == 'cuda':
                torch.cuda.reset_peak_memory_stats()
            inference_start = time.perf_counter()
            raw, score = map_and_score(self.encoder, bank, image)
            if self.encoder.device.type == 'cuda':
                torch.cuda.synchronize()
            elapsed = (time.perf_counter() - inference_start) * 1000
            threshold, margin = card['threshold'], card['uncertainty_margin']
            verdict = 'Uncertain' if abs(score-threshold) <= margin else ('Anomalous' if score >= threshold else 'Good')
            result = {'category': category, 'verdict': verdict, 'score': score, 'threshold': threshold,
                      'uncertainty_margin': margin, 'defect_category': None, 'model_id': card['model_id'],
                      'inference_ms': round(elapsed, 2), 'total_model_ms': round((time.perf_counter()-start)*1000, 2),
                      'peak_gpu_mb': round(torch.cuda.max_memory_allocated()/1024**2, 2) if self.encoder.device.type == 'cuda' else None,
                      'device': str(self.encoder.device), 'localization': '14 x 14 patch distances, interpolated; not a defect segmentation classifier',
                      'scope': 'VisA benchmark appearance anomaly screening; category is user-selected and not verified by this model.',
                      'calibration': card['calibration'], 'model_sha256': card['bank_sha256']}
            preview = image.copy()
            preview.thumbnail((1000,1000))
            return result, display_map(raw, preview, card['heatmap_scale'])

