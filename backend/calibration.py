"""Versioned decision calibration; encoder, memory and old records stay unchanged."""
import json
import math
import os


POLICY = 'normal-q95-v1'
FILENAME = 'sensitive_deployment_evaluation.json'
MACARONI_POLICY = 'macaroni-recall-v1'
MACARONI_FILENAME = 'macaroni_recall_deployment_evaluation.json'


def active_evaluation(root, baseline):
    policy = os.getenv('DEFECTRAG_CALIBRATION', MACARONI_POLICY)
    if policy == 'normal-max-v1':
        return baseline
    if policy not in (POLICY, MACARONI_POLICY):
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
    if policy == POLICY or not (root / 'results' / MACARONI_FILENAME).exists():
        return candidate
    targeted = json.loads((root / 'results' / MACARONI_FILENAME).read_text())
    if targeted.get('decision_policy') != MACARONI_POLICY or set(targeted['categories']) != set(candidate['categories']):
        raise ValueError('Invalid Macaroni calibration manifest')
    for category, previous in candidate['categories'].items():
        card = targeted['categories'][category]
        if category not in ('macaroni1','macaroni2'):
            if card != previous:
                raise ValueError('Macaroni-only policy changed another category')
            continue
        mutable = {'threshold','uncertainty_margin','model_id','calibration','metrics','decision_policy','previous_threshold','previous_model_id'}
        if ({k:v for k,v in card.items() if k not in mutable} !=
                {k:v for k,v in previous.items() if k not in mutable} or
                card['previous_threshold'] != previous['threshold'] or
                card['previous_model_id'] != previous['model_id'] or
                card['model_id'] != baseline['categories'][category]['model_id'] + '-q80-v1' or
                card['decision_policy'] != 'normal-q80-v1' or
                card['calibration'].get('policy') != 'normal-q80-v1' or
                card['calibration'].get('quantile') != .8 or
                card['calibration']['normal'] != previous['calibration']['normal'] or
                card['calibration']['anomalous'] != 0 or
                not math.isfinite(card['threshold']) or not 0 < card['threshold'] <= previous['threshold'] or
                not math.isclose(card['uncertainty_margin'], card['threshold']*.05, abs_tol=1e-12)):
            raise ValueError('Invalid Macaroni-only threshold: ' + category)
        for key in ('image_auroc','average_precision','pixel_auroc_224','pixel_average_precision_224','n_images'):
            if card['metrics'][key] != previous['metrics'][key]:
                raise ValueError('Decision calibration changed ranking metrics')
    return targeted


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
