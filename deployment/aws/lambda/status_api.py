"""Lambda behind a Function URL: returns a small public status document.

Runtime: Python 3.12. Handler: status_api.handler. No environment variables are required.
It only returns harmless public facts, so the URL can use auth type NONE.
Set reserved concurrency to a small number (for example 5) to cap cost and abuse.
"""
import json
import os
from datetime import datetime, timezone

SAVED_EXAMPLES = 24  # the showcase ships 24 saved real inspections (2 per product, tuned detector)


def handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "GET").upper()
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
    }
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": headers, "body": ""}
    if method != "GET":
        return {"statusCode": 405, "headers": headers, "body": json.dumps({"error": "Use GET"})}
    body = {
        "service": "DefectRAG showcase",
        "status": "ok",
        "saved_examples": SAVED_EXAMPLES,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "region": os.environ.get("AWS_REGION", "unknown"),
    }
    return {"statusCode": 200, "headers": headers, "body": json.dumps(body)}
