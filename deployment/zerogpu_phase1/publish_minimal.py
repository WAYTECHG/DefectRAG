"""Publish only the approved compatibility proof to the verified empty Space."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SUPPORT = ROOT / 'development-support/zerogpu-phase1'


def copy(source, destination, staging):
    target = staging / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    staging = SUPPORT / 'space-payload'
    staging.mkdir(exist_ok=False)
    local = json.loads((ROOT / 'runtime/zerogpu-phase1/last-genuine-inspection.json').read_text())
    assert local['phase1']['transport'] == '@gradio/client' and local['device'] == 'cuda'
    copy(HERE / 'SPACE_README.md', 'README.md', staging)
    copy(HERE / 'requirements-space.txt', 'requirements.txt', staging)
    copy(HERE / 'app.py', 'deployment/zerogpu_phase1/app.py', staging)
    for source in (ROOT / 'backend').glob('*.py'):
        copy(source, 'backend/' + source.name, staging)
    for source in (ROOT / 'knowledge').glob('*.md'):
        copy(source, 'knowledge/' + source.name, staging)
    copy(ROOT / 'knowledge/sources.json', 'knowledge/sources.json', staging)
    for source in (ROOT / 'samples').glob('*.jpg'):
        copy(source, 'samples/' + source.name, staging)
    for source in (ROOT / 'models/highres').glob('*.json'):
        copy(source, 'models/highres/' + source.name, staging)
    copy(ROOT / 'models/highres/pcb1.npz', 'models/highres/pcb1.npz', staging)
    for name in ('config.json', 'model.safetensors', 'ASSET_RECEIPT.json', 'LICENSE'):
        source = ROOT / 'models/encoder_dinov2' / name
        if source.exists():
            copy(source, 'models/encoder_dinov2/' + name, staging)
    (staging / 'models/embedding').mkdir()
    (staging / 'models/embedding/PHASE1_ONLY.txt').write_text('No embeddings or generation deployed; RAG endpoints disabled in Phase 1.')
    for name in ('evaluation.json', 'official_evaluation.json', 'highres_evaluation.json',
                 'highres_deployment_evaluation.json'):
        copy(ROOT / 'results' / name, 'results/' + name, staging)
    copy(ROOT / 'LICENSE', 'LICENSE', staging)
    copy(ROOT / 'docs/THIRD_PARTY_NOTICES.md', 'docs/THIRD_PARTY_NOTICES.md', staging)
    ui = SUPPORT / 'ui-dist'
    for source in ui.rglob('*'):
        if source.is_file() and source.name != 'PHASE1_BUILD.json':
            copy(source, 'frontend/dist/' + source.relative_to(ui).as_posix(), staging)
    (staging / 'app.py').write_text(
        "import os\nfrom pathlib import Path\n"
        "os.environ['DEFECTRAG_PHASE1_UI']=str(Path(__file__).parent/'frontend/dist')\n"
        "os.environ['GRADIO_ANALYTICS_ENABLED']='False'\n"
        "from deployment.zerogpu_phase1.app import server\n"
        "server.launch(server_name='0.0.0.0',server_port=7860,show_error=True)\n")
    manifest = {p.relative_to(staging).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in staging.rglob('*') if p.is_file()}
    assert not any(part in {'.env', '.git', '.venv', 'runtime', 'legacy-projects', 'node_modules'}
                   for name in manifest for part in Path(name).parts)
    config = (staging / 'frontend/dist/config.js').read_text()
    assert "supabaseUrl: ''" in config and "supabasePublishableKey: ''" in config
    receipt = {'status': 'staged', 'repo': 'Wizzas/DefectRAG', 'files': manifest,
               'bytes': sum(p.stat().st_size for p in staging.rglob('*') if p.is_file()),
               'private_history_config_and_qwen_excluded': True}
    if args.publish:
        api = HfApi()
        before = api.space_info(receipt['repo'])
        existing = set(api.list_repo_files(receipt['repo'], repo_type='space'))
        assert existing <= {'.gitattributes', 'README.md'}, 'Space is no longer empty; do not overwrite it'
        assert api.get_space_runtime(receipt['repo']).requested_hardware == 'zero-a10g'
        result = api.upload_folder(repo_id=receipt['repo'], repo_type='space', folder_path=staging,
                                   parent_commit=before.sha,
                                   commit_message='Phase 1 only: preserved React and genuine DINOv2 compatibility test')
        receipt.update(status='uploaded', commit=result.oid, url='https://huggingface.co/spaces/' + receipt['repo'])
    (SUPPORT / 'space-upload.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
