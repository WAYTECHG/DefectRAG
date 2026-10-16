"""Bounded normal-only memory fitting, independent calibration and final evaluation.
Run as python -m scripts.train --dataset PATH --encoder PATH.
"""
import argparse
import csv
import json
import time
import platform
import importlib.metadata
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_score, recall_score,
                             f1_score, confusion_matrix, precision_recall_curve)
from backend.vision import Encoder, map_and_score, sha256
from backend.config import ROOT, CATEGORIES

def make_split(rows, category, seed=42, train_count=64):
    rng = np.random.default_rng(seed)
    normal = sorted([r for r in rows if r['object'] == category and r['split']=='train' and r['label']=='normal'], key=lambda x:x['image'])
    test_good = sorted([r for r in rows if r['object']==category and r['split']=='test' and r['label']=='normal'], key=lambda x:x['image'])
    test_bad = sorted([r for r in rows if r['object']==category and r['split']=='test' and r['label']!='normal'], key=lambda x:x['image'])
    rng.shuffle(normal); rng.shuffle(test_bad)
    if len(normal) < train_count+32 or len(test_bad)<40 or not test_good:
        raise ValueError('Dataset split is incomplete')
    # No labelled anomalies enter fitting. Twenty test anomalies are explicitly
    # reassigned to calibration; the result is NOT the full official test protocol.
    return {'train':normal[:train_count], 'validation':normal[train_count:train_count+32]+test_bad[:20], 'test':test_good+test_bad[20:]}

def binary_metrics(labels, scores, threshold):
    prediction = np.asarray(scores) >= threshold
    return {'image_auroc':float(roc_auc_score(labels,scores)), 'average_precision':float(average_precision_score(labels,scores)),
            'precision':float(precision_score(labels,prediction,zero_division=0)), 'recall':float(recall_score(labels,prediction,zero_division=0)),
            'f1':float(f1_score(labels,prediction,zero_division=0)), 'confusion_matrix':confusion_matrix(labels,prediction,labels=[0,1]).tolist(),
            'n_images':len(labels)}

def calibrate(labels, scores):
    p,r,t = precision_recall_curve(labels,scores)
    f = 2*p[:-1]*r[:-1]/np.maximum(p[:-1]+r[:-1],1e-12)
    return float(t[int(np.argmax(f))])

