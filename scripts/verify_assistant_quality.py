"""Capture real upgraded answers against an isolated running inspection workspace."""
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
IDENTIFIER='a6226ef392eb417e8991369e890d816b'
QUESTIONS=['So this product is anomaly right?','Does 0.09 mean 9% accurate?',
           'What does this inspection heatmap show?','How does that map relate to the anomaly score?',
           'What caused this defect?']

if __name__=='__main__':
    path=ROOT/'results/assistant_quality_verification.json'
    report=json.loads(path.read_text()) if path.exists() else {'status':'running','inspection_id':IDENTIFIER,'answers':[]}
    with httpx.Client(base_url='http://127.0.0.1:8780',timeout=120,trust_env=False) as client:
        record=client.get('/api/inspections/'+IDENTIFIER).json()['data']
        for question in QUESTIONS:
            if any(a['question']==question for a in report['answers']):continue
            response=client.post('/api/assistant',json={'inspection_id':IDENTIFIER,'question':question});response.raise_for_status()
            answer=response.json()['data']
            assert f"{record['score']:.5f}" in answer['answer']
            report['answers'].append({'question':question,**answer})
            path.write_text(json.dumps(report,indent=2))
            print(question+' -> '+answer['mode'],flush=True)
    assert report['answers'][0]['mode']=='measurement_only' and report['answers'][0]['answer'].startswith('Yes—')
    assert report['answers'][1]['mode']=='measurement_only' and 'not an accuracy percentage' in report['answers'][1]['answer']
    assert all(a['mode']=='llm' for a in report['answers'][2:4])
    for answer in report['answers'][2:4]:
        sources={s['chunk_id']:s for s in answer['evidence']}
        assert answer['claims']
        assert all(c['quote'] in sources[c['source_id']]['text'] for c in answer['claims'])
    assert report['answers'][4]['mode']=='abstained'
    report.update(status='passed',checks={'saved_verdict_and_score':True,'score_not_accuracy':True,
        'real_local_qwen_explanations':2,'followup_with_quotes':True,'unsupported_root_cause_abstains':True,
        'scope':'five developer acceptance cases; not a general RAG accuracy benchmark'})
    path.write_text(json.dumps(report,indent=2))
    print(json.dumps(report['checks']),flush=True)
