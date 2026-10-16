"""Compare saved official test predictions and reports, without model execution."""
import csv,json
from pathlib import Path
import numpy as np
from backend.config import ROOT,CATEGORIES
from scripts.benchmark_official import write

if __name__=='__main__':
    old=json.loads((ROOT/'results/official_evaluation.json').read_text())
    new=json.loads((ROOT/'results/highres_evaluation.json').read_text())
    assert set(new['categories'])==set(CATEGORIES)
    rows=[]
    for category in CATEGORIES:
        a=json.loads((ROOT/'experiments/official_visa_v1'/category/'split.json').read_text())
        b=json.loads((ROOT/'experiments/dinov2_highres_v1'/category/'split.json').read_text())
        assert {r['image']:r['sha256'] for r in a['test']}=={r['image']:r['sha256'] for r in b['test']}
        before=old['categories'][category]['benchmark_mean'];after=new['categories'][category]['benchmark_mean']
        rows.append({'category':category,'old_image_auroc':before['auroc'],'new_image_auroc':after['auroc'],
          'auroc_change_pp':(after['auroc']-before['auroc'])*100,'old_image_ap':before['average_precision'],
          'new_image_ap':after['average_precision'],'old_pixel_ap':before['pixel_average_precision'],
          'new_pixel_ap':after['pixel_average_precision']})
    for report in (old,new):
        for metric in report['macro_mean']:
            assert abs(report['macro_mean'][metric]-np.mean([c['benchmark_mean'][metric] for c in report['categories'].values()]))<1e-12
    result={'status':'passed','same_official_test_identities_and_content_hashes':True,
      'baseline_macro':old['macro_mean'],'candidate_macro':new['macro_mean'],'candidate_macro_std':new['macro_std'],
      'all_categories':rows,'image_auroc_regressions':[r['category'] for r in rows if r['auroc_change_pp']<0],
      'pixel_ap_regressions':[r['category'] for r in rows if r['new_pixel_ap']<r['old_pixel_ap']],
      'metric_definitions':'Image mAP=unweighted mean of12 category image APs, averaged over3 seeds. Pixel mAP analogous. AU-PR trapezoidal, AP non-interpolated. Seed SD is bank variability, not a generalization confidence interval.',
      'exposure':'Retrospective model development comparison; not an untouched external test.'}
    write(ROOT/'results/highres_comparison.json',result)
    with (ROOT/'results/highres_comparison.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# Measured accuracy comparison','',
      'Same official test identities and content hashes. Three fixed seeds, all12 categories. Retrospective development evaluation; no new untouched-test claim.','',
      '| Product | Original AUROC | DINOv2 AUROC | Change (pp) | Original AP | DINOv2 AP |',
      '|---|---:|---:|---:|---:|---:|']
    lines += [f"| {r['category']} | {r['old_image_auroc']:.4f} | {r['new_image_auroc']:.4f} | {r['auroc_change_pp']:+.2f} | {r['old_image_ap']:.4f} | {r['new_image_ap']:.4f} |" for r in rows]
    lines += ['', '| Overall metric | Original | DINOv2 |','|---|---:|---:|']
    for label,key in [('Mean image AUROC · headline','auroc'),('Mean image AU-PR','au_pr'),('Mean pixel AUROC','pixel_auroc'),('Mean pixel AU-PR','pixel_au_pr'),('Supplementary mean image AP','average_precision'),('Supplementary mean pixel AP','pixel_average_precision')]:
        lines.append(f"| {label} | {old['macro_mean'][key]*100:.2f}% | {new['macro_mean'][key]*100:.2f}% |")
    lines += ['', 'Image AUROC regressions: '+(', '.join(result['image_auroc_regressions']) or 'none')+'.',
      'Pixel AP regressions: '+(', '.join(result['pixel_ap_regressions']) or 'none')+'.',
      'mAP here averages anomaly-ranking AP across products; it is not bounding-box mAP@IoU.','',
      'The benchmark uses all training normals. The deployed bank is a separate fixed-seed profile with a normal-only calibration holdout; see results/highres_deployment_evaluation.json. Historical inspections keep their original model IDs.']
    (ROOT/'docs/ACCURACY_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('all_categories',)},indent=2),flush=True)
