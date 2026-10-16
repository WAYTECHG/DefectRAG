"""One preregistered DINOv2 high-resolution candidate. Resume receipts; no test tuning."""
import argparse,csv,json,platform,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from threadpoolctl import threadpool_limits
from backend.config import ROOT,CATEGORIES
from backend.vision import sha256
from backend.highres import HighResolutionEncoder,foreground_mask,score_tokens,restore_map
from scripts.benchmark_official import write,rank_metrics,pixel_metrics


def save_array(path,**arrays):
    temporary=path.with_suffix('.npz.partial')
    with temporary.open('wb') as stream:np.savez_compressed(stream,**arrays)
    temporary.replace(path)


def select_banks(directory,seed_ids,held_indices):
    output=[]
    for j,seed in enumerate((42,43,44,42)):
        path=directory/f'bank_{j}.npz'
        if path.exists():
            output.append(np.load(path,allow_pickle=False)['patches']);continue
        files=[p for i,p in enumerate(seed_ids) if j!=3 or i not in held_indices]
        # Fixed image-balanced reservoir: 48 foreground + 16 remaining patches per normal.
        rng=np.random.default_rng(seed);samples=[]
        for file in files:
            with np.load(file,allow_pickle=False) as cached:
                features=cached['features'].astype('float32');mask=cached['mask']
            foreground=np.flatnonzero(mask);background=np.flatnonzero(~mask)
            chosen=np.r_[rng.choice(foreground,min(48,len(foreground)),replace=False),
                         rng.choice(background,min(16,len(background)),replace=False)]
            samples.append(features[chosen])
        bank=np.concatenate(samples)
        if len(bank)>32768:bank=bank[rng.choice(len(bank),32768,replace=False)]
        bank=F.normalize(torch.from_numpy(bank),dim=-1).numpy().astype('float16')
        save_array(path,patches=bank);output.append(bank)
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--categories',nargs='+',choices=CATEGORIES,default=list(CATEGORIES))
    args=parser.parse_args();output=ROOT/'experiments/dinov2_highres_v1';output.mkdir(parents=True,exist_ok=True)
    source=ROOT/'models/encoder_dinov2'
    protocol={'schema':1,'method':'AnomalyDINO-inspired DINOv2 ViT-S/14; custom full-data adaptation',
      'resolution':'short edge448; bicubic; retain aspect; crop trailing pixels to patch multiple14',
      'encoder_sha256':sha256(source/'model.safetensors'),'split_csv_sha256':sha256(args.dataset/'split_csv/1cls.csv'),
      'seeds':[42,43,44],'bank_patches':32768,'memory_sampling':'per train normal: up to48 PCA foreground +16 other patches, seeded uniform cap',
      'foreground':'PCA first component threshold10; center-sign rule; 2D3x3 dilation/closing; <1% mask falls back to all patches',
      'score':'mean of top1% foreground cosine distances','fit':'all official training normals for benchmark',
      'calibration':'separate deployment bank excludes every tenth content-hash-sorted training normal; maximum heldout normal score',
      'evaluation':'full official test; masks only for pixel metrics at224x224; image AP and trapezoidal AU-PR separately',
      'selection':'one fixed candidate; no test-based hyperparameter changes; seeds42/43/44 all reported; deployment seed42 fixed',
      'exposure':'retrospective development comparison; official test identities and earlier results already seen; not an untouched external test',
      'references':['https://arxiv.org/html/2405.14529v2','https://github.com/dammsi/AnomalyDINO'],
      'differences_from_paper':'HF encoder; image-balanced limited full-data memory; masking train and test; 2D morphology; no rotation augmentation'}
    path=output/'protocol.json'
    if path.exists():assert json.loads(path.read_text())==protocol,'Use a new version for changed settings'
    else:write(path,protocol)
    rows=list(csv.DictReader((args.dataset/'split_csv/1cls.csv').open(newline='')))
    encoder=HighResolutionEncoder(source)
    report_path=output/'evaluation.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {'protocol':protocol,'python':platform.python_version(),'torch':torch.__version__,'device':str(encoder.device),'categories':{}}
    for category in args.categories:
        directory=output/category;directory.mkdir(exist_ok=True)
        receipt=directory/'complete.json'
        if receipt.exists():
            for name,digest in json.loads(receipt.read_text())['files'].items():assert sha256(directory/name)==digest
            print('Preserved completed category '+category,flush=True);continue
        started=time.perf_counter()
        train=sorted([r for r in rows if r['object']==category and r['split']=='train'],key=lambda r:r['image'])
        test=sorted([r for r in rows if r['object']==category and r['split']=='test'],key=lambda r:r['image'])
        manifest=directory/'split.json'
        if manifest.exists():split=json.loads(manifest.read_text())
        else:
            split={group:[{**r,'sha256':sha256(args.dataset/r['image'])} for r in data] for group,data in [('train',train),('test',test)]}
            write(manifest,split)
        assert all(r['label']=='normal' for r in train) and sum(r['label']!='normal' for r in test)==100
        assert not {r['sha256'] for r in split['train']}&{r['sha256'] for r in split['test']}
        # Sort by content hash, grouping duplicates; no duplicate can straddle operational fit/holdout.
        train=sorted(split['train'],key=lambda r:(r['sha256'],r['image']))
        held_hashes=set(sorted({r['sha256'] for r in train})[::10])
        held_indices={i for i,r in enumerate(train) if r['sha256'] in held_hashes}
        cache=directory/'features';cache.mkdir(exist_ok=True);files=[]
        for i,row in enumerate(train):
            destination=cache/f'{i:04d}.npz';files.append(destination)
            if not destination.exists():
                with Image.open(args.dataset/row['image']) as image:tokens,geometry=encoder.encode(image)
                mask=foreground_mask(tokens,geometry['grid'])
                # Cache only the bounded deterministic per-image pool; holdout needs all features.
                if i in held_indices:chosen=np.arange(len(tokens))
                else:
                    rng=np.random.default_rng(i+2026);fg=np.flatnonzero(mask);bg=np.flatnonzero(~mask)
                    chosen=np.r_[rng.choice(fg,min(192,len(fg)),replace=False),rng.choice(bg,min(64,len(bg)),replace=False)]
                save_array(destination,features=tokens[chosen].cpu().numpy().astype('float16'),mask=mask[chosen])
            if (i+1)%100==0:print(f'{category}: encoded {i+1}/{len(train)} training normals',flush=True)
        arrays=select_banks(directory,files,held_indices)
        banks=[F.normalize(torch.from_numpy(bank.astype('float32')).to(encoder.device),dim=-1) for bank in arrays]
        calibration=[];scales=[]
        for i in sorted(held_indices):
            with np.load(files[i],allow_pickle=False) as saved:
                raw,score=score_tokens(torch.from_numpy(saved['features'].astype('float32')).to(encoder.device),banks[3],saved['mask'])
                scales.extend(raw[raw>0].tolist());calibration.append({'image':train[i]['image'],'sha256':train[i]['sha256'],'score':score})
        threshold=max(p['score'] for p in calibration);scale=float(np.quantile(scales,.995))
        write(directory/'normal_calibration.json',{'threshold':threshold,'heatmap_scale':scale,'fit_normals':len(train)-len(calibration),
            'heldout_normals':len(calibration),'predictions':calibration,'policy':'max heldout normal score; no test labels/masks'})
        # Flush every test image, so hibernation/disconnection need not repeat completed inference.
        predictions_path=directory/'test_progress.json';predictions=json.loads(predictions_path.read_text()) if predictions_path.exists() else []
        maps_dir=directory/'maps';maps_dir.mkdir(exist_ok=True)
        for i,row in enumerate(test):
            if i<len(predictions):continue
            with Image.open(args.dataset/row['image']) as image:tokens,geometry=encoder.encode(image)
            mask=foreground_mask(tokens,geometry['grid']);scores=[];maps=[]
            for bank in banks:
                raw,score=score_tokens(tokens,bank,mask);scores.append(score);maps.append(restore_map(raw,geometry,(224,224)))
            save_array(maps_dir/f'{i:04d}.npz',maps=np.asarray(maps,dtype='float32'))
            predictions.append({'image':row['image'],'label':int(row['label']!='normal'),'scores':scores,'foreground_fraction':float(mask.mean())})
            write(predictions_path,predictions)
            if (i+1)%50==0:print(f'{category}: evaluated {i+1}/{len(test)} test images',flush=True)
        masks=[]
        for row in test:
            if row['label']=='normal':mask=np.zeros((224,224),dtype=bool)
            else:
                with Image.open(args.dataset/row['mask']) as image:mask=np.asarray(image.convert('L').resize((224,224),Image.Resampling.NEAREST))>0
            masks.append(mask.ravel())
        truth=np.concatenate(masks);runs=[]
        for j in range(4):
            maps=np.concatenate([np.load(maps_dir/f'{i:04d}.npz',allow_pickle=False)['maps'][j].ravel() for i in range(len(test))])
            runs.append({**rank_metrics([p['label'] for p in predictions],[p['scores'][j] for p in predictions]),**pixel_metrics(truth,maps)})
        keys=list(runs[0]);metrics={'official_train_normals':len(train),'official_test_images':len(test),
          'benchmark_runs':[{'seed':seed,**runs[j]} for j,seed in enumerate((42,43,44))],
          'benchmark_mean':{k:float(np.mean([r[k] for r in runs[:3]])) for k in keys},
          'benchmark_std':{k:float(np.std([r[k] for r in runs[:3]],ddof=1)) for k in keys},
          'deployment_holdout_profile':{'threshold':threshold,'heatmap_scale':scale,**runs[3]},'seconds':time.perf_counter()-started}
        write(directory/'metrics.json',metrics)
        write(receipt,{'status':'passed','files':{p.name:sha256(p) for p in directory.iterdir() if p.is_file() and p.name!='complete.json'}})
        report['categories'][category]=metrics;write(report_path,report)
        print(category,json.dumps(metrics['benchmark_mean']),flush=True)
        del banks,arrays,truth,maps
    if len(report['categories'])==12:
        keys=list(next(iter(report['categories'].values()))['benchmark_mean'])
        report['macro_mean']={k:float(np.mean([c['benchmark_mean'][k] for c in report['categories'].values()])) for k in keys}
        report['macro_runs']=[{'seed':seed,**{k:float(np.mean([c['benchmark_runs'][j][k] for c in report['categories'].values()])) for k in keys}} for j,seed in enumerate((42,43,44))]
        report['macro_std']={k:float(np.std([r[k] for r in report['macro_runs']],ddof=1)) for k in keys}
        write(report_path,report);write(ROOT/'results/highres_evaluation.json',report)
    print('Candidate checkpoint saved; original models unchanged.',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