def evaluate(encoder, bank, rows, dataset):
    predictions, maps, masks = [], [], []
    for row in rows:
        start = time.perf_counter()
        with Image.open(dataset / row['image']) as im:
            raw,score = map_and_score(encoder,bank,im)
        elapsed = (time.perf_counter()-start)*1000
        label = int(row['label']!='normal')
        predictions.append({'image':row['image'], 'sha256':sha256(dataset/row['image']), 'label':label, 'score':score, 'latency_ms':elapsed})
        # Explicitly report reduced-resolution pixel metrics including normal images.
        maps.append(np.asarray(Image.fromarray(raw).resize((64,64),Image.Resampling.BILINEAR)).ravel())
        if label:
            with Image.open(dataset/row['mask']) as mask:
                masks.append((np.asarray(mask.convert('L').resize((64,64),Image.Resampling.NEAREST))>0).ravel())
        else:
            masks.append(np.zeros(64*64,dtype=bool))
    return predictions,np.concatenate(maps),np.concatenate(masks)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--encoder',required=True)
    parser.add_argument('--device',default='auto')
    parser.add_argument('--train-count',type=int,default=64)
    parser.add_argument('--categories',nargs='+',choices=CATEGORIES,default=list(CATEGORIES))
    args=parser.parse_args()
    rows=list(csv.DictReader((args.dataset/'split_csv'/'1cls.csv').open(newline='')))
    # Profile one forward before fitting all categories. No gradient training here.
    encoder=Encoder(args.encoder,args.device)
    encoder_path=Path(args.encoder)
    if not encoder_path.is_dir():
        from huggingface_hub import snapshot_download
        encoder_path=Path(snapshot_download(args.encoder,local_files_only=True))
    fingerprint=sha256(encoder_path/'model.safetensors')
    report={'method':'Frozen DINOv3 ViT-S/16 + cosine nearest-normal patch bank',
            'protocol':'64 normal fit images; 32 distinct training normals + 20 official test anomalies for calibration; remaining official test images for final evaluation. Seed 42. Not the full official VisA test protocol.',
            'platform':platform.platform(),'python':platform.python_version(),'torch':torch.__version__,
            'device':str(encoder.device),'encoder_sha256':fingerprint,'categories':{}}
    for category in args.categories:
        start=time.perf_counter()
        splits=make_split(rows,category,train_count=args.train_count)
        hashes={name:{sha256(args.dataset/r['image']) for r in group} for name,group in splits.items()}
        if any(hashes[a]&hashes[b] for a,b in [('train','validation'),('train','test'),('validation','test')]):
            raise ValueError('Cross-split content overlap detected')
        if encoder.device.type=='cuda':
            torch.cuda.reset_peak_memory_stats()
        features=[]
        for row in splits['train']:
            with Image.open(args.dataset/row['image']) as im:
                features.append(encoder.patches(im)[0].cpu())
        bank=torch.cat(features)
        indices=np.random.default_rng(42).choice(len(bank),min(8192,len(bank)),replace=False)
        bank=bank[indices]
        bank_path=ROOT/'models'/f'{category}.npz'
        np.savez_compressed(bank_path,patches=bank.numpy().astype('float16'))
        # Use exactly the saved bank precision for calibration and test.
        bank=F.normalize(torch.from_numpy(np.load(bank_path)['patches'].astype('float32')).to(encoder.device),dim=-1)
        val,vmaps,vmasks=evaluate(encoder,bank,splits['validation'],args.dataset)
        threshold=calibrate([x['label'] for x in val],[x['score'] for x in val])
        pixel_threshold=calibrate(vmasks,vmaps)
        test,tmaps,tmasks=evaluate(encoder,bank,splits['test'],args.dataset)
        metrics=binary_metrics([x['label'] for x in test],[x['score'] for x in test],threshold)
        metrics.update({'pixel_auroc_64':float(roc_auc_score(tmasks,tmaps)),
                        'pixel_average_precision_64':float(average_precision_score(tmasks,tmaps)),
                        'pixel_f1_64':float(f1_score(tmasks,tmaps>=pixel_threshold,zero_division=0)),
                        'pixel_threshold':pixel_threshold,
                        'latency_median_ms':float(np.median([x['latency_ms'] for x in test])),
                        'latency_p95_ms':float(np.percentile([x['latency_ms'] for x in test],95)),
                        'peak_gpu_mb':torch.cuda.max_memory_allocated()/1024**2 if encoder.device.type=='cuda' else None})
        margin=threshold*.05
        metrics['uncertain_fraction']=float(np.mean([abs(x['score']-threshold)<=margin for x in test]))
        card={'category':category,'available':True,'model_id':f'dinov3-normal-bank-{category}-v1','method':report['method'],
              'encoder_sha256':fingerprint,'bank_sha256':sha256(bank_path),'threshold':threshold,'uncertainty_margin':margin,
              'uncertainty_policy':'Fixed ±5% of validated threshold. Operational review band, not calibrated confidence.',
              'heatmap_scale':float(np.quantile(vmaps,.995)),'bank_size_bytes':bank_path.stat().st_size,
              'encoder_size_bytes':(encoder_path/'model.safetensors').stat().st_size,
              'calibration':{'method':'Max F1 on separate validation identities','normal':32,'anomalous':20,'seed':42},
              'train_normal_count':len(splits['train']),'metrics':metrics,'fit_and_evaluation_seconds':time.perf_counter()-start}
        (ROOT/'models'/f'{category}.json').write_text(json.dumps(card,indent=2))
        manifest={name:[{**r,'sha256':sha256(args.dataset/r['image'])} for r in group] for name,group in splits.items()}
        (ROOT/'results'/f'{category}_splits.json').write_text(json.dumps(manifest,indent=2))
        (ROOT/'results'/f'{category}_predictions.json').write_text(json.dumps({'validation':val,'test':test},indent=2))
        report['categories'][category]=card
        (ROOT/'results'/'evaluation.json').write_text(json.dumps(report,indent=2))
        print(category,json.dumps(metrics),flush=True)
        for label,name in [('normal','good'),('anomaly','anomalous')]:
            row=next(r for r in splits['test'] if (r['label']=='normal')==(label=='normal'))
            with Image.open(args.dataset/row['image']) as im:
                im=im.convert('RGB'); im.thumbnail((640,640)); im.save(ROOT/'samples'/f'{category}_{name}.jpg',quality=90)
    print('Completed. Final metrics are frozen; do not tune against final-test labels.',flush=True)

if __name__=='__main__': main()
