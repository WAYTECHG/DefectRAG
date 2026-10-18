"""Versioned decision calibration; encoder, memory and old records stay unchanged."""
import json
import math
import os


POLICY = 'normal-q95-v1'
FILENAME = 'sensitive_deployment_evaluation.json'


def active_evaluation(root, baseline):
    policy = os.getenv('DEFECTRAG_CALIBRATION', POLICY)
    if policy == 'normal-max-v1':
        return baseline
    if policy != POLICY:
        raise ValueError('Unknown decision calibration policy')
    path = root / 'results' / FILENAME
    if not path.exists():
        return baseline
    candidate = json.loads(path.read_text())
    if candidate.get('decision_policy') != POLICY or set(candidate['categories']) != set(baseline['categories']):
        raise ValueError('Invalid decision calibration manifest')
    for category, original in baseline['categories'].items():
        card = candidate['categories'][category]
        for key in ('category', 'profile', 'encoder_sha256', 'bank_sha256', 'heatmap_scale', 'train_normal_count'):
            if card[key] != original[key]:
                raise ValueError('Calibration manifest does not match the original model: ' + category)
        if (card['baseline_threshold'] != original['threshold'] or
                card['model_id'] != original['model_id'] + '-q95-v1' or
                card['calibration'].get('policy') != POLICY or
                card['calibration']['normal'] != original['calibration']['normal'] or
                card['calibration']['anomalous'] != 0 or
                not math.isfinite(card['threshold']) or not 0 < card['threshold'] <= original['threshold'] or
                not math.isclose(card['uncertainty_margin'], card['threshold'] * .05, abs_tol=1e-12)):
            raise ValueError('Invalid calibrated threshold: ' + category)
    return candidate


def calibrated_card(root, original):
    # Both local and ZeroGPU inference use this exact manifest and guard logic.
    baseline_path = root / 'results/highres_deployment_evaluation.json'
    if not baseline_path.exists():
        return original
    baseline = json.loads(baseline_path.read_text())
    for key in ('threshold', 'model_id', 'encoder_sha256', 'bank_sha256'):
        if baseline['categories'][original['category']][key] != original[key]:
            raise ValueError('Original model card and evaluation disagree')
    return active_evaluation(root, baseline)['categories'][original['category']]
