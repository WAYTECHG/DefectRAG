"""Verify snapshot provenance, privacy, asset closure and copied report resources."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def verify():
    output = ROOT / 'frontend/dist-static'
    bundle = output / 'showcase'
    manifest = json.loads((bundle / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = (bundle / name).resolve()
        assert path.is_relative_to(bundle.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    data = json.loads((bundle / 'data.json').read_text(encoding='utf-8'))
    expected = {e['id']: e for e in json.loads((ROOT / 'results/acceptance.json').read_text())['real_images']}
    scope = json.loads((ROOT / 'results/evidence_scope_verification.json').read_text())
    expected[scope['inspection_id']] = scope['answers'][0]['observation']
    extra=ROOT/'results/all_categories_acceptance.json'
    if extra.exists():expected.update({e['id']:e for e in json.loads(extra.read_text())['real_images']})
    assert len(data['records']) == len(expected)
    assert {r['id'] for r in data['records']} == set(expected)
    for record in data['records']:
        assert record['score'] == expected[record['id']]['score']
        assert record['verdict'] == expected[record['id']]['verdict']
        assert (output / record['image_url']).is_file()
        assert (output / record['heatmap_url']).is_file()
        report = bundle / 'reports' / (record['id'] + '.html')
        for image in re.findall(r'src="([^"]+)"', report.read_text(encoding='utf-8')):
            assert (report.parent / image).is_file()
    text = (bundle / 'data.json').read_text(encoding='utf-8')
    assert not re.search(r'localhost|127\.0\.0\.1|[A-Z]:\\\\|api[_-]?key|password|service_role', text, re.I)
    for path in output.rglob('*'):
        assert path.suffix not in {'.sqlite3', '.safetensors', '.pt', '.npz', '.env'}
    assert any(m.get('mode') == 'llm' for messages in data['messages'].values() for m in messages)
    receipt = {'status': 'passed', 'records': len(expected), 'snapshot_hashes': 'passed',
               'scores_match_saved_acceptance': True, 'report_images_exist': True,
               'saved_llm_conversation_present': True, 'no_private_paths_or_model_files': True}
    (ROOT / 'results/static_verification.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    verify()
