"""Add the nearest-normal-photo index to the Space (backend + data, one commit; the thumbnails ship with the screens).

    python -m deployment.space.references_release --dry-run     # read-only: shows what would change
    python -m deployment.space.references_release --stage DIR   # rebuilds the patched Space tree in DIR, boots it, queries the index
    python -m deployment.space.references_release --publish    # one commit: patched app.py + backend/references.py + 12 index files
    python -m deployment.space.references_release --rollback    # restores the saved app.py and removes the new files

The change is additive: results gain a "references" list (ids and similarities); detection is untouched. Publish the new
screens afterwards with deployment.space.publish --frontend-only (the thumbnails are in frontend/public/assets/references).
The live deployment/space/app.py is patched with exact-text replacements that must each match once.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from deployment.space.tuned_release import CATEGORIES, OUT, REPO, ROOT, boot, lf, once

TARGET = "deployment/space/app.py"
NEW_FILES = ["backend/references.py"] + [f"models/highres_tuned/references/{c}.npz" for c in CATEGORIES]
PROBE = (
    "import sys\n"
    "import numpy as np\n"
    "import torch\n"
    "from pathlib import Path\n"
    "from backend.references import ReferenceIndex\n"
    "index=ReferenceIndex(Path('models/highres_tuned/references'))\n"
    "tokens=torch.randn(64,384)\n"
    "found=index.nearest('pcb1',tokens,np.ones(64,dtype=bool))\n"
    "assert len(found)==3 and all(r['id'].startswith('pcb1/') for r in found), found\n"
    "assert index.nearest('not_a_product',tokens,np.ones(64,dtype=bool))==[]\n"
    "print('STAGED INDEX OK:', found[0]['id'], round(found[0]['similarity'],3))\n"
)


def patch(live):
    text = once(
        live,
        "from backend.storage import now\n",
        "from backend.storage import now\nfrom backend.references import ReferenceIndex\n",
        TARGET,
    )
    text = once(
        text,
        ".to(DEVICE)\n\n\n@spaces.GPU(duration=20)\n",
        ".to(DEVICE)\n"
        "# Nearest normal reference photos (an explanation aid only; the score and verdict never use it).\n"
        "REFERENCES = ReferenceIndex(BANK_DIRECTORY/'references') if PROFILE == 'dinov2_tuned_v1' else None\n\n\n"
        "@spaces.GPU(duration=20)\n",
        TARGET,
    )
    text = once(
        text,
        "    return {'raw': raw, 'geometry': geometry, 'score': score,\n",
        "    references = REFERENCES.nearest(category, tokens, mask) if REFERENCES is not None else []\n"
        "    return {'raw': raw, 'geometry': geometry, 'score': score, 'references': references,\n",
        TARGET,
    )
    text = once(
        text,
        "    record = {key:output[key] for key in ('inference_ms','device','gpu_name','peak_gpu_mb','foreground_fraction')}\n",
        "    record = {key:output[key] for key in ('inference_ms','device','gpu_name','peak_gpu_mb','foreground_fraction')}\n"
        "    if output.get('references'):record['references']=output['references']\n",
        TARGET,
    )
    compile(text, TARGET, "exec")
    return text


def plan(api):
    from huggingface_hub import hf_hub_download

    before = api.space_info(REPO)
    if api.get_space_runtime(REPO).requested_hardware != "zero-a10g":
        raise SystemExit("The Space is not on the expected zero-a10g hardware")
    live = lf(Path(hf_hub_download(REPO, TARGET, repo_type="space", revision=before.sha)).read_bytes()).decode("utf-8")
    if "ReferenceIndex" in live:
        raise SystemExit("The Space already has the reference index")
    for name in NEW_FILES:
        if not (ROOT / name).is_file():
            raise SystemExit(f"Missing local file: {name}")
    return before, live, patch(live)


def stage(api, directory):
    from huggingface_hub import snapshot_download

    before, _, patched = plan(api)
    target = Path(directory)
    if target.exists() and any(target.iterdir()):
        raise SystemExit("Choose an empty directory for staging")
    snapshot_download(
        REPO,
        repo_type="space",
        revision=before.sha,
        local_dir=target,
        allow_patterns=[
            "backend/*",
            "deployment/space/*.py",
            "results/*.json",
            "models/highres/*.json",
            "models/highres_tuned/*",
            "models/encoder_dinov2_tuned/*",
            "knowledge/*",
            "app.py",
        ],
    )
    (target / TARGET).write_bytes(patched.encode("utf-8"))
    for name in NEW_FILES:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes((ROOT / name).read_bytes())
    boot(target)
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=300,
        env={**__import__("os").environ, "PYTHONPATH": str(target)},
    )
    print(result.stdout.strip() or result.stderr.strip()[-1500:])
    if result.returncode:
        raise SystemExit("The staged Space tree failed the index check; nothing was uploaded")


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
        receipt = json.loads((OUT / "publish-references.json").read_text())
        saved = (Path(receipt["rollback_directory"]) / TARGET).read_bytes()
        before = api.space_info(REPO)
        operations = [CommitOperationAdd(path_in_repo=TARGET, path_or_fileobj=saved)]
        operations += [CommitOperationDelete(path_in_repo=name) for name in NEW_FILES]
        commit = api.create_commit(
            repo_id=REPO,
            repo_type="space",
            operations=operations,
            parent_commit=before.sha,
            commit_message="Remove the nearest normal photo index again",
        )
        print(json.dumps({"rollback_commit": commit.oid}))
        return
    if args.stage:
        stage(api, args.stage)
        return
    before, live, patched = plan(api)
    summary = {"parent": before.sha, "patched_live_files": [TARGET], "new_files": len(NEW_FILES)}
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return
    rollback = OUT / f"references-rollback-{before.sha[:12]}"
    (rollback / TARGET).parent.mkdir(parents=True, exist_ok=True)
    (rollback / TARGET).write_bytes(live.encode("utf-8"))
    operations = [CommitOperationAdd(path_in_repo=TARGET, path_or_fileobj=patched.encode("utf-8"))]
    for name in NEW_FILES:
        path = ROOT / name
        data = lf(path.read_bytes()) if path.suffix == ".py" else str(path)
        operations.append(CommitOperationAdd(path_in_repo=name, path_or_fileobj=data))
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="space",
        operations=operations,
        parent_commit=before.sha,
        commit_message="Inspection results name the closest normal reference photos (explanation only)",
    )
    receipt = {**summary, "commit": commit.oid, "rollback_directory": str(rollback)}
    (OUT / "publish-references.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    sys.exit(main())
