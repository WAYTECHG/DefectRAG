"""Macaroni-only q80 calibration from cached normal scores; no GPU or refitting."""
from copy import deepcopy
import json
from scripts.audit_recall import ROOT, digest, metrics, quantile


def main():
    source=ROOT/'results/sensitive_deployment_evaluation.json'
    baseline=json.loads(source.read_text())
    candidate=deepcopy(baseline)
    candidate.update(decision_policy='macaroni-recall-v1',
        protocol='Same frozen DINOv2 banks and official VisA assignments. Macaroni1/2 use the fixed linear 80th percentile of held-out training-normal scores; the other ten products retain their q95 policy. Higher recall with substantially more false alarms. Retrospective development evaluation, not independent validation.',
        decision_policy_reason='User authorized focusing only on Macaroni1/2 recall, prioritizing anomaly detection with more false alarms and minimal compute.',
        policy_selection_context='Operating policy adopted after examining development-exposed test-score diagnostics. Numeric thresholds use normal calibration only; no test-optimal threshold search or independent-validation claim.',
        previous_evaluation_sha256=digest(source))
    for category in ('macaroni1','macaroni2'):
        directory=ROOT/'experiments/dinov2_highres_v1'/category
        calibration=json.loads((directory/'normal_calibration.json').read_text())
        rows=json.loads((directory/'test_progress.json').read_text())
        scores=[p['score'] for p in calibration['predictions']]
        card=candidate['categories'][category]
        card.update(previous_threshold=card['threshold'], previous_model_id=card['model_id'],
                    threshold=quantile(scores,.8), model_id=card['model_id'].removesuffix('-q95-v1')+'-q80-v1',
                    decision_policy='normal-q80-v1')
        threshold=card['threshold'];card['uncertainty_margin']=threshold*.05
        card['calibration'].update(method='Fixed linear 80th percentile of heldout normal scores; no anomalous calibration',
            policy='normal-q80-v1',quantile=.8,calibration_above_threshold=sum(s>=threshold for s in scores))
        card['metrics'].update(metrics(rows,threshold),
            uncertain_fraction=sum(abs(r['scores'][3]-threshold)<=threshold*.05 for r in rows)/len(rows))
    for category in set(baseline['categories'])-{'macaroni1','macaroni2'}:
        assert candidate['categories'][category]==baseline['categories'][category]
    candidate['macro_mean']={key:sum(c['metrics'][key] for c in candidate['categories'].values())/len(candidate['categories'])
                             for key in baseline['macro_mean']}
    assert digest(source)==candidate['previous_evaluation_sha256']
    output=ROOT/'results/macaroni_recall_deployment_evaluation.json'
    text=json.dumps(candidate,indent=2)+'\n'
    if output.exists() and output.read_text()!=text:raise ValueError('Preserve differing existing version')
    output.write_text(text,encoding='utf8')
    print(json.dumps({'policy':candidate['decision_policy'],'macro_mean':candidate['macro_mean'],
        'categories':{c:candidate['categories'][c]['metrics'] for c in ('macaroni1','macaroni2')},'other_ten_unchanged':True},indent=2))


if __name__=='__main__':main()
