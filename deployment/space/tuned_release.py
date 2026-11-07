"""Publish the fine-tuned DINOv2 profile (dinov2_tuned_v1) to the Hugging Face Space in ONE commit.

    python -m deployment.space.tuned_release --dry-run             # read-only: shows exactly what would change
    python -m deployment.space.tuned_release --stage DIR            # builds the patched Space tree in DIR and boots it
    python -m deployment.space.tuned_release --publish              # uploads data + patched code in one commit
    python -m deployment.space.tuned_release --rollback             # restores the saved live code files in one commit

Why this is separate from publish.py: the live Space runs older backend code than this repository (it predates the
backend refactor), so uploading the local files over it would change more than this release. Instead the few live
files that must change are patched with exact-text replacements: each replacement must match the live text exactly
once, otherwise the release stops. The model files are new, so code and data go up together; the previous profile's
files stay on the Space and DEFECTRAG_SPACE_PROFILE=dinov2_highres_v1 selects them again.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "Wizzas/DefectRAG"
OUT = ROOT / "development-support/space"
CATEGORIES = (
    "pcb1",
    "capsules",
    "cashew",
    "candle",
    "chewinggum",
    "fryum",
    "macaroni1",
    "macaroni2",
    "pcb2",
    "pcb3",
    "pcb4",
    "pipe_fryum",
)
PATCHED = ("backend/calibration.py", "backend/highres.py", "backend/main.py", "deployment/space/app.py", "README.md")
LOCAL_MODEL_FILES = (
    [f"models/highres_tuned/{c}.{e}" for c in CATEGORIES for e in ("npz", "json")]
    + ["models/highres_tuned/PROFILE.json"]
    + [
        f"models/encoder_dinov2_tuned/{n}"
        for n in (
            "model.safetensors",
            "config.json",
            "preprocessor_config.json",
            "LICENSE",
            "README.md",
            "ASSET_RECEIPT.json",
        )
    ]
    + ["results/tuned_deployment_evaluation.json"]
)


def lf(data):
    return data.replace(b"\r\n", b"\n")


def once(text, old, new, where):
    if text.count(old) != 1:
        raise SystemExit(
            f"{where}: the live text changed (expected one match of {old[:70]!r}); review before releasing"
        )
    return text.replace(old, new)


def between(text, start, end=None):
    first = text.index(start)
    return text[first : text.index(end, first) if end else len(text)]


def patch(live):
    """Return the patched text of every live file that must change; `live` maps path -> live text (LF)."""
    local_calibration = (ROOT / "backend/calibration.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    local_highres = (ROOT / "backend/highres.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    constants = between(local_calibration, "TUNED_POLICY =", "\n\n\n") + "\n"
    function = between(local_calibration, "def tuned_card")
    profiles = between(local_highres, "PROFILES = {", "class HighResolutionDetector:").rstrip("\n") + "\n"
    out = {}

    text = live["backend/calibration.py"]
    if "tuned_card" in text:
        raise SystemExit("backend/calibration.py: already patched on the Space")
    out["backend/calibration.py"] = text.rstrip("\n") + "\n\n\n" + constants + "\n\n" + function.rstrip("\n") + "\n"

    text = live["backend/highres.py"]
    if "PROFILES" in text:
        raise SystemExit("backend/highres.py: already patched on the Space")
    text = once(
        text,
        "from .calibration import calibrated_card\n",
        "from .calibration import calibrated_card, tuned_card\n",
        "backend/highres.py",
    )
    out["backend/highres.py"] = text.rstrip("\n") + "\n\n\n" + profiles

    text = live["backend/main.py"]
    text = once(
        text,
        "        active=getattr(detector,'profile_name','legacy')=='dinov2_highres_v1'\n"
        "        path=settings.root/'results'/('highres_deployment_evaluation.json' if active else 'evaluation.json')\n",
        "        name=getattr(detector,'profile_name','legacy')\n"
        "        active=name=='dinov2_highres_v1'\n"
        "        tuned=name=='dinov2_tuned_v1'\n"
        "        path=settings.root/'results'/('tuned_deployment_evaluation.json' if tuned else 'highres_deployment_evaluation.json' if active else 'evaluation.json')\n",
        "backend/main.py",
    )
    out["backend/main.py"] = once(
        text,
        "        if profile.exists() and not active:result['serving_profile']",
        "        if profile.exists() and not (active or tuned):result['serving_profile']",
        "backend/main.py",
    )

    text = live["deployment/space/app.py"]
    text = once(
        text,
        "from backend.calibration import calibrated_card\n"
        "from backend.highres import HighResolutionEncoder, foreground_mask, score_tokens, restore_map\n",
        "from backend.highres import HighResolutionEncoder, PROFILES, foreground_mask, profile_card, score_tokens, restore_map\n",
        "deployment/space/app.py",
    )
    text = once(
        text,
        "CARDS = {category: calibrated_card(ROOT,json.loads((ROOT/f'models/highres/{category}.json').read_text())) for category in CATEGORIES}\n"
        "ENCODER = HighResolutionEncoder(ROOT/'models/encoder_dinov2', device='cpu')\n"
        "encoder_digest = sha256(ROOT/'models/encoder_dinov2/model.safetensors')\n",
        "# The fine-tuned encoder with coreset banks is the default; DEFECTRAG_SPACE_PROFILE=dinov2_highres_v1 restores the\n"
        "# previous frozen-encoder profile (its files stay in the Space).\n"
        "PROFILE = os.getenv('DEFECTRAG_SPACE_PROFILE', 'dinov2_tuned_v1')\n"
        "assert PROFILE in PROFILES, 'Unknown detector profile'\n"
        "BANK_DIRECTORY = ROOT/PROFILES[PROFILE]['directory']\n"
        "ENCODER_DIRECTORY = ROOT/PROFILES[PROFILE]['encoder']\n"
        "CARDS = {category: profile_card(ROOT,PROFILE,json.loads((BANK_DIRECTORY/f'{category}.json').read_text())) for category in CATEGORIES}\n"
        "ENCODER = HighResolutionEncoder(ENCODER_DIRECTORY, device='cpu')\n"
        "encoder_digest = sha256(ENCODER_DIRECTORY/'model.safetensors')\n",
        "deployment/space/app.py",
    )
    text = once(
        text,
        "    file = ROOT/f'models/highres/{category}.npz'\n",
        "    file = BANK_DIRECTORY/f'{category}.npz'\n",
        "deployment/space/app.py",
    )
    text = once(
        text,
        "    profile_name = 'dinov2_highres_v1'\n    def cards",
        "    profile_name = PROFILE\n    def cards",
        "deployment/space/app.py",
    )
    out["deployment/space/app.py"] = once(
        text,
        "profile='dinov2_highres_v1',calibration=card['calibration']",
        "profile=PROFILE,calibration=card['calibration']",
        "deployment/space/app.py",
    )

    text = live["README.md"]
    old = (
        "Existing React UI, real frozen DINOv2 inspection across all 12 VisA categories,\n"
        "original normal-reference banks and heatmaps, with versioned normal-only decision\n"
        "calibration. No training rerun. The q95 sensitivity policy trades more false\n"
        "alarms for higher recall; Macaroni1/2 use the more sensitive q80 decision policy.\n"
    )
    new = (
        "Existing React UI, real DINOv2 inspection across all 12 VisA categories with an\n"
        "encoder fine-tuned on synthetic defects, 32,768-patch coreset normal-reference banks\n"
        "and heatmaps, and normal-only decision thresholds. The q95 sensitivity policy trades\n"
        "more false alarms for higher recall; Macaroni1/2 use the more sensitive q80 policy.\n"
    )
    out["README.md"] = once(text, old, new, "README.md")
    for name, source in out.items():
        compile(source, name, "exec") if name.endswith(".py") else None
    return out


def verify_local_files():
    """The new model files must be exactly what the cards and the manifest say."""
    sys.path.insert(0, str(ROOT))
    from backend.calibration import tuned_card
    from backend.vision import sha256

    for relative in LOCAL_MODEL_FILES:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"Missing local file: {relative}")
    encoder = sha256(ROOT / "models/encoder_dinov2_tuned/model.safetensors")
    for category in CATEGORIES:
        card = json.loads((ROOT / f"models/highres_tuned/{category}.json").read_text(encoding="utf-8"))
        assert sha256(ROOT / f"models/highres_tuned/{category}.npz") == card["bank_sha256"], category
        assert card["encoder_sha256"] == encoder, category
        tuned_card(ROOT, card)
    assert json.loads((ROOT / "models/highres_tuned/PROFILE.json").read_text(encoding="utf-8"))["status"] == "active"


def live_snapshot(api, sha):
    from huggingface_hub import hf_hub_download

    names = set(api.list_repo_files(REPO, repo_type="space", revision=sha))
    live = {
        name: lf(Path(hf_hub_download(REPO, name, repo_type="space", revision=sha)).read_bytes()).decode("utf-8")
        for name in PATCHED
    }
    return names, live


def plan(api):
    before = api.space_info(REPO)
    runtime = api.get_space_runtime(REPO)
    if runtime.requested_hardware != "zero-a10g":
        raise SystemExit("The Space is not on the expected zero-a10g hardware")
    names, live = live_snapshot(api, before.sha)
    if any("tuned" in n for n in names):
        raise SystemExit("The Space already holds tuned files; inspect it before releasing again")
    verify_local_files()
    patched = patch(live)
    return before, live, patched


def build_operations(patched):
    from huggingface_hub import CommitOperationAdd

    operations = [
        CommitOperationAdd(path_in_repo=name, path_or_fileobj=text.encode("utf-8")) for name, text in patched.items()
    ]
    for relative in LOCAL_MODEL_FILES:
        path = ROOT / relative
        operations.append(
            CommitOperationAdd(
                path_in_repo=relative,
                path_or_fileobj=lf(path.read_bytes())
                if path.suffix in (".json", ".md") or path.name == "LICENSE"
                else str(path),
            )
        )
    return operations


def stage(api, directory):
    """Rebuild the Space's file tree from the live snapshot plus this release, then boot its model-loading path."""
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
            "knowledge/*",
            "app.py",
        ],
    )
    for name, text in patched.items():
        if name != "README.md":
            (target / name).write_bytes(text.encode("utf-8"))
    for relative in LOCAL_MODEL_FILES:
        (target / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target / relative)
    probe = (
        "import sys,types,json\n"
        "from pathlib import Path\n"
        "sys.modules['spaces']=types.SimpleNamespace(GPU=lambda *a,**k:(lambda f:f))\n"
        "sys.modules['gradio']=types.SimpleNamespace(Server=object)\n"
        "src=Path('deployment/space/app.py').read_text(encoding='utf-8')\n"
        "ns={'__file__':str(Path('deployment/space/app.py').resolve()),'__name__':'staged'}\n"
        "exec(compile(src[:src.index('@spaces.GPU')],'deployment/space/app.py','exec'),ns)\n"
        "assert ns['PROFILE']=='dinov2_tuned_v1' and len(ns['CARDS'])==12 and len(ns['BANKS'])==12\n"
        "from backend.config import Settings\n"
        "from backend.main import create_app\n"
        "from fastapi.testclient import TestClient\n"
        "class Meta:\n"
        "    profile_name=ns['PROFILE']\n"
        "    def cards(self): return list(ns['CARDS'].values())\n"
        "import tempfile\n"
        "app=create_app(Settings(root=Path('.').resolve(),data=Path(tempfile.mkdtemp())),detector=Meta(),workflow=object())\n"
        "with TestClient(app) as client:\n"
        "    data=client.get('/api/evaluation').json()['data']\n"
        "    models=client.get('/api/models').json()['data']\n"
        "assert data['profile']=='dinov2_tuned_v1' and data['decision_policy']=='tuned-normal-quantile-v1', data.get('profile')\n"
        "assert len(models)==12 and all(m['model_id'].startswith('dinov2-tuned-') for m in models)\n"
        "print('STAGED BOOT OK:', ns['PROFILE'], '| evaluation', data['profile'], round(data['macro_mean']['image_auroc'],4))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=600,
        env={**__import__("os").environ, "DEFECTRAG_SPACE_RUNTIME": str(target / "runtime"), "PYTHONPATH": str(target)},
    )
    print(result.stdout.strip() or result.stderr.strip()[-1500:])
    if result.returncode:
        raise SystemExit("The staged Space tree did not boot; nothing was uploaded")


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
        receipt = json.loads((OUT / "publish-tuned.json").read_text())
        folder = Path(receipt["rollback_directory"])
        operations = [
            CommitOperationAdd(path_in_repo=name, path_or_fileobj=(folder / name).read_bytes()) for name in PATCHED
        ]
        before = api.space_info(REPO)
        commit = api.create_commit(
            repo_id=REPO,
            repo_type="space",
            operations=operations,
            parent_commit=before.sha,
            commit_message="Restore the code files from before the fine-tuned profile release",
        )
        print(json.dumps({"rollback_commit": commit.oid, "restored": list(PATCHED)}))
        return
    if args.stage:
        stage(api, args.stage)
        return
    before, live, patched = plan(api)
    summary = {
        "parent": before.sha,
        "patched_live_files": list(patched),
        "new_files": len(LOCAL_MODEL_FILES),
        "new_megabytes": round(sum((ROOT / f).stat().st_size for f in LOCAL_MODEL_FILES) / 1e6, 1),
    }
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return
    rollback = OUT / f"tuned-rollback-{before.sha[:12]}"
    for name, text in live.items():
        (rollback / name).parent.mkdir(parents=True, exist_ok=True)
        (rollback / name).write_bytes(text.encode("utf-8"))
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="space",
        operations=build_operations(patched),
        parent_commit=before.sha,
        commit_message="Fine-tuned DINOv2 detector profile (dinov2_tuned_v1): coreset banks, thresholds from held-out normals",
    )
    receipt = {
        **summary,
        "commit": commit.oid,
        "rollback_directory": str(rollback),
        "hashes": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in patched.items()},
    }
    (OUT / "publish-tuned.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k != "hashes"}))


if __name__ == "__main__":
    main()
