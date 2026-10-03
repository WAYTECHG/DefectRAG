"""Small, auditable gates between retrieval and product-specific claims."""

from __future__ import annotations

from typing import Any
import re

PRODUCTS = frozenset({
    "breakfast_box", "juice_bottle", "pushpins", "screw_bag", "splicing_connectors"
})


def permitted_category(document: dict[str, Any], category: str) -> bool:
    """Do not show another product's instructions as evidence for this one."""
    return document.get("category") in ({"general", category} if category in PRODUCTS else {"general"})


def approved_product_rules(evidence: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    """A generic dataset description never counts as an approved inspection rule."""
    return [doc for doc in evidence if doc.get("category") == category
            and doc.get("knowledge_type") == "product_rule"
            and doc.get("review_status") == "approved"
            and doc.get("source_url") and doc.get("reviewed_by")]


def evidence_status(evidence: list[dict[str, Any]], category: str) -> dict[str, Any]:
    rules = approved_product_rules(evidence, category)
    return {
        "product_rules_available": bool(rules),
        "approved_rule_ids": [doc["id"] for doc in rules],
        "message": ("Approved product-specific rules were retrieved."
                    if rules else "No approved product-specific rule was retrieved. "
                    "The report can describe visible differences and general anomaly concepts, "
                    "but cannot verify a product specification or root cause."),
    }


def has_topic_overlap(question: str, evidence: list[dict[str, Any]]) -> bool:
    """A conservative abstention gate for unrelated questions; not a relevance metric."""
    stop = {"about", "what", "which", "where", "when", "does", "have", "from", "with", "your", "this", "that", "there", "their", "would", "could", "should", "explain", "please", "tell"}
    tokens = set(re.findall(r"[a-z0-9]{4,}", question.lower().replace("_", " "))) - stop
    if not tokens:
        return False
    text = " ".join(str(doc.get(key, "")) for doc in evidence for key in ("title", "text")).lower().replace("_", " ")
    return bool(tokens & set(re.findall(r"[a-z0-9]{4,}", text)))
