"""Build a clean release with file hashes, then verify and optionally extract it.
Never modifies model assets, datasets, earlier ZIPs or an existing extraction.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_PARTS={'node_modules','__pycache__','.pytest_cache','.git','runtime','development-support','.venv'}
HISTORICAL={'DEVELOPMENT_PROGRESS.previous.md','PAUSE_CHECKPOINT_20261016.md','acceptance_checkpoint.json',
            'rag_diagnostic.json','scope_diagnostic.json','pause_processes.json'}
ROOT_FILES={'README.md','LICENSE','DEVELOPMENT_PROGRESS.md','.env.example','.gitignore','.dockerignore',
            'requirements.txt','requirements-anomalib.txt','Start-DefectRAG.ps1','Start-DefectRAG.cmd','Dockerfile','compose.yaml','render.yaml'}
ROOT_DIRS={'backend','scripts','tests','knowledge','models','samples','results','docs','deployment','.vscode'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',default='DefectRAG-v2.zip')
    parser.add_argument('--extract',action='store_true')
    args=parser.parse_args()
    if Path(args.name).name!=args.name or not args.name.endswith('.zip'):raise ValueError('Use a ZIP basename')
    archive=ROOT.parent/args.name
    if archive.exists():raise FileExistsError('Earlier archive preserved: '+str(archive))
    paths=[]
    for p in ROOT.rglob('*'):
        if not p.is_file():continue
        relative=p.relative_to(ROOT)
        if set(relative.parts)&EXCLUDED_PARTS or p.name in HISTORICAL:continue
        if p.name.startswith('.env') and p.name!='.env.example':continue
        if p.suffix in {'.pyc','.zip','.bundle','.tar'} or '.sqlite' in p.name:continue
        if len(relative.parts)==1:
            include=p.name in ROOT_FILES
        elif relative.parts[0]=='frontend':
            include=relative.parts[1] in {'src','dist','dist-static','tests','public','package.json','package-lock.json','index.html','vite.config.js','vercel.json'}
        else:include=relative.parts[0] in ROOT_DIRS
        if include:paths.append(p)
    required={'models/encoder/model.safetensors','models/embedding/model.safetensors','knowledge/index/index.npz',
              'frontend/dist/index.html','results/software-tests.xml','README.md','docs/VERIFICATION_REPORT.md'}
    names={p.relative_to(ROOT).as_posix() for p in paths}
    if not required<=names:raise RuntimeError('Missing required release files: '+str(required-names))
    manifest={'schema':1,'created_utc':datetime.now(timezone.utc).isoformat(),
              'git_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
              'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(paths)]}
    manifest_path=ROOT/'RELEASE_MANIFEST.json';manifest_path.write_text(json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as zipped:
        for p in paths+[manifest_path]:zipped.write(p,'DefectRAG-v2/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert len(zipped.namelist())==len(set(zipped.namelist()))
        for item in manifest['files']:
            content=zipped.read('DefectRAG-v2/'+item['path'])
            assert hashlib.sha256(content).hexdigest()==item['sha256']
        extraction=None
        if args.extract:
            extraction=ROOT.parent/('release-verification-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
            extraction.mkdir(exist_ok=False)
            for name in zipped.namelist():
                if not (extraction/name).resolve().is_relative_to(extraction.resolve()):raise ValueError('Unsafe archive entry')
            zipped.extractall(extraction)
    receipt={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest(archive),
             'file_count':len(paths)+1,'crc_and_file_hashes':'passed','duplicate_entries':False,
             'git_commit':manifest['git_commit'],'extracted_project':str(extraction/'DefectRAG-v2') if extraction else None}
    archive.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
