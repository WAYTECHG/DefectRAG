"""Fast-forward the user's Desktop copy and verify recognized asset updates.
Preserves runtime data, secrets, earlier archives, and all existing Git history.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TARGET=Path(r'C:\Users\User\Desktop\DefectRAG-v2')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',default='DefectRAG-v2.zip')
    parser.add_argument('--bundle',default='DefectRAG-v2-release.bundle')
    parser.add_argument('--extra-archive',action='append',default=[])
    args=parser.parse_args()
    for name in [args.archive,args.bundle,*args.extra_archive]:
        if Path(name).name!=name:raise ValueError('Use artifact basenames')
    archive=ROOT.parent/args.archive
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
    baseline=json.loads((ROOT/'CHECKPOINT_MANIFEST.json').read_text())
    known={e['path']:e['sha256'] for e in baseline['files']}
    previous_manifest=TARGET/'RELEASE_MANIFEST.json'
    previous={e['path']:e['sha256'] for e in json.loads(previous_manifest.read_text())['files']} if previous_manifest.exists() else {}
    if git(ROOT,'status','--porcelain'):raise RuntimeError('Commit the source before synchronization')
    if git(TARGET,'status','--porcelain'):raise RuntimeError('Desktop edits preserved; reconcile before synchronization')
    tracked=set(git(ROOT,'ls-files').splitlines())
    # Check non-Git assets first so unrecognized changes cannot be overwritten.
    for e in manifest['files']:
        target=(TARGET/e['path']).resolve()
        if not target.is_relative_to(TARGET.resolve()):raise RuntimeError('Unsafe target')
        if e['path'] not in tracked and target.exists() and digest(target) not in {e['sha256'],known.get(e['path']),previous.get(e['path'])}:
            raise RuntimeError('Unrecognized Desktop asset preserved: '+str(target))
    git(TARGET,'fetch',str(ROOT),'main')
    git(TARGET,'merge','--ff-only','FETCH_HEAD')
    for e in manifest['files']:
        source=ROOT/e['path'];target=TARGET/e['path']
        if not target.exists() or digest(target)!=e['sha256']:
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        if digest(target)!=e['sha256']:raise RuntimeError('Copied hash mismatch: '+e['path'])
    shutil.copyfile(ROOT/'RELEASE_MANIFEST.json',TARGET/'RELEASE_MANIFEST.json')
    archives=[archive,*[ROOT.parent/name for name in args.extra_archive]]
    for source in [p for a in archives for p in (a,a.with_suffix('.receipt.json'))]:
        target=TARGET.parent/source.name
        if target.exists() and digest(target)!=digest(source):raise RuntimeError('Earlier Desktop archive preserved')
        if not target.exists():shutil.copyfile(source,target)
    bundle=ROOT/'development-support'/'git'/args.bundle
    target_bundle=TARGET/'development-support'/'git'/bundle.name
    target_bundle.parent.mkdir(parents=True,exist_ok=True)
    if target_bundle.exists() and digest(target_bundle)!=digest(bundle):raise RuntimeError('Earlier release bundle preserved')
    if not target_bundle.exists():shutil.copyfile(bundle,target_bundle)
    # Copying LF-exact release assets over a CRLF checkout may invalidate Git's
    # stat cache. Refresh only when there are no actual tracked content changes.
    git(TARGET,'-c','core.autocrlf=false','diff','--exit-code')
    git(TARGET,'-c','core.autocrlf=false','add','-u')
    if git(TARGET,'status','--porcelain'):raise RuntimeError('Desktop changes require review; files preserved')
    receipt={'status':'passed','desktop':str(TARGET),'commit':git(TARGET,'rev-parse','HEAD'),
             'verified_release_files':len(manifest['files'])+1,'archive':str(TARGET.parent/archive.name),
             'archive_sha256':digest(TARGET.parent/archive.name),'runtime_and_secrets':'preserved; not copied',
             'git_history':'fast-forwarded without rewriting','bundle':str(target_bundle)}
    (ROOT/'development-support'/'release_sync_receipt.json').write_text(json.dumps(receipt,indent=2))
    (TARGET/'development-support'/'release_sync_receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
