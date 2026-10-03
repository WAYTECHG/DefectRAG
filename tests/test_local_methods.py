"""Check local method availability and compact scoring without touching real model assets."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import inspection_service


class MethodAvailabilityTests(unittest.TestCase):
    def test_trained_methods_require_compact_bank_and_matching_head_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bank_dir = root / "assets"
            heads_dir = root / "training"
            bank_dir.mkdir()
            heads_dir.mkdir()
            with patch.object(inspection_service, "CLOUD_MEMORY_DIR", bank_dir), patch.object(inspection_service, "HEAD_DIR", heads_dir), patch.object(inspection_service, "FEATURES_DIR", root / "features"):
                (bank_dir / "breakfast_box.pt").touch()
                category = next(item for item in inspection_service.available_categories() if item["id"] == "breakfast_box")
                self.assertEqual(category["methods"], ["baseline"])
                (heads_dir / "breakfast_box_head.pt").touch()
                category = next(item for item in inspection_service.available_categories() if item["id"] == "breakfast_box")
                self.assertEqual(category["methods"], ["baseline", "trained", "fusion"])


@unittest.skipUnless(importlib.util.find_spec("torch") is not None, "PyTorch is installed in the Docker image")
class CompactScoringTests(unittest.TestCase):
    def test_selected_method_uses_its_own_patch_scores(self):
        import torch
        from torch.nn import functional as F
        from vision.compact_scorer import CompactDINOv3Scorer
        from vision.normal_autoencoder import NormalPatchAutoencoder

        class Encoder:
            device = torch.device("cpu")

            def encode(self, _):
                return {"patches": queries[None]}

        torch.manual_seed(42)
        memory = F.normalize(torch.randn(20, 16), dim=1)
        queries = F.normalize(torch.randn(196, 16), dim=1)
        head = NormalPatchAutoencoder(16, 8)
        with tempfile.TemporaryDirectory() as folder:
            bank = Path(folder) / "breakfast_box.pt"
            checkpoint = Path(folder) / "breakfast_box_head.pt"
            torch.save({"category": "breakfast_box", "patches": memory}, bank)
            torch.save({"category": "breakfast_box", "dimension": 16, "bottleneck": 8, "state_dict": head.state_dict()}, checkpoint)
            scorer = CompactDINOv3Scorer("breakfast_box", Encoder(), bank, checkpoint)
            for method in ("baseline", "trained", "fusion"):
                result = scorer.score_image("unused.png", method=method)
                self.assertAlmostEqual(result["anomaly_score"], result["comparison_scores"][method], places=5)
                self.assertEqual(result["anomaly_map"].shape, (14, 14))
                self.assertEqual(set(result["comparison_scores"]), {"baseline", "trained", "fusion"})
            self.assertNotAlmostEqual(result["comparison_scores"]["baseline"], result["comparison_scores"]["trained"])


if __name__ == "__main__":
    unittest.main()
