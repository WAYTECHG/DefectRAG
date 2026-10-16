import json
from pathlib import Path
import numpy as np
from sklearn.metrics import auc
from scripts.benchmark_official import pixel_metrics


def test_vectorized_pixel_metric_matches_reference_threshold_scan_with_ties():
    truth=np.array([False,False,True,True,False,True,False])
    scores=np.array([.1,.2,.2,.8,.8,.9,.1],dtype=np.float32)
    positive=scores[truth]
    thresholds=np.sort(np.r_[np.percentile(positive,np.linspace(100,0,100)),
        np.linspace(positive.max(),positive.min(),100),float(scores.min())-1e-8,float(scores.max())+1e-8])[::-1]
    fpr=[];recall=[];precision=[]
    for threshold in thresholds:
        predicted=scores.astype(np.float64)>threshold
        tp=np.sum(predicted&truth);fp=np.sum(predicted&~truth)
        recall.append(tp/truth.sum());fpr.append(fp/(~truth).sum())
        precision.append(tp/(tp+fp) if tp+fp else 1)
    actual=pixel_metrics(truth,scores)
    assert abs(actual['pixel_auroc']-auc(fpr,recall))<1e-12
    assert abs(actual['pixel_au_pr']-auc(recall,precision))<1e-12


def test_official_report_uses_all_official_identities_and_no_anomalous_calibration():
    root=Path(__file__).resolve().parents[1]
    report=json.loads((root/'results/official_evaluation.json').read_text())
    assert len(report['categories'])==12
    for category,metrics in report['categories'].items():
        directory=root/'experiments/official_visa_v1'/category
        if not directory.exists():continue  # Banks/manifests are a separate optional experiment artifact.
        split=json.loads((directory/'split.json').read_text())
        assert len(split['train'])==metrics['official_train_normals']
        assert len(split['test'])==metrics['official_test_images']
        assert all(r['split']=='train' and r['label']=='normal' for r in split['train'])
        assert all(r['split']=='test' for r in split['test'])
        assert sum(r['label']!='normal' for r in split['test'])==100
        assert [r['seed'] for r in metrics['benchmark_runs']]==[42,43,44]
        holdout=json.loads((directory/'normal_calibration.json').read_text())
        assert holdout['threshold']==max(p['score'] for p in holdout['predictions'])
        train_names={r['image'] for r in split['train']}
        assert all(p['image'] in train_names for p in holdout['predictions'])
