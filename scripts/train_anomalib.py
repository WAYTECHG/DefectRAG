"""Optional Anomalib Dinomaly experiment; unverified, never started automatically.

Uses the same frozen identity manifest as the compact detector. DINOv3 is not
silently passed to a DINOv2-only interface. Export is deliberately separate from
the shipped memory-bank API until independently evaluated and integrated.
"""
import argparse
import json
from pathlib import Path
from backend.config import ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--category',choices=['pcb1','capsules','cashew'],required=True)
    parser.add_argument('--authorize-training',action='store_true')
    parser.add_argument('--steps',type=int,default=500)
    args=parser.parse_args()
    if not args.authorize_training: parser.error('Requires approval via --authorize-training; may download a DINOv2 backbone')
    from anomalib.models import Dinomaly
    from anomalib.engine import Engine
    from anomalib.data import Folder
    import shutil
    import torch
    if not torch.cuda.is_available(): raise RuntimeError('This optional training path requires a compatible CUDA runtime')
    free,total=torch.cuda.mem_get_info()
    print(f'GPU memory before model: {free/1024**3:.2f} GiB free / {total/1024**3:.2f} GiB total')
    if free<4*1024**3: raise RuntimeError('Less than 4 GiB free; stop and profile before training')
    split=json.loads((ROOT/'results'/f'{args.category}_splits.json').read_text())
    staging=ROOT/'runtime'/'anomalib-data'/args.category
    for partition,rows in split.items():
        for row in rows:
            label='good' if row['label']=='normal' else 'bad'
            destination=staging/partition/label/Path(row['image']).name
            destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists():shutil.copyfile(args.dataset/row['image'],destination)
    # Folder automatic validation must not consume final test images: the
    # manifest validation set is passed explicitly using validation directories.
    datamodule=Folder(name=args.category,root=staging,normal_dir='train/good',normal_test_dir='validation/good',abnormal_dir='validation/bad',val_split_mode='same_as_test',train_batch_size=2,eval_batch_size=2,num_workers=0)
    model=Dinomaly(encoder_name='vit_small_patch14_dinov2',decoder_depth=4,
        target_layers=[2,3,4,5],fuse_layer_encoder=[[0,1],[2,3]],fuse_layer_decoder=[[0,1],[2,3]])
    engine=Engine(default_root_dir=str(ROOT/'runtime'/'anomalib-training'),max_steps=args.steps,accelerator='gpu',devices=1)
    engine.fit(model,datamodule=datamodule)
    engine.trainer.save_checkpoint(str(ROOT/'runtime'/'anomalib-training'/f'{args.category}.ckpt'))
    print('Experimental checkpoint saved. Final-test evaluation and API adapter remain required; do not replace calibrated production cards.')
if __name__=='__main__':main()
