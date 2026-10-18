"""Read signed export from the other staff browser session; no model/database writes."""
import csv
from io import StringIO
import json
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'development-support/space'

def main():
    url=json.loads((OUT/'phase5-private-links.json').read_text())['csv']
    assert urlparse(url).scheme=='https' and urlparse(url).netloc=='wizzas-defectrag.hf.space'
    response=httpx.get(url,timeout=25,trust_env=False)
    assert response.status_code==200
    rows=list(csv.DictReader(StringIO(response.text)))
    batch=[row for row in rows if row['batch']=='PHASE5-STAFF-BATCH']
    assert len(batch)==2 and len({row['id'] for row in batch})==2
    assert all(row['category']=='capsules' for row in batch)
    assert {row['verdict'] for row in batch}=={'Good','Uncertain'}
    report={'status':'passed','batch':'PHASE5-STAFF-BATCH','durable_records':batch,
            'read_from_other_staff_browser_session':True,
            'same_staff_account':True,'different_staff_user_tested':False,
            'submission_pattern':'Two successive one-image runs; latest UI run 1 completed / 0 failed.',
            'successful_single_click_two_file_run_verified':False,
            'note':'Actual free-account HF iframe inference and durable Supabase storage. No repeated model calls.'}
    (OUT/'phase5-hosted-batch.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':
    main()
