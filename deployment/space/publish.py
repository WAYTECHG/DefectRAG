"""Allowlisted incremental commits; no private runtime, dataset or secrets upload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd

ROOT = Path(__file__).resolve().parents[2]
REPO = 'Wizzas/DefectRAG'
OUT = ROOT/'development-support/space'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=int, choices=(2,3,4,5), required=True)
    args = parser.parse_args()
    if args.phase>=4:
        confirmation=OUT/'migration-confirmed.json'
        assert confirmation.exists() and json.loads(confirmation.read_text()).get('user_confirmed_manual_execution'), 'Wait for the user to confirm manual SQL execution before enabling staff persistence.'
    files = {}
    for relative in ('docs/THIRD_PARTY_NOTICES.md','docs/FRONTEND_LICENSES.txt','models/BGE-LICENSE.txt'):
        path=ROOT/relative
        if path.exists():
            files[relative]=path
    for relative in ('results/sensitive_deployment_evaluation.json',):
        files[relative]=ROOT/relative
    for directory in ('backend','deployment/space'):
        for path in (ROOT/directory).glob('*.py'):
            files[path.relative_to(ROOT).as_posix()] = path
    for path in (ROOT/'development-support/space/ui-dist').rglob('*'):
        if path.is_file():
            files['frontend/dist/'+path.relative_to(ROOT/'development-support/space/ui-dist').as_posix()] = path
    for path in (ROOT/'models/highres').glob('*.npz'):
        files[path.relative_to(ROOT).as_posix()] = path
    if args.phase>=3:
        for path in (ROOT/'models/embedding').rglob('*'):
            if path.is_file() and path.suffix not in ('.py','.pyc'):
                files[path.relative_to(ROOT).as_posix()] = path
        for path in (ROOT/'knowledge').glob('*.md'):
            files[path.relative_to(ROOT).as_posix()] = path
    requirements = (ROOT/'deployment/zerogpu_phase1/requirements-space.txt').read_text(encoding='utf-8')
    # The platform's unused preinstalled datasets 5 requires Hub <2. Gradio needs
    # >=1.16; pin the compatible intersection rather than upgrading unrelated libs.
    requirements = requirements.replace('huggingface-hub==2.2.0','huggingface-hub==1.31.0')
    root_app = ("import os\nfrom pathlib import Path\n"
                "os.environ['DEFECTRAG_SPACE_UI']=str(Path(__file__).parent/'frontend/dist')\n"
                "os.environ['GRADIO_ANALYTICS_ENABLED']='False'\n"
                f"os.environ['DEFECTRAG_LIVE_RAG']='{'1' if args.phase>=3 else '0'}'\n"
                f"os.environ['DEFECTRAG_STAFF_BACKEND']='{'1' if args.phase>=4 else '0'}'\n"
                "from deployment.space.app import server\n"
                "server.launch(server_name='0.0.0.0',server_port=7860,ssr_mode=False,show_error=True,run_history=False)\n")
    readme = (ROOT/'deployment/zerogpu_phase1/SPACE_README.md').read_text(encoding='utf-8')
    header = readme.split('---',2)[1].replace('DefectRAG - Phase 1 compatibility test','DefectRAG').replace('Existing React UI plus one genuine DINOv2 ZeroGPU inspection','Live React dashboard and DINOv2 inspection on ZeroGPU')
    body = f'''\n# DefectRAG — migration phase {args.phase}\n
Existing React UI, real frozen DINOv2 inspection across all 12 VisA categories,
original normal-reference banks and heatmaps, with versioned normal-only decision
calibration. No training rerun. The q95 sensitivity policy trades more false
alarms for higher recall; historical inspection decisions are preserved.
Anonymous browser history is isolated and temporary. Sign in to the configured
staff workspace for durable shared records when available. Do not treat anomaly
scores as probabilities or diagnoses. The operator selects the product category.

Gradio client requests use bounded GPU leases. Quotas and cold starts apply.
Local application and static showcase are preserved separately.

VisA: Amazon Science, CC BY 4.0, Zou et al., ECCV 2022.
DINOv2: Meta, Apache-2.0. See docs/THIRD_PARTY_NOTICES.md.
'''
    raw = {'app.py':root_app.encode(),'requirements.txt':requirements.encode(),
           'README.md':('---'+header+'---\n'+body).encode()}
    assert not any(part in ('.env','runtime','node_modules','experiments','.venv') for name in files for part in Path(name).parts)
    api = HfApi()
    before = api.space_info(REPO)
    assert api.get_space_runtime(REPO).requested_hardware=='zero-a10g'
    # Deduplicate unchanged allowlisted files between phase commits.
    state_file = OUT/'published-hashes.json'
    previous = json.loads(state_file.read_text()) if state_file.exists() else {}
    hashes = {name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
    hashes.update({name:hashlib.sha256(value).hexdigest() for name,value in raw.items()})
    operations = [CommitOperationAdd(path_in_repo=name,path_or_fileobj=path.read_bytes() if path.suffix in ('.py','.js','.json','.md','.html','.css','.svg') else path)
                  for name,path in files.items() if previous.get(name)!=hashes[name]]
    operations += [CommitOperationAdd(path_in_repo=name,path_or_fileobj=value)
                   for name,value in raw.items() if previous.get(name)!=hashes[name]]
    commit = api.create_commit(repo_id=REPO,repo_type='space',operations=operations,
        parent_commit=before.sha,commit_message=f'DefectRAG phase {args.phase}: incremental real-model application migration')
    state_file.write_text(json.dumps(hashes,indent=2))
    receipt = {'phase':args.phase,'commit':commit.oid,'parent':before.sha,'changed_files':len(operations),'manifest':hashes}
    (OUT/f'publish-phase{args.phase}.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({key:value for key,value in receipt.items() if key!='manifest'}))


if __name__=='__main__':
    main()
