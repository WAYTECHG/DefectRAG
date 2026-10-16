"""AnomalyDINO-inspired frozen DINOv2 profile; independent of the legacy banks.

Uses a rectangular high-resolution grid and label-free PCA foreground selection.
This is an adaptation, not an exact reproduction of the paper's implementation.
"""
import math
import json
import threading
import time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_closing
from sklearn.decomposition import PCA
import torch
import torch.nn.functional as F
from transformers import AutoModel
from .vision import distances,ModelUnavailable,sha256,display_map
from .config import CATEGORIES


class HighResolutionEncoder:
    def __init__(self,source,device='auto',resolution=448):
        self.device=torch.device(('cuda' if torch.cuda.is_available() else 'cpu') if device=='auto' else device)
        self.resolution=resolution
        torch.set_num_threads(min(4,torch.get_num_threads()))
        self.model=AutoModel.from_pretrained(str(source),local_files_only=True).eval().to(self.device)
        self.model.requires_grad_(False)
        if self.device.type=='cuda':self.model.half()
        self.dtype=next(self.model.parameters()).dtype
        self.patch_size=int(self.model.config.patch_size)
        self.mean=torch.tensor([.485,.456,.406],device=self.device,dtype=self.dtype)[:,None,None]
        self.std=torch.tensor([.229,.224,.225],device=self.device,dtype=self.dtype)[:,None,None]

    @torch.inference_mode()
    def encode(self,image):
        image=image.convert('RGB');width,height=image.size
        factor=self.resolution/min(width,height)
        resized=(int(width*factor),int(height*factor))
        cropped=tuple(v-v%self.patch_size for v in resized)
        pixels=np.array(image.resize(resized,Image.Resampling.BICUBIC).crop((0,0,*cropped)),copy=True)
        values=torch.from_numpy(pixels).permute(2,0,1).to(self.device,dtype=self.dtype)/255
        tokens=self.model(pixel_values=((values-self.mean)/self.std)[None]).last_hidden_state[0,1:].float()
        grid=(cropped[1]//self.patch_size,cropped[0]//self.patch_size)
        if len(tokens)!=grid[0]*grid[1]:raise ModelUnavailable('Unexpected DINOv2 feature grid')
        return tokens,{'grid':grid,'resized':resized,'cropped':cropped,'original':(width,height)}


def foreground_mask(tokens,grid,enabled=True):
    """Unsupervised foreground heuristic; never reads a defect annotation."""
    if not enabled:return np.ones(len(tokens),dtype=bool)
    values=tokens.detach().cpu().numpy() if isinstance(tokens,torch.Tensor) else np.asarray(tokens)
    component=PCA(n_components=1,svd_solver='randomized',random_state=42).fit_transform(values).reshape(grid)
    mask=component>10
    h,w=grid;center=mask[int(h*.2):int(h*.8),int(w*.2):int(w*.8)]
    if center.mean()<=.35:mask=-component>10
    mask=binary_closing(binary_dilation(mask,structure=np.ones((3,3))),structure=np.ones((3,3)),border_value=1)
    if mask.mean()<.01:return np.ones(len(tokens),dtype=bool)
    return mask.ravel()


def score_tokens(tokens,bank,mask):
    features=F.normalize(tokens.float(),dim=-1)
    raw=distances(features,bank)
    selected=raw[torch.as_tensor(mask,device=raw.device,dtype=torch.bool)]
    score=float(selected.topk(max(1,math.ceil(len(selected)*.01))).values.mean())
    raw=raw.masked_fill(~torch.as_tensor(mask,device=raw.device,dtype=torch.bool),0)
    return raw.cpu().numpy(),score


def restore_map(raw,geometry,size=None):
    grid=tuple(geometry['grid']);cropped=tuple(geometry['cropped']);resized=tuple(geometry['resized'])
    patch=Image.fromarray(np.asarray(raw,dtype='float32').reshape(grid)).resize(cropped,Image.Resampling.BILINEAR)
    canvas=Image.new('F',resized);canvas.paste(patch,(0,0))
    return np.asarray(canvas.resize(size or tuple(geometry['original']),Image.Resampling.BILINEAR))


class HighResolutionDetector:
    profile_name='dinov2_highres_v1'

    def __init__(self,settings):
        self.settings=settings;self.directory=settings.root/'models/highres'
        self.encoder=None;self.banks={};self.lock=threading.Lock()

    def cards(self):
        return [json.loads((self.directory/f'{category}.json').read_text()) for category in CATEGORIES]

    def load(self,category):
        if category not in CATEGORIES:raise ValueError('Unsupported product category')
        card=json.loads((self.directory/f'{category}.json').read_text())
        if self.encoder is None:
            source=self.settings.root/'models/encoder_dinov2'
            if sha256(source/'model.safetensors')!=card['encoder_sha256']:raise ModelUnavailable('DINOv2 checkpoint checksum mismatch')
            self.encoder=HighResolutionEncoder(source,self.settings.device)
        if category not in self.banks:
            path=self.directory/f'{category}.npz'
            if sha256(path)!=card['bank_sha256']:raise ModelUnavailable('High-resolution memory checksum mismatch')
            with np.load(path,allow_pickle=False) as saved:bank=saved['patches'].astype('float32')
            self.banks[category]=F.normalize(torch.from_numpy(bank).to(self.encoder.device),dim=-1)
        return card,self.banks[category]

    def predict(self,image,category):
        with self.lock:
            start=time.perf_counter();card,bank=self.load(category)
            if self.encoder.device.type=='cuda':torch.cuda.reset_peak_memory_stats()
            inference=time.perf_counter();tokens,geometry=self.encoder.encode(image)
            mask=foreground_mask(tokens,geometry['grid']);raw,score=score_tokens(tokens,bank,mask)
            if self.encoder.device.type=='cuda':torch.cuda.synchronize()
            elapsed=(time.perf_counter()-inference)*1000
            threshold,margin=card['threshold'],card['uncertainty_margin']
            verdict='Uncertain' if abs(score-threshold)<=margin else 'Anomalous' if score>=threshold else 'Good'
            preview=image.copy();preview.thumbnail((1000,1000))
            full=restore_map(raw,geometry,preview.size)
            result={'category':category,'verdict':verdict,'score':score,'threshold':threshold,'uncertainty_margin':margin,
              'defect_category':None,'model_id':card['model_id'],'model_sha256':card['bank_sha256'],
              'inference_ms':round(elapsed,2),'total_model_ms':round((time.perf_counter()-start)*1000,2),
              'peak_gpu_mb':round(torch.cuda.max_memory_allocated()/1024**2,2) if self.encoder.device.type=='cuda' else None,
              'device':str(self.encoder.device),'localization':f"{geometry['grid'][0]} x {geometry['grid'][1]} DINOv2 patch distances with PCA foreground heuristic; interpolated, not supervised segmentation",
              'scope':'VisA appearance anomaly screening; operator-selected category is not verified; foreground heuristic can fail.',
              'calibration':card['calibration'],'foreground_fraction':float(mask.mean()),'profile':self.profile_name}
            return result,display_map(full,preview,card['heatmap_scale'])
