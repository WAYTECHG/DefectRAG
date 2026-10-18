"""Create a separate normal-only q95 policy, preserving every baseline artifact.

This is a recall-oriented development policy, not new independent validation.
Test labels are used only to report its retrospective operating metrics.
"""
from copy import deepcopy
import json
from pathlib import Path

from scripts.audit_recall import ROOT, digest, metrics, quantile


def main():
    source = ROOT / 'results/highres_deployment_evaluation.json'
    baseline_hash = digest(source)
    baseline = json.loads(source.read_text())
    candidate = deepcopy(baseline)
    candidate.update(decision_policy='normal-q95-v1',
        protocol='Official VisA test assignments; same frozen DINOv2 operational banks. Threshold is the fixed linear 95th percentile of the existing content-grouped held-out training-normal scores. All categories use the same quantile; no test-label optimization. Retrospective development evaluation, not independent validation.',
        baseline_evaluation_sha256=baseline_hash,
        validation_scope='Normal-only calibration and cached-score/software consistency checks; future recall and false-alarm rates are not guaranteed.',
        decision_policy_reason='User requested prioritizing anomaly recall and accepts more false alarms.',
        policy_selection_context='Policy adopted after viewing retrospective threshold-sensitivity results; not an independent or test-blind validation.',
        source_sha256={})
    for category, card in candidate['categories'].items():
        directory = ROOT / 'experiments/dinov2_highres_v1' / category
        calibration_path = directory / 'normal_calibration.json'
        predictions_path = directory / 'test_progress.json'
        calibration = json.loads(calibration_path.read_text())
        rows = json.loads(predictions_path.read_text())
        normal_scores = [row['score'] for row in calibration['predictions']]
        assert max(normal_scores) == card['threshold']
        assert len(normal_scores) == card['calibration']['normal']
        # Threshold uses only normal calibration scores. Never optimize on test labels.
        threshold = quantile(normal_scores, .95)
        card.update(baseline_threshold=card['threshold'], threshold=threshold,
                    uncertainty_margin=threshold*.05, decision_policy='normal-q95-v1',
                    model_id=card['model_id']+'-q95-v1')
        card['calibration'].update(method='Fixed linear 95th percentile of heldout normal scores; no anomalous calibration',
                                   policy='normal-q95-v1', quantile=.95,
                                   calibration_above_threshold=sum(s >= threshold for s in normal_scores),
                                   future_false_positive_rate_guaranteed=False)
        card['metrics'].update(metrics(rows, threshold),
            uncertain_fraction=sum(abs(row['scores'][3]-threshold) <= threshold*.05 for row in rows)/len(rows))
        for path in (calibration_path, predictions_path):
            candidate['source_sha256'][str(path.relative_to(ROOT))] = digest(path)
    candidate['macro_mean'] = {key: sum(c['metrics'][key] for c in candidate['categories'].values()) / len(candidate['categories'])
                               for key in (*baseline['macro_mean'], 'false_positive_rate')}
    assert digest(source) == baseline_hash
    output = ROOT / 'results/sensitive_deployment_evaluation.json'
    text = json.dumps(candidate, indent=2) + '\n'
    if output.exists() and output.read_text() != text:
        raise ValueError('Preserve differing existing calibration; use a new policy version')
    output.write_text(text, encoding='utf-8')
    print(json.dumps({'output':str(output),'baseline_preserved_sha256':baseline_hash,'macro_mean':candidate['macro_mean']}, indent=2))


if __name__ == '__main__':
    main()
