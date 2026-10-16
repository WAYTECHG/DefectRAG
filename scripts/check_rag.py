"""Check real generation on an existing inspection without creating new images."""
import json
import time
import httpx
from backend.config import ROOT

if __name__=='__main__':
    report={'answers':[],'status':'running'}
    path=ROOT/'results'/'rag_live.json'
    try:
        with httpx.Client(base_url='http://127.0.0.1:8766',timeout=120,trust_env=False) as client:
            assert client.get('/api/health').json()['data']['version']=='2.0.1'
            record=client.get('/api/inspections?category=pcb1').json()['data'][-1]
            report['inspection_id']=record['id']
            for question in ['Explain this anomaly score and its limitations.','How is its decision threshold calibrated?','What caused this defect?']:
                start=time.perf_counter()
                response=client.post('/api/assistant',json={'inspection_id':record['id'],'question':question})
                response.raise_for_status();answer=response.json()['data']
                report['answers'].append({'question':question,'seconds':time.perf_counter()-start,**answer})
                path.write_text(json.dumps(report,indent=2))
                expected='abstained' if 'caused' in question else 'llm'
                assert answer['mode']==expected,answer
                print(question,answer['mode'],answer['answer'],flush=True)
        report['status']='passed'
    except Exception as exc:
        report['status']='failed';report['failure']=str(exc)
        raise
    finally:path.write_text(json.dumps(report,indent=2))
