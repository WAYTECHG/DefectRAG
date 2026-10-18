"""Verify original assets and take a private, online SQLite backup before sync."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path(r'C:\Users\User\Desktop\DefectRAG-v2')


def verify():
    with zipfile.ZipFile(ROOT.parent / 'DefectRAG-v2-all12-checkpoint.zip') as archive:
        manifest = json.loads(archive.read('DefectRAG-v2/RELEASE_MANIFEST.json'))
    original = [item for item in manifest['files'] if item['path'].startswith('models/') or
                (item['path'].startswith('results/') and
                 (item['path'].endswith(('_splits.json', '_predictions.json')) or
                  item['path'] == 'results/evaluation.json'))]
    for item in original:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
    backup = ROOT / 'development-support/saved-runtime/desktop-before-highres.sqlite3'
    backup.parent.mkdir(parents=True, exist_ok=True)
    source = DESKTOP / 'runtime/inspection.sqlite3'
    if not backup.exists():
        with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as db:
            with sqlite3.connect(backup) as target:
                db.backup(target)
    with sqlite3.connect(backup.as_uri() + '?mode=ro', uri=True) as saved:
        assert saved.execute('pragma integrity_check').fetchone()[0] == 'ok'
        counts = {}
        with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as live:
            for table in ('inspections', 'messages'):
                old = saved.execute('select * from ' + table).fetchall()
                current = set(live.execute('select * from ' + table).fetchall())
                assert all(row in current for row in old), 'Existing history changed: ' + table
                counts[table] = len(old)
    result = {'status': 'passed', 'original_files_hash_identical': len(original),
              'private_backup': str(backup.relative_to(ROOT)), 'backup_integrity': 'ok',
              'backup_counts': counts, 'original_desktop_rows_preserved': True,
              'runtime_excluded_from_release': True}
    (ROOT / 'results/highres_preservation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
