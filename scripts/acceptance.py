"""Resumable live acceptance using real VisA records and actual Qwen generation."""
import argparse
import json
import time
from pathlib import Path
import httpx
from backend.config import ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--dataset',type=Path,required=True)
    args=parser.parse_args()
    path=ROOT/'results'/'acceptance.json'
    report={'status':'running','real_images':[],'rag':[],'checks':{}}
    def save():path.write_text(json.dumps(report,indent=2))
    try:
        with httpx.Client(base_url=args.url,timeout=120,trust_env=False) as client:
            assert client.get('/').status_code==200
            report['checks']['dashboard_served']=True
            for category in ('pcb1','capsules','cashew'):
                saved=json.loads((ROOT/'results'/f'{category}_predictions.json').read_text())['test']
                existing=client.get('/api/inspections',params={'category':category,'batch':'acceptance-real-images','limit':500}).json()['data']
                for label in (0,1):
                    row=next(r for r in saved if r['label']==label)
                    filename=Path(row['image']).name
                    result=next((r for r in existing if r.get('filename')==filename and abs(r['score']-row['score'])<1e-5),None)
                    reused=result is not None
                    if result is None:
                        response=client.post('/api/inspect',data={'category':category,'batch':'acceptance-real-images'},files={'file':(filename,(args.dataset/row['image']).read_bytes(),'image/jpeg')})
                        response.raise_for_status();result=response.json()['data']
                    assert abs(result['score']-row['score'])<1e-5
                    assert client.get(result['heatmap_url']).status_code==200
                    assert client.get(result['image_url']).status_code==200
                    assert client.get('/api/inspections/'+result['id']).json()['data']['id']==result['id']
                    report['real_images'].append({'id':result['id'],'category':category,'truth':label,'verdict':result['verdict'],'score':result['score'],'score_matches_saved_evaluation':True,'inference_ms':result['inference_ms'],'reused_existing_record':reused})
                    save()
            identifier=report['real_images'][0]['id']
            questions=('Explain this anomaly score and its limitations.','How is its decision threshold calibrated?','What caused this defect?')
            for question in questions:
                start=time.perf_counter()
                response=client.post('/api/assistant',json={'inspection_id':identifier,'question':question})
                response.raise_for_status();answer=response.json()['data']
                report['rag'].append({'question':question,'seconds':time.perf_counter()-start,**answer});save()
                if 'caused' in question:assert answer['mode']=='abstained'
                else:
                    assert answer['mode']=='llm',answer
                    assert answer['claims']
                    assert {'retrieve','validate_evidence','generate','validate_answer'}<=set(answer['trace'])
                    for claim in answer['claims']:
                        evidence=next(e for e in answer['evidence'] if e['chunk_id']==claim['source_id'])
                        assert claim['quote'] in evidence['text']
            messages=client.get(f'/api/inspections/{identifier}/messages').json()['data'][-6:]
            report['checks']['followup_messages_persisted']=[m.get('question') for m in messages if m['role']=='user']==list(questions)
            report['checks']['batch_filter']=len(client.get('/api/inspections?batch=acceptance-real-images').json()['data'])>=6
            report['checks']['report_available']=client.get(f'/api/inspections/{identifier}/report').status_code==200
            response=client.post('/api/retrieve',json={'question':'What does the anomaly heatmap show?'})
            assert response.status_code==200 and response.json()['data']
            report['checks']['actual_retrieval']=True
            bad=client.post('/api/inspect',data={'category':'pcb1'},files={'file':('bad.jpg',b'broken','image/jpeg')})
            report['checks']['invalid_image_rejected']=bad.status_code==422
            report['checks']['local_alerts']=bool(client.get('/api/alerts').json()['data'])
        assert all(report['checks'].values()),report['checks']
        report['status']='passed'
        print(json.dumps({'checks':report['checks'],'real_predictions':len(report['real_images']),'genuine_generated_answers':sum(r['mode']=='llm' for r in report['rag'])},indent=2))
    except Exception as exc:
        report['status']='failed';report['failure']=str(exc)
        raise
    finally:save()
if __name__=='__main__':main()
