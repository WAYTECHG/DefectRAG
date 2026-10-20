"""Exercise real local Git fast-forwards on temporary fixture repositories only."""
from pathlib import Path
import json
import shutil
import subprocess
import pytest


def git(folder,*args):
    return subprocess.run(['git','-C',str(folder),*args],check=True,capture_output=True,text=True).stdout.strip()


def repositories(tmp_path):
    source=tmp_path/'source';source.mkdir();git(source,'init','-b','main')
    git(source,'config','user.email','fixture@example.invalid');git(source,'config','user.name','Sync fixture')
    for name,text in {'frontend/public/config.js':'fixture-config','deployment/RUN_AND_DEPLOY.md':'fixture-guide','code.py':'old'}.items():
        file=source/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
    git(source,'add','--','frontend/public/config.js','deployment/RUN_AND_DEPLOY.md','code.py');git(source,'commit','-m','fixture baseline')
    desktop=tmp_path/'desktop';subprocess.run(['git','clone',str(source),str(desktop)],check=True,capture_output=True)
    git(source,'switch','-c','feature/auth-mfa-inactive');(source/'code.py').write_text('new')
    git(source,'add','--','code.py');git(source,'commit','-m','fixture update')
    return source,desktop


def run_sync(source,desktop):
    shell=shutil.which('pwsh')
    if not shell:pytest.skip('PowerShell runtime not on PATH; real Desktop run separately required')
    return subprocess.run([shell,'-NoProfile','-File',str(Path('deployment/space/sync_code.ps1').resolve()),
        '-DesktopPath',str(desktop),'-SourcePath',str(source)],capture_output=True,text=True,timeout=30)


def test_sync_preserves_local_config_untracked_files_and_main_branch(tmp_path_factory):
    source,desktop=repositories(tmp_path_factory.mktemp('sync'));baseline=git(desktop,'rev-parse','HEAD')
    (desktop/'frontend/public/config.js').write_text('newer-desktop-config')
    (desktop/'supabase.txt').write_text('fixture-only-never-read-by-sync')
    result=run_sync(source,desktop)
    assert result.returncode==0,result.stderr
    assert (desktop/'code.py').read_text()=='new'
    assert (desktop/'frontend/public/config.js').read_text()=='newer-desktop-config'
    assert (desktop/'supabase.txt').read_text()=='fixture-only-never-read-by-sync'
    assert git(desktop,'rev-parse','main')==baseline
    receipt=json.loads(next((desktop/'development-support/space').glob('desktop-sync-*.json')).read_text(encoding='utf-8-sig'))
    assert receipt['working_builds_replaced'] is False and receipt['datasets_models_secrets_records_copied'] is False


def test_sync_refuses_overlapping_local_code_edits_without_overwrite(tmp_path_factory):
    source,desktop=repositories(tmp_path_factory.mktemp('sync'));before=git(desktop,'rev-parse','HEAD')
    (desktop/'code.py').write_text('newer-local-code')
    result=run_sync(source,desktop)
    assert result.returncode!=0 and 'Overlapping Desktop edits preserved' in result.stderr
    assert git(desktop,'rev-parse','HEAD')==before and (desktop/'code.py').read_text()=='newer-local-code'
