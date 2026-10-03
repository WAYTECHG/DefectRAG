import unittest
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from app.document_processor import extract_text, make_chunks
from app.rag_service import build_prompt
from app.inspection_service import CATEGORY_THRESHOLDS, _build_grounded_query, _save_heatmap
from rag.anomaly_crop import anomaly_map_to_bounding_box, create_location_visualization


class DocumentProcessorTests(unittest.TestCase):
    def test_markdown_is_chunked_and_has_stable_ids(self):
        body = ("Inspection checks must confirm component placement. " * 80).encode()
        records = extract_text("inspection.md", body)
        chunks = make_chunks(records, "inspection.md")
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks, make_chunks(records, "inspection.md"))
        self.assertTrue(all(chunk["text"] for chunk in chunks))

    def test_json_records_support_content_alias(self):
        records = extract_text("notes.json", b'{"documents":[{"title":"Check","content":"Verify connector count."}]}')
        self.assertEqual(records, [{"title": "Check", "text": "Verify connector count."}])

    def test_unsupported_extensions_are_rejected(self):
        with self.assertRaises(ValueError):
            extract_text("diagram.png", b"not text")

    def test_csv_rows_are_converted_to_searchable_text(self):
        records = extract_text("criteria.csv", b"criterion,limit\nconnector_count,4\n")
        self.assertEqual(records[0]["title"], "criteria — row 1")
        self.assertIn("criterion: connector_count", records[0]["text"])
        self.assertIn("limit: 4", records[0]["text"])


class PromptTests(unittest.TestCase):
    def test_prompt_includes_evidence_numbering_and_question(self):
        prompt = build_prompt("What is checked?", [{"title": "Inspection", "source": "manual.md", "text": "Check alignment."}])
        self.assertIn("[1] Inspection", prompt)
        self.assertIn("Check alignment.", prompt)
        self.assertIn("What is checked?", prompt)


class InspectionTests(unittest.TestCase):
    def test_every_loco_category_has_a_positive_threshold(self):
        self.assertEqual(len(CATEGORY_THRESHOLDS), 5)
        self.assertTrue(all(value > 0 for value in CATEGORY_THRESHOLDS.values()))

    def test_grounded_query_contains_visual_evidence(self):
        query = _build_grounded_query("breakfast_box", 0.12, 4, 9, {"visual_observation": "one item is displaced", "evidence": ["uneven spacing"]})
        self.assertIn("one item is displaced", query)
        self.assertIn("uneven spacing", query)
        self.assertIn("row=4", query)

    def test_heatmap_is_written_at_original_size(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.png"
            output = Path(folder) / "heatmap.jpg"
            Image.new("RGB", (160, 120), "white").save(source)
            _save_heatmap(source, np.linspace(0, 1, 196).reshape(14, 14), output)
            self.assertTrue(output.exists())
            with Image.open(output) as rendered:
                self.assertEqual(rendered.size, (160, 120))

    def test_connected_anomaly_region_becomes_pixel_bounding_box(self):
        anomaly_map = np.zeros((14, 14), dtype=np.float32)
        anomaly_map[4:6, 8:10] = [[0.8, 0.9], [0.85, 1.0]]
        box = anomaly_map_to_bounding_box(anomaly_map, (1400, 700), expansion_cells=0)
        self.assertEqual(box["pixel"], {"x_min": 800, "y_min": 200, "x_max": 1000, "y_max": 300})
        self.assertEqual(box["peak_patch"], {"row": 5, "column": 9})

    def test_location_visualization_draws_bounding_box(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.png"
            output = Path(folder) / "location.jpg"
            Image.new("RGB", (320, 240), "white").save(source)
            box = {"pixel": {"x_min": 80, "y_min": 60, "x_max": 180, "y_max": 150}}
            create_location_visualization(source, 5, 5, bounding_box=box, output_path=output)
            self.assertTrue(output.exists())
            with Image.open(output) as rendered:
                self.assertEqual(rendered.size, (320, 240))


if __name__ == "__main__":
    unittest.main()
