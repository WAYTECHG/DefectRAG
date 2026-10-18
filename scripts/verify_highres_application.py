"""Real isolated API/CPU/RAG acceptance of the installed high-resolution profile."""
import json,time
from pathlib import Path
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from backend.config import ROOT,CATEGORIES,Settings
from backend.main import create_app
from backend.highres import HighResolutionDetector
from backend.vision import sha256
from scripts.benchmark_official import write

if __name__=='__main__':
    output=ROOT/'results/highres_application_verification.json'
    report=json.loads(output.read_text()) if output.exists() else {'status':'running','examples':[],'answers':[]}
    app=create_app(Settings(data=ROOT/'runtime/highres-acceptance',profile='dinov2_highres_v1'))
    with TestClient(app) as client:
        health=client.get('/api/health').json()['data']
        assert len(health['models'])==12 and all(c['model_id'].startswith('dinov2-highres-') for c in health['models'])
        for category in CATEGORIES:
            for label,truth in [('good',0),('anomalous',1)]:
                if any(e['category']==category and e['truth']==truth for e in report['examples']):continue
                sample=ROOT/'samples'/f'{category}_{label}.jpg'
                response=client.post('/api/inspect',data={'category':category,'batch':'highres-acceptance'},
                    files={'file':(sample.name,sample.read_bytes(),'image/jpeg')})
                response.raise_for_status();record=response.json()['data']
                assert record['model_id']==f'dinov2-highres-{category}-v1'
                assert record['model_sha256']==sha256(ROOT/'models/highres'/f'{category}.npz')
                assert record['calibration']['anomalous']==0 and 'PCA' in record['localization']
                for url in (record['image_url'],record['heatmap_url'],f"/api/inspections/{record['id']}/report"):
                    assert client.get(url).status_code==200
                actual=client.get('/api/inspections/'+record['id']).json()['data']
                assert actual['score']==record['score']
                report['examples'].append({'category':category,'truth':truth,**{k:record[k] for k in ('id','model_id','verdict','score','threshold','inference_ms','peak_gpu_mb','localization','foreground_fraction')}})
                write(output,report);print(category+' '+label+' -> '+record['verdict']+' '+str(round(record['score'],5)),flush=True)
        target=next(e for e in report['examples'] if e['category']=='macaroni2' and e['truth']==1)
        questions=['Is this image anomalous?','Does the score mean accuracy?',
                   'What does this saved inspection heatmap show?','How was this model threshold calibrated?',
                   'What caused this defect?']
        for question in questions:
            if any(a['question']==question for a in report['answers']):continue
            response=client.post('/api/assistant',json={'inspection_id':target['id'],'question':question})
            response.raise_for_status();answer=response.json()['data']
            assert f"{target['score']:.5f}" in answer['answer']
            assert all(s.get('model_family')!='dinov3' for s in answer['evidence'])
            report['answers'].append({'question':question,**answer});write(output,report)
            print(question+' -> '+answer['mode'],flush=True)
        assert all(a['mode']=='measurement_only' for a in report['answers'][:2])
        assert report['answers'][2]['mode']=='llm',report['answers'][2]
        assert report['answers'][-1]['mode']=='abstained'
        assert client.get('/api/evaluation').json()['data']['profile']=='dinov2_highres_v1'
        official=client.get('/api/benchmark/official').json()['data']
        assert len(official['candidate']['categories'])==12
        assert target['id'] in client.get('/api/export.csv').text
    if not report.get('cpu_smoke'):
        cpu=HighResolutionDetector(Settings(device='cpu',profile='dinov2_highres_v1'))
        with Image.open(ROOT/'samples/macaroni2_anomalous.jpg') as image:prediction,overlay=cpu.predict(image,'macaroni2')
        assert prediction['device']=='cpu' and overlay.width>0
        report['cpu_smoke']={k:prediction[k] for k in ('model_id','score','verdict','inference_ms','device')}
    report.update(status='passed',checks={'real_images':24,'all12_highres_profiles':True,'separate_normal_only_calibration':True,
        'images_reports_saved_records':True,'trusted_measurement_answers':2,'real_qwen_heatmap':True,
        'wrong_family_documents_excluded':True,'unsupported_cause_abstains':True,'cpu_smoke':True,
        'scope':'software/runtime acceptance on resized sample derivatives; not a new accuracy benchmark'})
    write(output,report);print(json.dumps(report['checks']),flush=True)
