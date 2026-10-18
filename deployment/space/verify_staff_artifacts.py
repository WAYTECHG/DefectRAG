"""Read only the signed report/export links captured from the authorized dashboard."""
import csv
import html
from io import StringIO
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import httpx
from deployment.space.supabase_repository import read_public_config

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'development-support/space'
IDENTIFIER='a6351615259d42868b766a004f5dd303'

def main():
    links=json.loads((OUT/'phase4-private-links.json').read_text())
    config=read_public_config(OUT/'ui-dist/config.js')
    for value in links.values():
        assert urlparse(value).scheme=='https' and urlparse(value).netloc=='wizzas-defectrag.hf.space'
    checks={}
    with httpx.Client(timeout=25,trust_env=False) as client:
        exported=client.get(links['csv'])
        checks['csv_status']=exported.status_code
        assert exported.status_code==200
        rows=list(csv.DictReader(StringIO(exported.text)))
        item=next(row for row in rows if row['id']==IDENTIFIER)
        checks['csv_has_staff_inspection']=item['batch']=='PHASE4-STAFF-ACCEPTANCE'
        report=client.get(links['report'])
        checks['report_status']=report.status_code
        assert report.status_code==200
        checks['conversation_present']=all(text in report.text for text in
            ('Is this image anomalous?','What does the heatmap show?','screening-4'))
        cells={html.unescape(re.sub('<[^>]+>','',key)):html.unescape(re.sub('<[^>]+>','',value))
               for key,value in re.findall(r'<tr><th>(.*?)</th><td>(.*?)</td></tr>',report.text)}
        checks['supabase_storage']=cells.get('storage')=='supabase'
        checks['acknowledged_persisted']=cells.get('alert acknowledged')=='True'
        images=re.findall(r'<img src="([^"]+)"',report.text)
        assert len(images)==2
        checks['image_statuses']=[]
        for image in images:
            image=html.unescape(image)
            assert urlparse(image).netloc==urlparse(config['url']).netloc
            response=client.get(image)
            checks['image_statuses'].append(response.status_code)
        assert checks['image_statuses']==[200,200]
        (OUT/'phase4-staff-report.html').write_text(report.text,encoding='utf8')
        (OUT/'phase4-staff-export.csv').write_text(exported.text,encoding='utf8')
    assert all(checks[key] for key in ('csv_has_staff_inspection','conversation_present','supabase_storage','acknowledged_persisted'))
    summary={'status':'passed','inspection_id':IDENTIFIER,'checks':checks,
             'measurements':{key:cells.get(key) for key in ('score','threshold','inference ms','verdict','model id','device')}}
    (OUT/'phase4-staff-artifacts.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))

if __name__=='__main__':
    main()
