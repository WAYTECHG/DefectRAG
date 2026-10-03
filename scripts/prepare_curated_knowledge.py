"""Validate developer-reviewed rules against local source excerpts; never auto-publish."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge.policy import PRODUCTS


def prepare(manifest: dict, source_root: Path) -> list[dict]:
    result, ids = [], set()
    for record in manifest.get("sources", []):
        category = record.get("category")
        if category not in PRODUCTS:
            raise ValueError(f"Unknown product category: {category!r}")
        if not all(record.get(key) for key in ("path", "title", "source_url", "reviewed_by", "reviewed_at")):
            raise ValueError("Every source needs path, title, source_url, reviewed_by, reviewed_at")
        source_path = (source_root / record["path"]).resolve()
        if not source_path.is_relative_to(source_root.resolve()) or not source_path.is_file():
            raise ValueError(f"Source must be a local file under {source_root}: {record['path']}")
        source_text = " ".join(source_path.read_text(encoding="utf-8").split())
        for rule in record.get("rules", []):
            rule_id, claim, excerpt = (rule.get("id"), rule.get("claim"), rule.get("evidence_excerpt"))
            if not all((rule_id, claim, excerpt)) or rule_id in ids:
                raise ValueError("Each rule needs a unique id, claim, and evidence_excerpt")
            if " ".join(excerpt.split()) not in source_text:
                raise ValueError(f"Rule {rule_id}: excerpt is absent from the reviewed source")
            ids.add(rule_id)
            result.append({
                "id": rule_id, "title": record["title"], "text": claim,
                "evidence_excerpt": excerpt, "category": category,
                "anomaly_type": rule.get("anomaly_type", "general"),
                "knowledge_type": "product_rule", "review_status": "approved",
                "reviewed_by": record["reviewed_by"], "reviewed_at": record["reviewed_at"],
                "source": record["title"], "source_url": record["source_url"],
            })
    if not result:
        raise ValueError("No reviewed product rules in manifest; nothing written")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base", type=Path, help="Existing reviewed JSONL corpus to preserve in the staged output")
    args = parser.parse_args()
    records = prepare(json.loads(args.manifest.read_text(encoding="utf-8")), args.source_root)
    if args.base:
        existing = [json.loads(line) for line in args.base.read_text(encoding="utf-8").splitlines() if line.strip()]
        new_ids = {row["id"] for row in records}
        records = [row for row in existing if row["id"] not in new_ids] + records
    if args.output.resolve() == (args.base.resolve() if args.base else None):
        raise ValueError("Write to a staged output; do not overwrite the active corpus")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    temporary.replace(args.output)
    print(f"Prepared a staged corpus with {len(records)} entries at {args.output}. "
          "Review the output and rebuild the text index separately; this does not deploy it.")


if __name__ == "__main__":
    main()
