"""Scoped, read-only batch-name preflight; not a distributed name reservation."""
import unicodedata


def normalize_batch(value):
    return ' '.join(unicodedata.normalize('NFKC',str(value or '')).split()).lower()


def batch_name_available(repo,name):
    key=normalize_batch(name)
    for archived in (False,True):
        offset=0
        while True:
            rows=repo.list(limit=500,offset=offset,archived=archived)
            if any(normalize_batch(row.get('batch'))==key for row in rows):
                return False
            if len(rows)<500:
                break
            offset+=len(rows)
    return True
