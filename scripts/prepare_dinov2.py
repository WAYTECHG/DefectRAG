"""Fetch only public DINOv2 tensor/config assets into a separate local directory."""
import json
from pathlib import Path
from urllib.request import urlopen
from huggingface_hub import HfApi,snapshot_download
from backend.config import ROOT
from backend.vision import sha256

if __name__=='__main__':
    destination=ROOT/'models/encoder_dinov2'
    destination.mkdir(parents=True,exist_ok=True)
    license_path=destination/'LICENSE'
    if not license_path.exists():
        with urlopen('https://raw.githubusercontent.com/facebookresearch/dinov2/main/LICENSE',timeout=30) as response:
            license_path.write_bytes(response.read())
    receipt=destination/'ASSET_RECEIPT.json'
    if receipt.exists():
        saved=json.loads(receipt.read_text())
        assert sha256(destination/'model.safetensors')==saved['model_sha256']
        print('Preserved existing verified DINOv2 asset.');raise SystemExit(0)
    info=HfApi().model_info('facebook/dinov2-small')
    snapshot_download('facebook/dinov2-small',revision=info.sha,local_dir=destination,
        cache_dir=ROOT/'runtime/model-download-cache',
        allow_patterns=['config.json','model.safetensors','preprocessor_config.json','README.md','LICENSE'])
    receipt.write_text(json.dumps({'repo':'facebook/dinov2-small','revision':info.sha,
        'model_sha256':sha256(destination/'model.safetensors'),'license':'Apache-2.0',
        'source':'https://huggingface.co/facebook/dinov2-small','remote_code':False},indent=2))
    print(receipt.read_text(),flush=True)
