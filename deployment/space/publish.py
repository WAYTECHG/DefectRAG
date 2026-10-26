"""Allowlisted incremental commits; no private runtime, dataset or secrets upload."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = 'Wizzas/DefectRAG'
OUT = ROOT/'development-support/space'


def checked_frontend():
    checked=subprocess.run(['node',str(ROOT/'deployment/space/frontend_release.mjs'),'check',str(OUT/'ui-dist')],
        cwd=ROOT,capture_output=True,text=True,check=False,timeout=60)
    if checked.returncode:
        raise SystemExit('Frontend release blocked: '+checked.stderr.strip())
    return json.loads(checked.stdout)


def entry_cache_headers(source):
    """Patch only the two known HTML/config responses in the installed server."""
    text=source.decode('utf-8')
    for name in ('index.html','config.js'):
        original="return FileResponse(UI/'"+name+"')"
        fixed="return FileResponse(UI/'"+name+"',headers={'Cache-Control':'no-store'})"
        if text.count(fixed)==1:continue
        if text.count(original)!=1:raise SystemExit('Live entry response changed; review it before patching')
        text=text.replace(original,fixed)
    return text.encode('utf-8')


def publish_frontend(frontend, dry_run=False, refresh_html_cache=False):
    """Publish verified browser assets only; preserve the installed server/settings."""
    from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
    api=HfApi()
    before=api.space_info(REPO)
    remote=set(api.list_repo_files(REPO,repo_type='space',revision=before.sha))
    rollback=OUT/('frontend-rollback-'+before.sha[:12])
    payloads={}
    previous_file=OUT/'publish-frontend.json'
    previous=json.loads(previous_file.read_text()) if previous_file.exists() else {}
    for name,digest in frontend['files'].items():
        payload=(OUT/'ui-dist'/name).read_bytes()
        if hashlib.sha256(payload).hexdigest()!=digest:raise SystemExit('Frontend changed before publication')
        target='frontend/dist/'+name
        if target in remote:
            # The last successful immutable commit proves these unchanged files.
            # Still verify live config explicitly; no flag changes are inferred.
            if name!='config.js' and previous.get('commit')==before.sha and previous.get('manifest',{}).get(name)==digest:continue
            original=Path(hf_hub_download(REPO,target,repo_type='space',revision=before.sha)).read_bytes()
            if name=='config.js' and original!=payload:
                raise SystemExit('Live public configuration differs; preserve/reconcile it before publishing')
            if original==payload:continue
            if not dry_run:
                saved=rollback/name
                saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(original)
        payloads[target]=payload
    if refresh_html_cache:
        target='deployment/space/app.py'
        original=Path(hf_hub_download(REPO,target,repo_type='space',revision=before.sha)).read_bytes()
        patched=entry_cache_headers(original)
        if patched!=original:
            payloads[target]=patched
            if not dry_run:
                saved=rollback/'server-entry-cache.py'
                saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(original)
    summary={'source_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'parent':before.sha,'frontend_only':not refresh_html_cache,'entry_cache_headers_only_server_patch':refresh_html_cache,
             'changed_files':list(payloads),'dry_run':dry_run}
    if dry_run:
        print(json.dumps(summary));return
    if checked_frontend()!=frontend:raise SystemExit('Frontend inputs changed before publication')
    if not payloads:
        print(json.dumps({**summary,'commit':before.sha,'already_current':True}));return
    commit=api.create_commit(repo_id=REPO,repo_type='space',parent_commit=before.sha,
        operations=[CommitOperationAdd(path_in_repo=name,path_or_fileobj=value) for name,value in payloads.items()],
        commit_message=('Add optional dashboard tutorial and refresh entry cache headers'
                        if refresh_html_cache else 'Update verified React dashboard'))
    receipt={**summary,'commit':commit.oid,'rollback_directory':str(rollback),'manifest':frontend['files']}
    (OUT/'publish-frontend.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({k:v for k,v in receipt.items() if k!='manifest'}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=int, choices=(2,3,4,5))
    parser.add_argument('--check-frontend',action='store_true',help='Offline readiness check only; never contacts Hugging Face')
    parser.add_argument('--frontend-only',action='store_true',help='Publish only verified frontend files; preserve server and settings')
    parser.add_argument('--dry-run',action='store_true',help='Read-only frontend release plan; no upload')
    parser.add_argument('--refresh-html-cache',action='store_true',help='With --frontend-only, patch only live HTML/config no-store headers')
    args = parser.parse_args()
    frontend=checked_frontend()
    if args.check_frontend:
        print(json.dumps({'verified':True,'files':len(frontend['files']),'source_fingerprint':frontend['source_fingerprint']}))
        return
    if args.frontend_only:
        publish_frontend(frontend,args.dry_run,args.refresh_html_cache)
        return
    if args.refresh_html_cache:parser.error('--refresh-html-cache requires --frontend-only')
    if args.dry_run:parser.error('--dry-run requires --frontend-only')
    if args.phase is None:parser.error('--phase is required for an authorized deployment')
    from huggingface_hub import HfApi, CommitOperationAdd
    if args.phase>=4:
        confirmation=OUT/'migration-confirmed.json'
        assert confirmation.exists() and json.loads(confirmation.read_text()).get('user_confirmed_manual_execution'), 'Wait for the user to confirm manual SQL execution before enabling staff persistence.'
        from deployment.space.supabase_repository import read_public_config
        read_public_config(OUT/'ui-dist/config.js')  # Refuse a blank example before changing a working Space.
    files = {}
    for relative in ('docs/THIRD_PARTY_NOTICES.md','docs/FRONTEND_LICENSES.txt','models/BGE-LICENSE.txt'):
        path=ROOT/relative
        if path.exists():
            files[relative]=path
    for relative in ('results/sensitive_deployment_evaluation.json','results/macaroni_recall_deployment_evaluation.json'):
        files[relative]=ROOT/relative
    for directory in ('backend','deployment/space'):
        for path in (ROOT/directory).glob('*.py'):
            files[path.relative_to(ROOT).as_posix()] = path
    for name in frontend['files']:
        files['frontend/dist/'+name] = OUT/'ui-dist'/name
    frontend_bytes={name:files['frontend/dist/'+name].read_bytes() for name in frontend['files']}
    if any(hashlib.sha256(content).hexdigest()!=frontend['files'][name] for name,content in frontend_bytes.items()):
        raise SystemExit('Frontend changed while assembling release')
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
alarms for higher recall; Macaroni1/2 use the more sensitive q80 decision policy.
Historical inspection decisions are preserved.
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
    operations = [CommitOperationAdd(path_in_repo=name,path_or_fileobj=frontend_bytes[name.removeprefix('frontend/dist/')] if name.startswith('frontend/dist/')
                  else path.read_bytes() if path.suffix in ('.py','.js','.json','.md','.html','.css','.svg') else path)
                  for name,path in files.items() if previous.get(name)!=hashes[name]]
    operations += [CommitOperationAdd(path_in_repo=name,path_or_fileobj=value)
                   for name,value in raw.items() if previous.get(name)!=hashes[name]]
    if checked_frontend()!=frontend:raise SystemExit('Frontend inputs changed before publication; rebuild and verify')
    commit = api.create_commit(repo_id=REPO,repo_type='space',operations=operations,
        parent_commit=before.sha,commit_message=f'DefectRAG phase {args.phase}: incremental real-model application migration')
    state_file.write_text(json.dumps(hashes,indent=2))
    receipt = {'phase':args.phase,'commit':commit.oid,'parent':before.sha,'changed_files':len(operations),'manifest':hashes}
    (OUT/f'publish-phase{args.phase}.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({key:value for key,value in receipt.items() if key!='manifest'}))


if __name__=='__main__':
    main()
