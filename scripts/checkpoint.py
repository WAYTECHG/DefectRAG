"""Non-destructive development snapshot. Excludes caches and active DB files.

SQLite is preserved through its online backup API, avoiding inconsistent WAL copies.
This is not the final release packaging script.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import sqlite3
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()

def main():
    # Keep the small additional LangChain packages for offline DEVELOPMENT only.
    overlay=ROOT.parent/'.test-deps'
    if overlay.exists():
        shutil.copytree(overlay,ROOT/'development-support'/'langchain-overlay',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    history=ROOT/'runtime'/'inspection.sqlite3'
    backup=ROOT/'development-support'/'saved-runtime'/'inspection.sqlite3'
    if history.exists():
        backup.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(history) as source,sqlite3.connect(backup) as target:
            source.backup(target)
        artifacts=ROOT/'runtime'/'artifacts'
        if artifacts.exists():
            shutil.copytree(artifacts,backup.parent/'artifacts',dirs_exist_ok=True)
    excluded={'node_modules','runtime','__pycache__','.pytest_cache','.git','.venv','.venv-defectrag'}
    paths=[p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts)&excluded)
           and p.name not in {'.env','CHECKPOINT_MANIFEST.json'} and p.suffix not in {'.pyc','.zip'}]
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'purpose':'Resumable development checkpoint; not final accepted release',
              'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(paths)]}
    manifest_path=ROOT/'CHECKPOINT_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=ROOT.parent/'DefectRAG-v2-checkpoint-20261016.zip'
    if archive.exists():
        archive=ROOT.parent/('DefectRAG-v2-checkpoint-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as zipped:
        for path in [*paths,manifest_path]:zipped.write(path,'DefectRAG-v2/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert 'DefectRAG-v2/DEVELOPMENT_PROGRESS.md' in zipped.namelist()
        assert not any('/runtime/' in name or '/node_modules/' in name for name in zipped.namelist())
    receipt={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest(archive),'file_count':len(paths)+1,'zip_crc_check':'passed',
             'manifest':'DefectRAG-v2/CHECKPOINT_MANIFEST.json'}
    receipt_path=archive.with_suffix('.receipt.json')
    receipt_path.write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
