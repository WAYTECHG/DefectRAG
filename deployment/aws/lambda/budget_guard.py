"""SNS-triggered cost guard: stops EC2 instances tagged Project=DefectRAG-lab.

Runtime: Python 3.12. Handler: budget_guard.handler. Trigger: SNS topic that AWS Budgets publishes to.
It never terminates anything and ignores every instance without the tag.
Test safely with the event {"dry_run": true}: it lists the instances and stops nothing.
"""
import json
import logging

import boto3

log = logging.getLogger()
log.setLevel(logging.INFO)

TAG_KEY = "Project"
TAG_VALUE = "DefectRAG-lab"


def running_lab_instances(ec2):
    found = []
    pages = ec2.get_paginator("describe_instances").paginate(
        Filters=[
            {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]},
        ]
    )
    for page in pages:
        for reservation in page["Reservations"]:
            found.extend(item["InstanceId"] for item in reservation["Instances"])
    return found


def handler(event, context):
    dry_run = bool(event.get("dry_run")) if isinstance(event, dict) else False
    from_budget = isinstance(event, dict) and "Records" in event
    if from_budget:
        for record in event["Records"]:
            log.info("Budget message: %s", str(record.get("Sns", {}).get("Message", ""))[:500])
    ec2 = boto3.client("ec2")
    ids = running_lab_instances(ec2)
    result = {"matched": ids, "dry_run": dry_run, "stopped": []}
    if ids and not dry_run:
        ec2.stop_instances(InstanceIds=ids)
        result["stopped"] = ids
    log.info("Result: %s", json.dumps(result))
    return result
