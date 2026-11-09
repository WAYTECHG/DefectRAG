"""Rebuild the saved-example showcase from inspections made by the deployed tuned detector.

Reads a finished inspection database and its artifacts in read-only mode. It never runs the model and never
publishes arbitrary uploads: only inspections whose file name is one of the 24 allowlisted VisA samples
(`<product>_good.jpg` / `<product>_anomalous.jpg`) are exported, with every result kept exactly as measured
(including the cases the detector got wrong).

    python -m scripts.export_showcase_tuned --source <folder with inspection.sqlite3 and artifacts/>
"""

import argparse
import csv
import hashlib
import html
import io
import json
import os
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "frontend" / "public" / "showcase"
FIELDS = [
    "id",
    "created_at",
    "category",
    "verdict",
    "score",
    "threshold",
    "uncertainty_margin",
    "inference_ms",
    "model_id",
]
CATEGORIES = [
    "candle",
    "capsules",
    "cashew",
    "chewinggum",
    "fryum",
    "macaroni1",
    "macaroni2",
    "pcb1",
    "pcb2",
    "pcb3",
    "pcb4",
    "pipe_fryum",
]
ALLOWED = {f"{c}_{kind}.jpg": (c, kind) for c in CATEGORIES for kind in ("good", "anomalous")}
ATTRIBUTION = "VisA · Zou et al., ECCV 2022 · CC BY 4.0"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def load_inspections(source):
    database = Path(source) / "inspection.sqlite3"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        payloads = [json.loads(row[0]) for row in db.execute("SELECT payload FROM inspections")]
    chosen = {}
    for payload in sorted(payloads, key=lambda p: p["created_at"]):
        name = payload.get("filename")
        if name in ALLOWED and payload["category"] == ALLOWED[name][0]:
            chosen[name] = payload  # the latest run of each sample wins
    missing = sorted(set(ALLOWED) - set(chosen))
    if missing:
        raise ValueError("Missing saved inspections for: " + ", ".join(missing))
    models = {p["model_id"].split("-")[0] + "-" + p["model_id"].split("-")[1] for p in chosen.values()}
    if models != {"dinov2-tuned"}:
        raise ValueError("Expected only inspections by the tuned detector, found: " + ", ".join(sorted(models)))
    return [chosen[name] for name in sorted(chosen)]


def report_page(record, esc):
    table = "".join(f"<tr><th>{esc(k)}</th><td>{esc(record.get(k, ''))}</td></tr>" for k in FIELDS)
    identifier = record["id"]
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Saved DefectRAG example</title><style>body{font:16px system-ui;max-width:900px;margin:30px auto;padding:16px}"
        "img{max-width:46%}th,td{padding:6px;text-align:left}@media print{button{display:none}}</style>"
        "<h1>Saved inspection example</h1><p>Previously measured VisA example. No live inference runs on this website.</p>"
        f"<p>{ATTRIBUTION} · resized images and model overlay. "
        '<a href="https://github.com/amazon-science/spot-diff">Dataset source</a></p>'
        '<button onclick="window.print()">Print / save PDF</button><table>' + table + "</table>"
        f'<h2>Image and measured heatmap</h2><img alt="VisA sample" src="../images/{identifier}.jpg">'
        f'<img alt="Saved heatmap" src="../images/{identifier}_heatmap.jpg">'
        "<h2>Recorded evidence conversation</h2><p>No evidence conversation was recorded for this inspection.</p></html>"
    )


def export(source, output=OUTPUT):
    source = Path(source)
    inspections = load_inspections(source)
    for folder in ("images", "reports"):
        shutil.rmtree(output / folder, ignore_errors=True)
        (output / folder).mkdir(parents=True, exist_ok=True)
    records, samples, conversations = [], [], {}
    esc = lambda value: html.escape(str(value))  # noqa: E731
    for payload in inspections:
        identifier = payload["id"]
        record = {k: payload[k] for k in FIELDS if k in payload}
        record.update(
            batch="Verified VisA examples",
            filename="VisA example",
            image_url=f"showcase/images/{identifier}.jpg",
            heatmap_url=f"showcase/images/{identifier}_heatmap.jpg",
        )
        for suffix in (".jpg", "_heatmap.jpg"):
            shutil.copyfile(source / "artifacts" / (identifier + suffix), output / "images" / (identifier + suffix))
        stem = Path(payload["filename"]).stem
        samples.append(
            {
                "name": stem,
                "category": record["category"],
                "record_id": identifier,
                "url": record["image_url"],
                "attribution": ATTRIBUTION,
            }
        )
        conversations[identifier] = []
        records.append(record)
        (output / "reports" / (identifier + ".html")).write_text(report_page(record, esc), encoding="utf-8")
    evaluation = read_json("results/tuned_deployment_evaluation.json")
    official = read_json("results/official_evaluation.json")
    if (ROOT / "results/highres_evaluation.json").exists():
        official["candidate"] = read_json("results/highres_evaluation.json")
    if (ROOT / "results/mvtec_summary.json").exists():
        official["mvtec"] = read_json("results/mvtec_summary.json")
    data = {
        "schema": 1,
        "mode": "saved_examples",
        "records": records,
        "samples": samples,
        "messages": conversations,
        "evaluation": evaluation,
        "official_evaluation": official,
        "attribution": ATTRIBUTION + " · resized images and model overlays",
        "source": "https://github.com/amazon-science/spot-diff",
    }
    text = json.dumps(data, indent=2)
    if ":\\" in text or "Users/" in text or "localhost" in text or "127.0.0.1" in text:
        raise ValueError("Local path or service address found in public snapshot")
    (output / "data.json").write_text(text, encoding="utf-8")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    (output / "inspections.csv").write_text(buffer.getvalue(), encoding="utf-8")
    hashes = {
        p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "files": hashes,
                "records": len(records),
                "provenance": "24 inspections by the deployed tuned detector (dinov2_tuned_v1); results kept as measured, including misses; no assistant conversations",
            },
            indent=2,
        )
    )
    print(json.dumps({"status": "passed", "examples": len(records), "files": len(hashes), "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=str(Path(os.environ.get("TEMP", ".")) / "defectrag-thumb-data"),
        help="folder holding inspection.sqlite3 and artifacts/",
    )
    export(parser.parse_args().source)
