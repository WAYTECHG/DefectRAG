"""Versioned VisA official-split benchmark, with a separate normal-calibrated profile.

No test labels/masks choose model settings or deployment thresholds. Existing
application banks and measured results are never overwritten. No gradient training.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, auc
from backend.config import ROOT, CATEGORIES
from backend.vision import Encoder, distances, sha256


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def rank_metrics(labels, scores):
    precision, recall, _=precision_recall_curve(labels, scores)
    return {'auroc':float(roc_auc_score(labels,scores)),
            'au_pr':float(auc(recall,precision)),
            'average_precision':float(average_precision_score(labels,scores))}


def pixel_metrics(labels, scores):
    """Reference VisA 200-threshold integration, computed via sorted counts."""
    positive=np.sort(scores[labels]); negative=np.sort(scores[~labels])
    thresholds=np.sort(np.concatenate([np.percentile(positive,np.linspace(100,0,100)),
        np.linspace(positive.max(),positive.min(),100),[float(scores.min())-1e-8,float(scores.max())+1e-8]]))[::-1]
    tp=len(positive)-np.searchsorted(positive,thresholds,side='right')
    fp=len(negative)-np.searchsorted(negative,thresholds,side='right')
    recall=tp/len(positive); fpr=fp/len(negative)
    precision=np.divide(tp,tp+fp,out=np.ones(len(tp)),where=(tp+fp)>0)
    return {'pixel_auroc':float(auc(fpr,recall)),'pixel_au_pr':float(auc(recall,precision)),
            'pixel_average_precision':float(average_precision_score(labels,scores))}


def score_features(features, bank):
    raw=distances(features,bank)
    score=float(raw.topk(max(1,int(np.ceil(len(raw)*.01)))).values.mean().item())
    return raw.cpu().numpy(),score


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'experiments/official_visa_v1')
    parser.add_argument('--device',default='auto')
    parser.add_argument('--categories',nargs='+',choices=CATEGORIES,default=list(CATEGORIES))
    args=parser.parse_args(); output=args.output.resolve()
    if not output.is_relative_to(ROOT):raise ValueError('Experiment output must remain inside this project')
    csv_path=args.dataset/'split_csv/1cls.csv'
    encoder_hash=sha256(ROOT/'models/encoder/model.safetensors')
    protocol={'schema':1,'dataset':'VisA official split_csv/1cls.csv','split_csv_sha256':sha256(csv_path),
        'method':'Frozen DINOv3 ViT-S/16 + cosine nearest-normal patch memory; custom baseline, not Dinomaly',
        'encoder_sha256':encoder_hash,'benchmark_seeds':[42,43,44],'bank_patch_limit':8192,
        'image_score':'mean of highest 1% patch distances','pixel_evaluation_resolution':224,
        'pixel_metrics':'VisA reference 200-threshold AUROC/AU-PR; normal images included; AP separately',
        'preprocessing':'bundled DINOv3 image processor, default 224 input; no augmentation or GT masks in features',
        'benchmark':'all official training normals; all official test images; threshold-free ranking metrics',
        'deployment':'seed42; 10% official training normals held out; threshold=max held-out normal score; no test anomalies used',
        'prior_test_exposure':'retrospective benchmark: test images/results were seen in earlier modified-split experiments; no new test-driven tuning',
        'selection_policy':'fixed before execution; all three seeds reported; no best-seed selection',
        'sources':['https://github.com/amazon-science/spot-diff','https://arxiv.org/html/2207.14315',
                   'https://raw.githubusercontent.com/amazon-science/spot-diff/main/utils/metrics.py']}
    protocol_file=output/'protocol.json'
    if protocol_file.exists():
        if json.loads(protocol_file.read_text())!=protocol:raise RuntimeError('Existing experiment settings differ; use a new version')
    else:write(protocol_file,protocol)
    rows=list(csv.DictReader(csv_path.open(newline='')))
    encoder=Encoder(ROOT/'models/encoder',args.device)
    report={'protocol':protocol,'python':platform.python_version(),'torch':torch.__version__,
            'device':str(encoder.device),'categories':{}}
    report_path=output/'evaluation.json'
    if report_path.exists():report=json.loads(report_path.read_text())
    for category in args.categories:
        receipt=output/category/'complete.json'
        if receipt.exists():
            saved=json.loads(receipt.read_text())
            for name,digest in saved['files'].items():
                if sha256(output/category/name)!=digest:raise RuntimeError('Completed artifact changed: '+name)
            report['categories'][category]=json.loads((output/category/'metrics.json').read_text())
            print('Preserved completed official category: '+category,flush=True);continue
        started=time.perf_counter(); directory=output/category; directory.mkdir(parents=True,exist_ok=True)
        train=sorted([r for r in rows if r['object']==category and r['split']=='train'],key=lambda r:r['image'])
        test=sorted([r for r in rows if r['object']==category and r['split']=='test'],key=lambda r:r['image'])
        assert train and test and all(r['label']=='normal' for r in train)
        assert sum(r['label']!='normal' for r in test)==100
        manifest={group:[{**r,'sha256':sha256(args.dataset/r['image'])} for r in group_rows]
                  for group,group_rows in [('train',train),('test',test)]}
        assert not {r['sha256'] for r in manifest['train']}&{r['sha256'] for r in manifest['test']}
        write(directory/'split.json',manifest)
        with Image.open(args.dataset/train[0]['image']) as image:first,side=encoder.patches(image)
        patches=len(first); total=len(train)*patches
        selections=[np.sort(np.random.default_rng(seed).choice(total,min(8192,total),replace=False)) for seed in (42,43,44)]
        # Separate operational holdout; grouped by content hash to prevent duplicate leakage.
        unique=sorted({r['sha256'] for r in manifest['train']})
        held_hashes=set(np.random.default_rng(42).choice(unique,max(1,int(np.ceil(len(unique)*.10))),replace=False))
        fit_ids=[i for i,r in enumerate(manifest['train']) if r['sha256'] not in held_hashes]
        held_ids=set(range(len(train)))-set(fit_ids); fit_position={v:i for i,v in enumerate(fit_ids)}
        deploy_selection=np.sort(np.random.default_rng(42).choice(len(fit_ids)*patches,min(8192,len(fit_ids)*patches),replace=False))
        buffers=[[],[],[],[]]; held_features=[]
        for i,row in enumerate(train):
            if i==0:features=first
            else:
                with Image.open(args.dataset/row['image']) as image:features,grid=encoder.patches(image)
                assert grid==side
            cpu=features.cpu()
            for j,selection in enumerate(selections):
                chosen=selection[np.searchsorted(selection,i*patches):np.searchsorted(selection,(i+1)*patches)]-i*patches
                if len(chosen):buffers[j].append(cpu[chosen])
            if i in held_ids:held_features.append((row['image'],cpu.half()))
            else:
                position=fit_position[i]
                chosen=deploy_selection[np.searchsorted(deploy_selection,position*patches):np.searchsorted(deploy_selection,(position+1)*patches)]-position*patches
                if len(chosen):buffers[3].append(cpu[chosen])
            if (i+1)%200==0:print(f'{category}: extracted {i+1}/{len(train)} official training normals',flush=True)
        banks=[]
        for j,buffer in enumerate(buffers):
            array=torch.cat(buffer).numpy().astype('float16')
            np.savez_compressed(directory/f'bank_{j}.npz',patches=array)
            banks.append(F.normalize(torch.from_numpy(array.astype('float32')).to(encoder.device),dim=-1))
        del buffers,first
        validation=[]; val_maps=[]
        for name,features in held_features:
            raw,score=score_features(features.float().to(encoder.device),banks[3]);validation.append({'image':name,'score':score});val_maps.extend(raw.tolist())
        threshold=max(v['score'] for v in validation)
        write(directory/'normal_calibration.json',{'threshold':threshold,'fit_normals':len(fit_ids),'held_out_normals':len(held_ids),
            'policy':'maximum held-out normal score; no anomalous validation; fixed 5% operational review band','predictions':validation,
            'heatmap_scale':float(np.quantile(val_maps,.995))})
        predictions=[[],[],[],[]]; maps=[[],[],[],[]]; masks=[]
        for i,row in enumerate(test):
            with Image.open(args.dataset/row['image']) as image:features,_=encoder.patches(image)
            label=int(row['label']!='normal')
            if label:
                with Image.open(args.dataset/row['mask']) as image:mask=np.asarray(image.convert('L').resize((224,224),Image.Resampling.NEAREST))>0
            else:mask=np.zeros((224,224),dtype=bool)
            masks.append(mask.ravel())
            for j,bank in enumerate(banks):
                raw,score=score_features(features,bank)
                predictions[j].append({'image':row['image'],'label':label,'score':score})
                maps[j].append(np.asarray(Image.fromarray(raw.reshape(side,side)).resize((224,224),Image.Resampling.BILINEAR)).ravel())
            if (i+1)%100==0:print(f'{category}: evaluated {i+1}/{len(test)} official test images',flush=True)
        truth=np.concatenate(masks); runs=[]
        for j in range(4):
            metrics={**rank_metrics([r['label'] for r in predictions[j]],[r['score'] for r in predictions[j]]),
                     **pixel_metrics(truth,np.concatenate(maps[j]))}
            write(directory/f'predictions_{j}.json',predictions[j]);runs.append(metrics)
        keys=list(runs[0]); category_report={'official_train_normals':len(train),'official_test_images':len(test),
            'benchmark_runs':[{'seed':seed,**runs[j]} for j,seed in enumerate((42,43,44))],
            'benchmark_mean':{k:float(np.mean([r[k] for r in runs[:3]])) for k in keys},
            'benchmark_std':{k:float(np.std([r[k] for r in runs[:3]],ddof=1)) for k in keys},
            'deployment_holdout_profile':{'seed':42,'threshold':threshold,'fit_normals':len(fit_ids),'validation_normals':len(held_ids),**runs[3]},
            'seconds':time.perf_counter()-started}
        write(directory/'metrics.json',category_report)
        files={p.name:sha256(p) for p in directory.iterdir() if p.is_file() and p.name!='complete.json'}
        write(receipt,{'status':'passed','files':files})
        report['categories'][category]=category_report;write(report_path,report)
        print(category,json.dumps(category_report['benchmark_mean']),flush=True)
        del maps,masks,banks,held_features
    if len(report['categories'])==len(CATEGORIES):
        keys=list(next(iter(report['categories'].values()))['benchmark_mean'])
        report['macro_mean']={k:float(np.mean([r['benchmark_mean'][k] for r in report['categories'].values()])) for k in keys}
        report['macro_runs']=[{'seed':seed,**{k:float(np.mean([r['benchmark_runs'][j][k] for r in report['categories'].values()])) for k in keys}} for j,seed in enumerate((42,43,44))]
        report['macro_std']={k:float(np.std([r[k] for r in report['macro_runs']],ddof=1)) for k in keys}
        write(report_path,report);write(ROOT/'results/official_evaluation.json',report)
    print('Saved official-split experiment. Existing application banks were not replaced.',flush=True)


if __name__=='__main__':main()
