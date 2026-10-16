"""Install the completed candidate beside legacy banks, then mark it active.

Release choice is a disclosed retrospective comparison, not fresh test validation.
No best-seed or per-category model selection is performed.
"""
import json,shutil
from pathlib import Path
import numpy as np
from backend.config import ROOT,CATEGORIES
from backend.vision import sha256
from scripts.benchmark_official import write
from scripts.train import binary_metrics

if __name__=='__main__':
    experiment=ROOT/'experiments/dinov2_highres_v1'
    report=json.loads((ROOT/'results/highres_evaluation.json').read_text())
    original=json.loads((ROOT/'results/official_evaluation.json').read_text())
    assert set(report['categories'])==set(CATEGORIES)
    assert report['macro_mean']['auroc']>original['macro_mean']['auroc'],'Candidate did not improve macro image AUROC; not activated'
    assert report['macro_mean']['average_precision']>original['macro_mean']['average_precision'],'Candidate did not improve image mAP; not activated'
    directory=ROOT/'models/highres';directory.mkdir(exist_ok=True)
    evaluation={'method':report['protocol']['method'],'profile':'dinov2_highres_v1',
      'protocol':'Official VisA test assignments; operational bank fitted on official training normals excluding a content-grouped 10% normal calibration holdout. Threshold=max heldout normal score. Retrospective development evaluation; not an untouched external test.',
      'encoder_sha256':report['protocol']['encoder_sha256'],'device':report['device'],'categories':{}}
    for category in CATEGORIES:
        source=experiment/category
        for name,digest in json.loads((source/'complete.json').read_text())['files'].items():assert sha256(source/name)==digest
        target=directory/f'{category}.npz'
        if target.exists():assert sha256(target)==sha256(source/'bank_3.npz'),'Preserve unknown existing candidate bank'
        else:shutil.copyfile(source/'bank_3.npz',target)
        calibration=json.loads((source/'normal_calibration.json').read_text())
        predictions=json.loads((source/'test_progress.json').read_text())
        labels=np.array([p['label'] for p in predictions]);scores=np.array([p['scores'][3] for p in predictions])
        threshold=calibration['threshold'];margin=threshold*.05
        ranking=report['categories'][category]['deployment_holdout_profile']
        metrics={**binary_metrics(labels,scores,threshold),'pixel_auroc_224':ranking['pixel_auroc'],
          'pixel_average_precision_224':ranking['pixel_average_precision'],'uncertain_fraction':float(np.mean(np.abs(scores-threshold)<=margin)),
          'latency_median_ms':None,'peak_gpu_mb':None}
        card={'category':category,'available':True,'model_id':f'dinov2-highres-{category}-v1',
          'method':report['protocol']['method'],'profile':'dinov2_highres_v1',
          'encoder_sha256':report['protocol']['encoder_sha256'],'bank_sha256':sha256(target),
          'threshold':threshold,'uncertainty_margin':margin,'heatmap_scale':calibration['heatmap_scale'],
          'uncertainty_policy':'Fixed ±5% of threshold; operational heuristic, not calibrated confidence',
          'bank_size_bytes':target.stat().st_size,'encoder_size_bytes':(ROOT/'models/encoder_dinov2/model.safetensors').stat().st_size,
          'calibration':{'method':'Maximum heldout normal score; no anomalous calibration','normal':calibration['heldout_normals'],'anomalous':0,'seed':42},
          'train_normal_count':calibration['fit_normals'],'metrics':metrics,'resolution_short_edge':448,'patch_size':14,
          'foreground':'Unsupervised PCA threshold/sign heuristic; can fail'}
        path=directory/f'{category}.json'
        if path.exists():assert json.loads(path.read_text())==card,'Preserve existing differing model card'
        else:write(path,card)
        evaluation['categories'][category]=card
    evaluation['macro_mean']={key:float(np.mean([c['metrics'][key] for c in evaluation['categories'].values()])) for key in ('image_auroc','average_precision','precision','recall','f1','pixel_auroc_224','pixel_average_precision_224')}
    assert evaluation['macro_mean']['image_auroc']>original['macro_mean']['auroc'],'Operational AUROC did not improve; profile remains inactive'
    assert evaluation['macro_mean']['average_precision']>original['macro_mean']['average_precision'],'Operational mAP did not improve; profile remains inactive'
    write(ROOT/'results/highres_deployment_evaluation.json',evaluation)
    write(directory/'PROFILE.json',{'status':'active','profile':'dinov2_highres_v1','categories':list(CATEGORIES),
      'benchmark':'results/highres_evaluation.json','deployment_evaluation':'results/highres_deployment_evaluation.json',
      'release_choice':'Single fixed candidate improved retrospective macro AUROC and mAP; no per-category or best-seed selection',
      'legacy_recovery':'Set DEFECTRAG_PROFILE=legacy; original models and scores unchanged'})
    print(json.dumps({'status':'installed','benchmark_macro':report['macro_mean'],'deployment_macro':evaluation['macro_mean']},indent=2),flush=True)
