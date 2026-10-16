"""Real local RAG verification of the previously failing heatmap explanation."""
import json
import time
import httpx
from backend.config import ROOT

if __name__=='__main__':
    report={'status':'running','answers':[]}
    path=ROOT/'results'/'evidence_scope_verification.json'
    try:
        with httpx.Client(base_url='http://127.0.0.1:8766',timeout=120,trust_env=False) as client:
            record=client.get('/api/inspections?category=pcb1').json()['data'][0]
            report['inspection_id']=record['id']
            for question in ('What does this inspection heatmap show?','How does that map relate to anomaly scoring?'):
                started=time.perf_counter()
                response=client.post('/api/assistant',json={'inspection_id':record['id'],'question':question})
                response.raise_for_status();answer=response.json()['data']
                report['answers'].append({'question':question,'seconds':time.perf_counter()-started,**answer})
                path.write_text(json.dumps(report,indent=2))
                assert answer['mode']=='llm',answer
                assert not any(d['id']=='dinomaly' for d in answer['evidence'])
                assert any('cosine distance' in d['text'] for d in answer['evidence'])
                for claim in answer['claims']:
                    source=next(d for d in answer['evidence'] if d['chunk_id']==claim['source_id'])
                    assert claim['quote'] in source['text']
                print(question,answer['answer'],flush=True)
        report['status']='passed'
    except Exception as exc:
        report['status']='failed';report['failure']=str(exc)
        raise
    finally:path.write_text(json.dumps(report,indent=2))
