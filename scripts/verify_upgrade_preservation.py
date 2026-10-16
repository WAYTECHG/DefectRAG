"""Hash-check original artifacts and take a read-only SQLite backup before syncing."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    with zipfile.ZipFile(ROOT.parent/'DefectRAG-v2-all12-checkpoint.zip') as archive:
        manifest=json.loads(archive.read('DefectRAG-v2/RELEASE_MANIFEST.json'))
    original=[e for e in manifest['files'] if e['path'].startswith('models/') or
              (e['path'].startswith('results/') and (e['path'].endswith('_splits.json') or
               e['path'].endswith('_predictions.json') or e['path']=='results/evaluation.json'))]
    for item in original:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    desktop=Path(r'C:\Users\User\Desktop\DefectRAG-v2')
    backup=ROOT/'development-support/saved-runtime/desktop-before-upgrade.sqlite3'
    backup.parent.mkdir(parents=True,exist_ok=True)
    source=desktop/'runtime/inspection.sqlite3'
    if not backup.exists():
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as db,sqlite3.connect(backup) as target:
            db.backup(target)
    with sqlite3.connect(backup.as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
        counts={name:db.execute('select count(*) from '+name).fetchone()[0] for name in ('inspections','messages')}
    result={'status':'passed','original_model_and_evaluation_files_unchanged':len(original),
            'reference':'DefectRAG-v2-all12-checkpoint.zip','desktop_history_backup':'development-support/saved-runtime/desktop-before-upgrade.sqlite3',
            'backup_integrity':'ok','backup_counts':counts,'backup_excluded_from_public_release':True}
    (ROOT/'results/upgrade_preservation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
