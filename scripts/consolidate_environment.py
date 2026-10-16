"""Repair an already moved Windows venv, or verify the consolidated local app.

No package downloads, model fitting, archive creation or directory deletion.
Run with the moved .venv/Scripts/python.exe. Moves are handled separately.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / 'development-support'


def save(name, result):
    SUPPORT.mkdir(exist_ok=True)
    (SUPPORT / name).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


def repair():
    target = ROOT / '.venv'
    assert Path(sys.prefix).resolve() == target.resolve(), 'Use this project virtual environment'
    assert (ROOT / '.python-deps').is_dir(), 'Local dependency overlay missing'
    site = target / 'Lib/site-packages'
    (site / 'defectrag-local-deps.pth').write_text('../../../.python-deps\n', encoding='utf-8')
    # Refresh activation/configuration without reinstalling packages or copying
    # the running executable. Installed CUDA libraries stay untouched.
    builder = venv.EnvBuilder(with_pip=False)
    context = builder.ensure_directories(str(target))
    builder.create_configuration(context)
    builder.setup_scripts(context)
    from pip._vendor.distlib.scripts import ScriptMaker
    maker = ScriptMaker(None, str(target / 'Scripts'))
    maker.executable = str(target / 'Scripts/python.exe')
    maker.clobber = True
    maker.variants = {''}
    written = set()
    for distribution in importlib.metadata.distributions():
        for entry in distribution.entry_points:
            if entry.group not in ('console_scripts', 'gui_scripts') or entry.name in written:
                continue
            if Path(entry.name).name != entry.name:
                raise ValueError('Unsafe installed entry point')
            maker.make(entry.name + ' = ' + entry.value,
                       options={'gui': entry.group == 'gui_scripts'})
            written.add(entry.name)
    for name in ('pip', 'pip3', 'pip3.12'):
        maker.make(name + ' = pip._internal.cli.main:main')
    save('environment-relocation.json', {'status': 'passed', 'python': sys.executable,
         'repaired_console_entry_points': len(written), 'packages_reinstalled': False})


def verify():
    import torch
    from backend.config import Settings, CATEGORIES
    from backend.main import create_app
    from fastapi.testclient import TestClient
    from backend.vision import sha256
    assert Path(sys.prefix).resolve() == (ROOT / '.venv').resolve()
    for module in ('fastapi', 'uvicorn', 'transformers', 'langchain_core',
                   'langchain_community', 'langchain_text_splitters', 'langgraph'):
        __import__(module)
    verified = 0
    for experiment in ('official_visa_v1', 'dinov2_highres_v1'):
        for category in CATEGORIES:
            folder = ROOT / 'experiments' / experiment / category
            receipt = json.loads((folder / 'complete.json').read_text())
            for name, expected in receipt['files'].items():
                assert sha256(folder / name) == expected, str(folder / name)
                verified += 1
    # Private rows must survive consolidation unchanged.
    backup = SUPPORT / 'saved-runtime/desktop-before-highres.sqlite3'
    with sqlite3.connect(backup.as_uri() + '?mode=ro', uri=True) as old:
        with sqlite3.connect((ROOT / 'runtime/inspection.sqlite3').as_uri() + '?mode=ro', uri=True) as current:
            for table in ('inspections', 'messages'):
                rows = set(current.execute('select * from ' + table).fetchall())
                assert all(row in rows for row in old.execute('select * from ' + table))
    app = create_app(Settings(data=ROOT / 'runtime/consolidation-check'))
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        assert client.get('/api/health').status_code == 200
        sample = ROOT / 'samples/pcb1_anomalous.jpg'
        response = client.post('/api/inspect', data={'category': 'pcb1', 'batch': 'consolidation-check'},
                               files={'file': (sample.name, sample.read_bytes(), 'image/jpeg')})
        response.raise_for_status()
        record = response.json()['data']
        assert record['model_id'] == 'dinov2-highres-pcb1-v1'
        assert client.get(record['heatmap_url']).status_code == 200
        answer = client.post('/api/assistant', json={'inspection_id': record['id'],
                              'question': 'Is this image anomalous?'})
        answer.raise_for_status()
        assert record['verdict'] in answer.json()['data']['answer']
    for executable in ('pip.exe', 'uvicorn.exe'):
        subprocess.run([str(ROOT / '.venv/Scripts' / executable), '--version'], check=True)
    save('consolidation-verification.json', {'status': 'passed', 'python': sys.executable,
         'torch': torch.__version__, 'cuda': torch.cuda.is_available(),
         'experiment_files_hash_verified': verified, 'complete_experiments': 2,
         'categories_each': 12, 'private_history': 'preserved',
         'real_api_inspection': {key: record[key] for key in ('model_id', 'score', 'verdict', 'device')},
         'assistant': 'passed', 'console_launchers': 'passed', 'packages_reinstalled': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repair', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.repair:
        repair()
    if args.verify:
        verify()
