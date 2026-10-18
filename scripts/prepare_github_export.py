"""Build a small source-only GitHub upload folder; never copy private state/history."""
import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES=('backend/','scripts/','tests/','deployment/','knowledge/','frontend/src/',
             'frontend/tests/','frontend/public/','docs/')
FILES={'README.md','LICENSE','.gitignore','.dockerignore','.env.example','requirements.txt',
       'requirements-anomalib.txt','Dockerfile','compose.yaml','render.yaml',
       'Start-DefectRAG.cmd','Start-DefectRAG.ps1','frontend/package.json',
       'frontend/package-lock.json','frontend/index.html','frontend/vite.config.js',
       'results/evaluation.json','results/official_evaluation.json','results/highres_evaluation.json',
       'results/highres_deployment_evaluation.json','results/highres_comparison.json','results/highres_comparison.csv'}
FILES.update({'results/sensitive_deployment_evaluation.json','results/recall_threshold_audit.json',
              'results/macaroni_recall_deployment_evaluation.json'})
EXCLUDED=('knowledge/index/','frontend/public/config.js','docs/README_LEGACY.md')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'development-support/github-ready/DefectRAG')
    args=parser.parse_args()
    output=args.output.resolve()
    assert output.is_relative_to(ROOT/'development-support'),'Keep exports under development-support.'
    assert not output.exists(),'Choose a new empty export destination; existing exports are preserved.'
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    copied=[]
    for name in filter(None,paths):
        if name not in FILES and not name.startswith(DIRECTORIES):continue
        if name.startswith(EXCLUDED) or Path(name).suffix in ('.sqlite','.npz','.safetensors','.pt','.zip','.log'):continue
        path=ROOT/name
        if not path.is_file() or path.is_symlink():continue
        if path.stat().st_size>15*1024*1024:raise ValueError('Unexpected large tracked file: '+name)
        target=output/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
        copied.append(name)
    config=output/'frontend/public/config.js'
    config.parent.mkdir(parents=True,exist_ok=True)
    config.write_text('window.DEFECTRAG_PUBLIC_CONFIG = {supabaseUrl:"",supabasePublishableKey:""};\n')
    credential=re.compile(r'hf_[A-Za-z0-9]{25,}|sb_secret_[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}')
    for path in output.rglob('*'):
        if path.is_file() and path.suffix in ('.py','.js','.jsx','.json','.md','.txt','.html'):
            assert not credential.search(path.read_text(encoding='utf8',errors='replace')),'Credential-like value requires review: '+str(path.relative_to(output))
    assert not any((output/name).exists() for name in ('models','runtime','experiments','.venv','.git','.env','DEVELOPMENT_PROGRESS.md'))
    manifest={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
              'files':len(copied)+1,'public_config_blank':True,
              'excluded':'Git history, models, datasets, private runtime, environments, local evidence, secrets, build outputs'}
    (output/'GITHUB_EXPORT.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'folder':str(output),**manifest}))

if __name__=='__main__':
    main()
