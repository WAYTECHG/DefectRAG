"""Bind resumable item IDs to image content, product and batch within a repository."""
import hashlib
import json
import re

def fingerprint(content,category,batch):
    metadata=json.dumps([category,batch.strip()],separators=(',',':')).encode()
    return hashlib.sha256(metadata+b'\0'+content).hexdigest()

def existing_request(repo,request_id,content,category,batch):
    if not request_id:return None
    if not re.fullmatch('[a-f0-9]{32}',request_id):
        raise ValueError('Invalid inspection request ID. Start a new batch.')
    record=repo.get(request_id)
    if record and record.get('request_fingerprint')!=fingerprint(content,category,batch):
        raise ValueError('This request ID belongs to another upload. Start a new batch.')
    return record
