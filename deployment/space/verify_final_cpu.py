"""CPU-only public deployment boundaries; no model jobs or database writes."""
import hashlib
import json
from pathlib import Path
import re
import secrets
import httpx

ROOT=Path(__file__).resolve().parents[2]
TARGET='https://wizzas-defectrag.hf.space'

def main():
    checks=[]
    with httpx.Client(timeout=25,trust_env=False) as client:
        page=client.get(TARGET+'/')
        page.raise_for_status()
        css=re.search(r'href="([^"]+\.css)"',page.text).group(1)
        original=next((ROOT/'frontend/dist/assets').glob('*.css')).read_bytes()
        deployed=client.get(TARGET+'/'+css.lstrip('./'))
        deployed.raise_for_status()
        checks.append({'name':'css_preserved','passed':deployed.content==original,
                       'sha256':hashlib.sha256(deployed.content).hexdigest()})
        for endpoint in ('health','models','evaluation','benchmark/official','samples'):
            response=client.get(TARGET+'/api/'+endpoint)
            checks.append({'name':endpoint,'passed':response.status_code==200,'status':response.status_code})
            if endpoint=='health':
                checks[-1]['categories']=len(response.json()['data']['models'])
                checks[-1]['zero_gpu']=response.json()['data']['zero_gpu']
                checks[-1]['staff_persistence_enabled']=response.json()['data'].get('staff_persistence_enabled')
                checks[-1]['passed'] &= checks[-1]['categories']==12 and checks[-1]['zero_gpu'] is True and checks[-1]['staff_persistence_enabled'] is True
        for endpoint in ('stats','inspections','alerts','archives','export.csv'):
            response=client.get(TARGET+'/api/'+endpoint)
            checks.append({'name':'workspace_required_'+endpoint,'passed':response.status_code==401,
                           'status':response.status_code})
        for endpoint in ('stats','inspections'):
            response=client.get(TARGET+'/api/'+endpoint,headers={
                'X-DefectRAG-Session':secrets.token_hex(32),'Authorization':'Bearer invalid-acceptance-token'})
            checks.append({'name':'invalid_staff_token_'+endpoint,'passed':response.status_code==403,
                           'status':response.status_code})
    report={'status':'passed' if all(row['passed'] for row in checks) else 'failed','checks':checks}
    (ROOT/'development-support/space/final-cpu.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    assert report['status']=='passed'

if __name__=='__main__':
    main()
