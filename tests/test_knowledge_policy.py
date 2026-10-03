import tempfile
import unittest
from pathlib import Path

import numpy as np

from knowledge.policy import evidence_status, permitted_category, has_topic_overlap
from scripts.prepare_curated_knowledge import prepare
from vision.box_metrics import box_iou, mask_box


class CurationTests(unittest.TestCase):
    def test_unreviewed_generic_text_cannot_become_a_product_rule(self):
        generic = {"id": "s", "category": "screw_bag", "source_url": "https://example.org"}
        self.assertFalse(evidence_status([generic], "screw_bag")["product_rules_available"])
        self.assertFalse(permitted_category({"category": "pushpins"}, "screw_bag"))
        self.assertTrue(permitted_category({"category": "general"}, "screw_bag"))
        self.assertFalse(has_topic_overlap("How tall is Mount Everest?", [{"title": "Logical anomalies", "text": "Unexpected product configuration"}]))

    def test_curated_rule_requires_an_actual_source_excerpt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "approved.txt").write_text("Each kit contains one verified component.", encoding="utf-8")
            source = {"path": "approved.txt", "title": "Inspected specification", "source_url": "https://example.org/source",
                      "reviewed_by": "owner", "reviewed_at": "2026-10-02", "category": "breakfast_box",
                      "rules": [{"id": "verified_rule", "claim": "The kit has one component.",
                                 "evidence_excerpt": "one verified component"}]}
            result = prepare({"sources": [source]}, root)
            self.assertTrue(evidence_status(result, "breakfast_box")["product_rules_available"])
            source["rules"][0]["evidence_excerpt"] = "imagined component"
            with self.assertRaises(ValueError):
                prepare({"sources": [source]}, root)


class GeometryTests(unittest.TestCase):
    def test_single_box_overlap_is_not_map50(self):
        mask = np.zeros((5, 5), dtype=bool)
        mask[1:3, 1:3] = True
        box = mask_box(mask)
        self.assertEqual(box_iou(box, box), 1.0)
        self.assertEqual(box_iou(box, {"x_min": 3, "y_min": 3, "x_max": 5, "y_max": 5}), 0.0)
