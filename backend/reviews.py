"""Append-only human reviews, stored separately from immutable model measurements."""
import json

PREFIX='DEFECTRAG_REVIEW_V1:'
STATUSES=('Needs review','In review','Reviewed')
DECISIONS=('Pending','Hold','Accept','Reject')

def validate_review(status,decision,note=''):
    if (status not in STATUSES or decision not in DECISIONS or
        (status=='Reviewed') == (decision=='Pending') or not isinstance(note,str) or len(note)>1000):
        raise ValueError('Choose a review status and a compatible decision.')
    return {'status':status,'decision':decision,'note':note.strip()}

def review_body(status,decision,note=''):
    return PREFIX+json.dumps(validate_review(status,decision,note))

def parse_review(body):
    if not isinstance(body,str) or not body.startswith(PREFIX):return None
    try:
        value=json.loads(body[len(PREFIX):])
        return validate_review(value['status'],value['decision'],value.get('note',''))
    except (ValueError,KeyError,TypeError):return None
