"""Bounded anonymous RPC denial check; no SQL/admin operations or real record IDs."""
import json
from pathlib import Path
import uuid
import httpx
from deployment.space.supabase_repository import read_public_config

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'development-support/space'

def main():
    confirmation=json.loads((OUT/'migration-confirmed.json').read_text())
    assert confirmation.get('user_confirmed_manual_execution') is True
    config=read_public_config(OUT/'ui-dist/config.js')
    identifier=uuid.uuid4().hex
    checks=[]
    with httpx.Client(timeout=20,trust_env=False) as client:
        for name,payload in (
            ('defectrag_append_conversation',{'p_id':identifier,'p_question':'Authorization boundary test',
                                            'p_answer':{'answer':'Disposable denial check; not a model answer.'}}),
            ('defectrag_acknowledge_review',{'p_id':identifier})):
            response=client.post(config['url']+'/rest/v1/rpc/'+name,
                                 headers={'apikey':config['key']},json=payload)
            body=response.json()
            check={'rpc':name,'status':response.status_code,'code':body.get('code'),
                   'permission_denied':response.status_code in (401,403) and body.get('code')=='42501'}
            checks.append(check)
    report={'role':'anonymous','checks':checks,
            'status':'passed' if all(row['permission_denied'] for row in checks) else 'failed',
            'note':'No user JWT/admin access. Random nonexistent inspection ID. Missing function is not accepted as a pass.'}
    (OUT/'rpc-anonymous.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    assert report['status']=='passed'

if __name__=='__main__':
    main()
