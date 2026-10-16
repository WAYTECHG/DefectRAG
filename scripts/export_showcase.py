"""Export only the six allowlisted, already measured VisA acceptance examples.

Reads SQLite in read-only mode; never performs inference or publishes arbitrary uploads.
"""
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'frontend' / 'public' / 'showcase'


def export(output=OUTPUT):
    acceptance = json.loads((ROOT / 'results/acceptance.json').read_text())
    examples = list(acceptance['real_images'])
    if len(examples) != 6 or len({e['id'] for e in examples}) != 6:
        raise ValueError('Expected six distinct verified acceptance examples')
    scope = json.loads((ROOT / 'results/evidence_scope_verification.json').read_text())
    final_fingerprint = scope['answers'][0]['knowledge_fingerprint']
    examples.append({**scope['answers'][0]['observation'], 'truth': 1})
    extra_path=ROOT/'results/all_categories_acceptance.json'
    extra=json.loads(extra_path.read_text())['real_images'] if extra_path.exists() else []
    examples.extend(extra)
    extra_ids={e['id'] for e in extra}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'images').mkdir(exist_ok=True)
    (output / 'reports').mkdir(exist_ok=True)
    records, samples, conversations = [], [], {}
    fields = ['id', 'created_at', 'category', 'verdict', 'score', 'threshold',
              'uncertainty_margin', 'inference_ms', 'model_id']
    database = ROOT / 'runtime/inspection.sqlite3'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        for example in examples:
            extra_db=sqlite3.connect((ROOT/'runtime/verification12/inspection.sqlite3').as_uri()+'?mode=ro',uri=True) if example['id'] in extra_ids else None
            selected=extra_db or db
            row = selected.execute('SELECT payload FROM inspections WHERE id=?', (example['id'],)).fetchone()
            if not row:
                raise ValueError('Saved measured example missing: ' + example['id'])
            source = json.loads(row[0])
            record = {k: source[k] for k in fields if k in source}
            if record['score'] != example['score'] or record['verdict'] != example['verdict']:
                raise ValueError('Example differs from measured acceptance record')
            identifier = record['id']
            record.update(batch='Verified VisA examples', filename='VisA example',
                          image_url=f'showcase/images/{identifier}.jpg',
                          heatmap_url=f'showcase/images/{identifier}_heatmap.jpg')
            for suffix in ('.jpg', '_heatmap.jpg'):
                artifacts=ROOT/('runtime/verification12/artifacts' if extra_db else 'runtime/artifacts')
                shutil.copyfile(artifacts / (identifier + suffix),
                                output / 'images' / (identifier + suffix))
            name = record['category'] + ('_anomalous' if example['truth'] else '_good')
            if identifier == scope['inspection_id']:
                name += '_followup'
            samples.append({'name': name, 'category': record['category'], 'record_id': identifier,
                            'url': record['image_url'], 'attribution': 'VisA · Zou et al., ECCV 2022 · CC BY 4.0'})
            # Publish saved validated answers and abstentions; omit obsolete fallback diagnostics.
            rows = selected.execute('SELECT role,payload FROM messages WHERE inspection_id=? ORDER BY id', (identifier,)).fetchall()
            if extra_db:extra_db.close()
            messages = []
            for previous, current in zip(rows, rows[1:]):
                if previous[0] != 'user' or current[0] != 'assistant':
                    continue
                answer = json.loads(current[1])
                if answer.get('mode') not in ('llm', 'abstained'):
                    continue
                if answer.get('mode') == 'llm' and answer.get('knowledge_fingerprint') != final_fingerprint:
                    continue
                messages.extend([{'role': 'user', 'question': json.loads(previous[1])['question']},
                                 {'role': 'assistant', **{k: answer[k] for k in ('answer', 'mode', 'evidence', 'trace') if k in answer}}])
            if identifier == scope['inspection_id']:
                messages = []
                for answer in scope['answers']:
                    messages.extend([{'role': 'user', 'question': answer['question']},
                                     {'role': 'assistant', **{k: answer[k] for k in ('answer', 'mode', 'evidence', 'trace')}}])
            conversations[identifier] = messages
            records.append(record)
            esc = lambda value: html.escape(str(value))
            table = ''.join(f'<tr><th>{esc(k)}</th><td>{esc(record.get(k, ""))}</td></tr>' for k in fields)
            discussion = ''.join('<p>' + esc(m.get('question', m.get('answer', ''))) + '</p>' for m in messages)
            sources = {s['chunk_id']: s for m in messages for s in m.get('evidence', [])}
            discussion += '<h2>Retrieved source passages</h2>' + ''.join(
                '<article><h3>' + esc(k) + ' · ' + esc(s['title']) + '</h3><p>' + esc(s['text']) + '</p><p>' + esc(s['url']) + '</p></article>'
                for k, s in sources.items())
            (output / 'reports' / (identifier + '.html')).write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Saved DefectRAG example</title><style>body{font:16px system-ui;max-width:900px;margin:30px auto;padding:16px}img{max-width:46%}th,td{padding:6px;text-align:left}@media print{button{display:none}}</style>'
                '<h1>Saved inspection example</h1><p>Previously measured VisA example. No live inference runs on this website.</p>'
                '<p>VisA · Zou et al., ECCV 2022 · CC BY 4.0 · resized images and model overlay. '
                '<a href="https://github.com/amazon-science/spot-diff">Dataset source</a></p>'
                '<button onclick="window.print()">Print / save PDF</button><table>' + table + '</table>'
                f'<h2>Image and measured heatmap</h2><img alt="VisA sample" src="../images/{identifier}.jpg"><img alt="Saved heatmap" src="../images/{identifier}_heatmap.jpg">'
                '<h2>Recorded evidence conversation</h2>' + discussion + '</html>', encoding='utf-8')
    evaluation = json.loads((ROOT / 'results/evaluation.json').read_text())
    evaluation['serving_profile'] = json.loads((ROOT / 'results/serving_profile.json').read_text())
    # These files contain only evaluation metrics/configuration, not private runtime paths.
    data = {'schema': 1, 'mode': 'saved_examples', 'records': records, 'samples': samples,
            'messages': conversations, 'evaluation': evaluation,
            'attribution': 'VisA · Zou et al., ECCV 2022 · CC BY 4.0 · resized images and model overlays',
            'source': 'https://github.com/amazon-science/spot-diff'}
    text = json.dumps(data, indent=2)
    if ':\\' in text or 'Users/' in text or 'localhost' in text or '127.0.0.1' in text:
        raise ValueError('Local path or service address found in public snapshot')
    (output / 'data.json').write_text(text, encoding='utf-8')
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(records)
    (output / 'inspections.csv').write_text(buffer.getvalue(), encoding='utf-8')
    hashes = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
    (output / 'manifest.json').write_text(json.dumps({'files': hashes, 'records': len(records),
        'provenance': 'results/acceptance.json + results/evidence_scope_verification.json; existing runtime artifacts; no experiments repeated'}, indent=2))
    print(json.dumps({'status': 'passed', 'examples': len(records), 'files': len(hashes), 'output': str(output)}))


if __name__ == '__main__':
    export()
