"""Switch the hosted fine-tuned profile to ONE q95 rule for every product (Macaroni 1 and 2 included), in one commit.

    python -m deployment.space.tuned_thresholds --dry-run          # read-only: shows exactly what would change
    python -m deployment.space.tuned_thresholds --stage DIR        # rebuilds the patched Space tree in DIR and boots it
    python -m deployment.space.tuned_thresholds --publish          # one commit: code rule + 2 cards + manifest + README line
    python -m deployment.space.tuned_thresholds --rollback         # restores the saved previous files in one commit

The Space checks every card and the manifest against the rule in backend/calibration.py at start-up, so the rule, the two
changed cards and the manifest must change together: one commit, never separate ones. Each live text patch must match
the live file exactly once, otherwise the release stops. Banks and the encoder are not touched.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from deployment.space.tuned_release import OUT, REPO, ROOT, boot, lf, once, verify_local_files

DATA = (
    "models/highres_tuned/macaroni1.json",
    "models/highres_tuned/macaroni2.json",
    "results/tuned_deployment_evaluation.json",
)
PATCHED = ("backend/calibration.py", "README.md")
PREVIOUS = ROOT / "development-support" / "manifest-backup" / "q80-era"


def patch(live):
    out = {}
    out["backend/calibration.py"] = once(
        live["backend/calibration.py"],
        'TUNED_QUANTILES = {"macaroni1": 0.8, "macaroni2": 0.8}\n',
        "# One rule for every product (the 95th percentile of the held-out normal scores). "
        "Per-product exceptions would go here.\nTUNED_QUANTILES: dict[str, float] = {}\n",
        "backend/calibration.py",
    )
    out["README.md"] = once(
        live["README.md"],
        "more false alarms for higher recall; Macaroni1/2 use the more sensitive q80 policy.\n",
        "more false alarms for higher recall; one rule is used for every product.\n",
        "README.md",
    )
    for name, text in out.items():
        if name.endswith(".py"):
            compile(text, name, "exec")
    return out


def live_files(api, sha):
    from huggingface_hub import hf_hub_download

    names = set(api.list_repo_files(REPO, repo_type="space", revision=sha))

    def read(name):
        return lf(Path(hf_hub_download(REPO, name, repo_type="space", revision=sha)).read_bytes())

    return names, {n: read(n).decode("utf-8") for n in PATCHED}, {n: read(n) for n in DATA}


def plan(api):
    before = api.space_info(REPO)
    if api.get_space_runtime(REPO).requested_hardware != "zero-a10g":
        raise SystemExit("The Space is not on the expected zero-a10g hardware")
    names, live, live_data = live_files(api, before.sha)
    if not all(n in names for n in DATA):
        raise SystemExit("The tuned profile files are not on the Space yet; run deployment.space.tuned_release first")
    verify_local_files()
    for name in DATA:  # the live data must be exactly what this change replaces
        previous = lf((PREVIOUS / Path(name).name).read_bytes())
        if live_data[name] != previous:
            raise SystemExit(f"{name}: the live file is not the version this update expects; review before changing it")
    new_data = {n: lf((ROOT / n).read_bytes()) for n in DATA}
    for category in ("macaroni1", "macaroni2"):
        card = json.loads(new_data[f"models/highres_tuned/{category}.json"])
        assert card["calibration"]["quantile"] == 0.95, category
    return before, live, patch(live), new_data


def operations(patched, new_data):
    from huggingface_hub import CommitOperationAdd

    ops = [CommitOperationAdd(path_in_repo=n, path_or_fileobj=t.encode("utf-8")) for n, t in patched.items()]
    ops += [CommitOperationAdd(path_in_repo=n, path_or_fileobj=b) for n, b in new_data.items()]
    return ops


def stage(api, directory):
    from huggingface_hub import snapshot_download

    before, _, patched, new_data = plan(api)
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
    for name, text in patched.items():
        if name != "README.md":
            (target / name).write_bytes(text.encode("utf-8"))
    for name, data in new_data.items():
        (target / name).write_bytes(data)
    boot(target)
    for category in ("macaroni1", "macaroni2"):
        card = json.loads((target / f"models/highres_tuned/{category}.json").read_text(encoding="utf-8"))
        print(f"  staged {category}: quantile {card['calibration']['quantile']}, threshold {card['threshold']:.4f}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--stage", metavar="DIR")
    group.add_argument("--publish", action="store_true")
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    if args.rollback:
        receipt = json.loads((OUT / "publish-thresholds.json").read_text())
        folder = Path(receipt["rollback_directory"])
        ops = [CommitOperationAdd(path_in_repo=n, path_or_fileobj=(folder / n).read_bytes()) for n in (*PATCHED, *DATA)]
        before = api.space_info(REPO)
        commit = api.create_commit(
            repo_id=REPO,
            repo_type="space",
            operations=ops,
            parent_commit=before.sha,
            commit_message="Restore the macaroni thresholds from before the one-rule update",
        )
        print(json.dumps({"rollback_commit": commit.oid, "restored": [*PATCHED, *DATA]}))
        return
    if args.stage:
        stage(api, args.stage)
        return
    before, live, patched, new_data = plan(api)
    summary = {"parent": before.sha, "patched_live_files": list(patched), "replaced_data_files": list(new_data)}
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return
    rollback = OUT / f"thresholds-rollback-{before.sha[:12]}"
    live_all = {**live, **{n: lf((PREVIOUS / Path(n).name).read_bytes()).decode("utf-8") for n in DATA}}
    for name, text in live_all.items():
        (rollback / name).parent.mkdir(parents=True, exist_ok=True)
        (rollback / name).write_bytes(text.encode("utf-8"))
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="space",
        operations=operations(patched, new_data),
        parent_commit=before.sha,
        commit_message="One q95 rule for every product: Macaroni 1 and 2 no longer use the more sensitive limit",
    )
    receipt = {
        **summary,
        "commit": commit.oid,
        "rollback_directory": str(rollback),
        "hashes": {
            n: hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
            for n, b in {**patched, **new_data}.items()
        },
    }
    (OUT / "publish-thresholds.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k != "hashes"}))


if __name__ == "__main__":
    sys.exit(main())
