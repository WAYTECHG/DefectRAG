"""Audit cached operational scores without inference or changes to model assets.

The two fixed quantiles are sensitivity diagnostics, never test-selected policies.
Results are retrospective: they are not fresh validation of a replacement threshold.
"""
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    index = int(position)
    return values[index] + (values[min(index + 1, len(values) - 1)] - values[index]) * (position - index)


def metrics(rows, threshold):
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = row['scores'][3] >= threshold
        actual = row['label'] == 1
        tp += predicted and actual
        fp += predicted and not actual
        tn += not predicted and not actual
        fn += not predicted and actual
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {'precision': precision, 'recall': recall,
            'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            'false_positive_rate': fp / (fp + tn) if fp + tn else 0.0,
            'confusion_matrix': [[tn, fp], [fn, tp]]}


def main():
    evaluation_path = ROOT / 'results/highres_deployment_evaluation.json'
    evaluation = json.loads(evaluation_path.read_text())
    report = {
        'scope': 'Cached-score retrospective threshold sensitivity audit; no inference, training or activation',
        'limitations': [
            'Official test results were previously seen; candidate figures are descriptive, not independent validation.',
            'Quantiles use only saved held-out normal scores; no anomalous labels choose thresholds.',
            'A 95th-percentile calibration threshold does not guarantee a 5% future false-positive rate.',
            'Binary metrics use score >= threshold; the dashboard review band is separate.',
            'Changing a threshold does not improve AUROC or feature separation.',
        ],
        'source_sha256': {str(evaluation_path.relative_to(ROOT)): digest(evaluation_path)},
        'categories': {},
    }
    for category, card in evaluation['categories'].items():
        directory = ROOT / 'experiments/dinov2_highres_v1' / category
        paths = [directory / name for name in ('normal_calibration.json', 'test_progress.json', 'split.json')]
        calibration, rows, split = [json.loads(path.read_text()) for path in paths]
        for path in paths:
            report['source_sha256'][str(path.relative_to(ROOT))] = digest(path)
        scores = [row['score'] for row in calibration['predictions']]
        assert scores and all(math.isfinite(score) for score in scores)
        assert all(row['label'] in (0, 1) and len(row['scores']) == 4 and
                   all(math.isfinite(score) for score in row['scores']) for row in rows)
        assert len(rows) == len(split['test']) == card['metrics']['n_images']
        assert all(row['label'] == int(source['label'] != 'normal') and row['image'] == source['image']
                   for row, source in zip(rows, split['test']))
        train_hashes = {row['sha256'] for row in split['train']}
        test_hashes = {row['sha256'] for row in split['test']}
        held_hashes = set(sorted(train_hashes)[::10])
        assert not train_hashes & test_hashes
        assert {row['sha256'] for row in calibration['predictions']} == held_hashes
        assert max(scores) == calibration['threshold'] == card['threshold']
        current = metrics(rows, card['threshold'])
        for key in ('precision', 'recall', 'f1'):
            assert math.isclose(current[key], card['metrics'][key], abs_tol=1e-12)
        assert current['confusion_matrix'] == card['metrics']['confusion_matrix']
        policies = {}
        for name, threshold in [('current_maximum', max(scores)),
                                ('diagnostic_normal_q99', quantile(scores, .99)),
                                ('diagnostic_normal_q95', quantile(scores, .95))]:
            policies[name] = {'threshold': threshold, **metrics(rows, threshold)}
        report['categories'][category] = {'calibration_normals': len(scores), 'policies': policies}
    report['checks'] = 'All 12 saved confusion matrices and precision/recall/F1 reproduced; labels, counts and content splits checked.'
    report['macro_mean'] = {
        policy: {metric: sum(category['policies'][policy][metric] for category in report['categories'].values()) / len(report['categories'])
                 for metric in ('precision', 'recall', 'f1', 'false_positive_rate')}
        for policy in ('current_maximum', 'diagnostic_normal_q99', 'diagnostic_normal_q95')}
    # Check original inputs again before saving an entirely separate audit artifact.
    assert all(digest(ROOT / path) == value for path, value in report['source_sha256'].items())
    output = ROOT / 'results/recall_threshold_audit.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'checks': report['checks'], 'macro_mean': report['macro_mean'], 'output': str(output)}, indent=2))


if __name__ == '__main__':
    main()
