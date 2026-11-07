"""Serve the MVTec AD summary from the Space's Official benchmark route (backend + data, one commit).

    python -m deployment.space.mvtec_release --dry-run     # read-only: shows what would change
    python -m deployment.space.mvtec_release --stage DIR   # rebuilds the patched Space tree in DIR and checks the route
    python -m deployment.space.mvtec_release --publish     # one commit: patched backend/main.py + results/mvtec_summary.json
    python -m deployment.space.mvtec_release --rollback    # restores the saved backend/main.py and removes the data file

The change is additive: the route gains a "mvtec" key when results/mvtec_summary.json exists, so the old frontend keeps
working. Publish the new dashboard screens afterwards with deployment.space.publish --frontend-only. The live
backend/main.py is patched with one exact-text replacement that must match once, as in the earlier releases.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from deployment.space.tuned_release import OUT, REPO, ROOT, lf, once

DATA = "results/mvtec_summary.json"
TARGET = "backend/main.py"
OLD = "        if candidate_source.exists():report['candidate']=json.loads(candidate_source.read_text())\n        return {'data':report}\n"
NEW = (
    "        if candidate_source.exists():report['candidate']=json.loads(candidate_source.read_text())\n"
    "        mvtec=settings.root/'results/mvtec_summary.json'\n"
    "        if mvtec.exists():report['mvtec']=json.loads(mvtec.read_text())\n"
    "        return {'data':report}\n"
)
PROBE = (
    "import sys,tempfile\n"
    "from pathlib import Path\n"
    "from backend.config import Settings\n"
    "from backend.main import create_app\n"
    "from fastapi.testclient import TestClient\n"
    "class Meta:\n"
    "    profile_name='dinov2_tuned_v1'\n"
    "    def cards(self): return []\n"
    "app=create_app(Settings(root=Path('.').resolve(),data=Path(tempfile.mkdtemp())),detector=Meta(),workflow=object())\n"
    "with TestClient(app) as client:\n"
    "    data=client.get('/api/benchmark/official').json()['data']\n"
    "assert data['mvtec']['products']==15 and len(data['mvtec']['categories'])==15, 'mvtec summary missing'\n"
    "assert 'candidate' in data\n"
    "print('STAGED ROUTE OK: mvtec products', data['mvtec']['products'], '| candidate present')\n"
)


def plan(api):
    from huggingface_hub import hf_hub_download

    before = api.space_info(REPO)
    if api.get_space_runtime(REPO).requested_hardware != "zero-a10g":
        raise SystemExit("The Space is not on the expected zero-a10g hardware")
    live = lf(Path(hf_hub_download(REPO, TARGET, repo_type="space", revision=before.sha)).read_bytes()).decode("utf-8")
    if "mvtec_summary" in live:
        raise SystemExit("The Space already serves the MVTec summary")
    patched = once(live, OLD, NEW, TARGET)
    compile(patched, TARGET, "exec")
    summary = json.loads((ROOT / DATA).read_text(encoding="utf-8"))
    assert summary["products"] == 15 and summary["test_images"] == 1725, "unexpected summary"
    return before, live, patched, lf((ROOT / DATA).read_bytes())


def stage(api, directory):
    from huggingface_hub import snapshot_download

    before, _, patched, data = plan(api)
    target = Path(directory)
    if target.exists() and any(target.iterdir()):
        raise SystemExit("Choose an empty directory for staging")
    snapshot_download(
        REPO,
        repo_type="space",
        revision=before.sha,
        local_dir=target,
        allow_patterns=["backend/*", "deployment/space/*.py", "results/*.json", "knowledge/*", "app.py"],
    )
    (target / TARGET).write_bytes(patched.encode("utf-8"))
    (target / DATA).write_bytes(data)
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=300,
        env={**__import__("os").environ, "PYTHONPATH": str(target), "DEFECTRAG_FACTORY_ONLY": "1"},
    )
    print(result.stdout.strip() or result.stderr.strip()[-1500:])
    if result.returncode:
        raise SystemExit("The staged Space tree failed the route check; nothing was uploaded")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--stage", metavar="DIR")
    group.add_argument("--publish", action="store_true")
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

    api = HfApi()
    if args.rollback:
        receipt = json.loads((OUT / "publish-mvtec.json").read_text())
        saved = (Path(receipt["rollback_directory"]) / TARGET).read_bytes()
        before = api.space_info(REPO)
        commit = api.create_commit(
            repo_id=REPO,
            repo_type="space",
            operations=[
                CommitOperationAdd(path_in_repo=TARGET, path_or_fileobj=saved),
                CommitOperationDelete(path_in_repo=DATA),
            ],
            parent_commit=before.sha,
            commit_message="Remove the MVTec summary route again",
        )
        print(json.dumps({"rollback_commit": commit.oid}))
        return
    if args.stage:
        stage(api, args.stage)
        return
    before, live, patched, data = plan(api)
    summary = {"parent": before.sha, "patched_live_files": [TARGET], "new_files": [DATA]}
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return
    rollback = OUT / f"mvtec-rollback-{before.sha[:12]}"
    (rollback / TARGET).parent.mkdir(parents=True, exist_ok=True)
    (rollback / TARGET).write_bytes(live.encode("utf-8"))
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="space",
        operations=[
            CommitOperationAdd(path_in_repo=TARGET, path_or_fileobj=patched.encode("utf-8")),
            CommitOperationAdd(path_in_repo=DATA, path_or_fileobj=data),
        ],
        parent_commit=before.sha,
        commit_message="Official benchmark route also serves the MVTec AD summary",
    )
    receipt = {**summary, "commit": commit.oid, "rollback_directory": str(rollback)}
    (OUT / "publish-mvtec.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    sys.exit(main())
