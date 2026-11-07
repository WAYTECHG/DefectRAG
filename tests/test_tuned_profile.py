"""The fine-tuned DINOv2 profile: selection, rollback, manifest guards and the policy of its thresholds."""

import json
from copy import deepcopy

import pytest

from backend.calibration import TUNED_FILENAME, TUNED_POLICY, TUNED_QUANTILES, tuned_card
from backend.config import CATEGORIES, Settings
from backend.highres import PROFILES, HighResolutionDetector, TunedDetector
from backend.vision import Detector, ModelUnavailable, create_detector


def card(category, threshold=0.1):
    quantile = TUNED_QUANTILES.get(category, 0.95)
    return {
        "category": category,
        "model_id": f"dinov2-tuned-{category}-v1",
        "profile": "dinov2_tuned_v1",
        "encoder_sha256": "e" * 64,
        "bank_sha256": "b" * 64,
        "threshold": threshold,
        "uncertainty_margin": threshold * 0.05,
        "heatmap_scale": 0.12,
        "calibration": {"normal": 90, "anomalous": 0, "policy": TUNED_POLICY, "quantile": quantile},
    }


@pytest.fixture
def installed(tmp_path):
    (tmp_path / "results").mkdir()
    manifest = {"decision_policy": TUNED_POLICY, "categories": {c: card(c) for c in CATEGORIES}}
    (tmp_path / "results" / TUNED_FILENAME).write_text(json.dumps(manifest))
    return tmp_path, manifest


def marker(root, folder, status):
    directory = root / "models" / folder
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "PROFILE.json").write_text(json.dumps({"status": status}))


def test_auto_prefers_the_active_tuned_profile_and_legacy_stays_available(tmp_path):
    marker(tmp_path, "highres", "active")
    marker(tmp_path, "highres_tuned", "active")
    assert isinstance(create_detector(Settings(root=tmp_path, profile="auto")), TunedDetector)
    assert type(create_detector(Settings(root=tmp_path, profile="dinov2_highres_v1"))) is HighResolutionDetector
    assert isinstance(create_detector(Settings(root=tmp_path, profile="legacy")), Detector)


def test_an_unvalidated_tuned_profile_never_replaces_the_working_one(tmp_path):
    marker(tmp_path, "highres", "active")
    marker(tmp_path, "highres_tuned", "pending")
    assert type(create_detector(Settings(root=tmp_path, profile="auto"))) is HighResolutionDetector
    with pytest.raises(ModelUnavailable, match="not validated"):
        create_detector(Settings(root=tmp_path, profile="dinov2_tuned_v1"))


def test_asking_for_a_missing_tuned_profile_fails_closed(tmp_path):
    with pytest.raises(ModelUnavailable, match="not installed"):
        create_detector(Settings(root=tmp_path, profile="dinov2_tuned_v1"))
    with pytest.raises(ModelUnavailable, match="Unknown"):
        create_detector(Settings(root=tmp_path, profile="dinov2_tuned_v2"))


def test_profiles_use_separate_files_so_the_previous_profile_can_be_restored():
    assert PROFILES["dinov2_tuned_v1"]["directory"] != PROFILES["dinov2_highres_v1"]["directory"]
    assert PROFILES["dinov2_tuned_v1"]["encoder"] != PROFILES["dinov2_highres_v1"]["encoder"]
    assert TunedDetector.profile_name == "dinov2_tuned_v1"


def test_matching_card_and_manifest_are_accepted(installed):
    root, _ = installed
    assert tuned_card(root, card("pcb1"))["threshold"] == 0.1


@pytest.mark.parametrize("key", ["threshold", "bank_sha256", "encoder_sha256", "model_id", "heatmap_scale"])
def test_a_card_that_disagrees_with_the_manifest_is_rejected(installed, key):
    root, _ = installed
    changed = deepcopy(card("pcb1"))
    changed[key] = "x" if isinstance(changed[key], str) else changed[key] * 2
    with pytest.raises(ValueError, match="disagree"):
        tuned_card(root, changed)


def test_every_product_uses_the_same_q95_rule(installed):
    root, manifest = installed
    assert TUNED_QUANTILES == {}
    wrong = deepcopy(manifest)
    wrong["categories"]["macaroni2"]["calibration"]["quantile"] = 0.8
    (root / "results" / TUNED_FILENAME).write_text(json.dumps(wrong))
    with pytest.raises(ValueError, match="Invalid tuned threshold"):
        tuned_card(root, wrong["categories"]["macaroni2"])


def test_thresholds_must_be_finite_positive_and_use_no_anomalous_images(installed):
    root, manifest = installed
    for edit in (
        lambda c: c.update(threshold=0.0, uncertainty_margin=0.0),
        lambda c: c["calibration"].update(anomalous=3),
        lambda c: c.update(uncertainty_margin=0.5),
    ):
        broken = deepcopy(manifest)
        edit(broken["categories"]["pcb1"])
        broken["categories"]["pcb1"]["calibration"].setdefault("policy", TUNED_POLICY)
        original = deepcopy(broken["categories"]["pcb1"])
        (root / "results" / TUNED_FILENAME).write_text(json.dumps(broken))
        with pytest.raises(ValueError, match="Invalid tuned threshold"):
            tuned_card(root, original)


def test_a_manifest_with_another_policy_is_rejected(installed):
    root, manifest = installed
    manifest["decision_policy"] = "something-else"
    (root / "results" / TUNED_FILENAME).write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Invalid tuned calibration manifest"):
        tuned_card(root, card("pcb1"))
