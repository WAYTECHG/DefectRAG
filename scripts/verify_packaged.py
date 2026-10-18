"""Exercise an extracted archive's real API, weights and local RAG assets.
May be executed as a file from outside the extraction; imports are pinned to cwd.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    project=Path.cwd().resolve()
    if not (project/'RELEASE_MANIFEST.json').exists():raise RuntimeError('Run inside a newly extracted release')
    if (project/'runtime').exists():raise RuntimeError('Extraction already used; choose a fresh extraction')
    os.environ['DEFECTRAG_ENCODER']=str(project/'models'/'encoder')
    os.environ['DEFECTRAG_EMBEDDING']=str(project/'models'/'embedding')
    os.environ['DEFECTRAG_DATA']=str(project/'runtime')
    sys.path.insert(0,str(project))
    import backend.main as implementation
    from backend.config import Settings
    from fastapi.testclient import TestClient
    assert Path(implementation.__file__).resolve().is_relative_to(project)
    report={'status':'running','python':platform.python_version(),'loaded_from_extraction':True,'checks':{}}
    try:
        app=implementation.create_app(Settings(data=project/'runtime'))
        with TestClient(app) as client:
            report['checks']['dashboard']=client.get('/').status_code==200
            assert client.get('/api/inspections').json()['data']==[]
            sample=project/'samples'/'pcb1_anomalous.jpg'
            response=client.post('/api/inspect',data={'category':'pcb1','batch':'extracted-release'},files={'file':(sample.name,sample.read_bytes(),'image/jpeg')})
            response.raise_for_status();record=response.json()['data']
            expected='dinov2-highres-' if (project/'models/highres/PROFILE.json').exists() else 'dinov3-'
            assert record['score']>=0 and record['model_id'].startswith(expected)
            report['prediction']={k:record[k] for k in ('category','verdict','score','threshold','inference_ms','model_sha256')}
            report['checks']['genuine_inference']=True
            report['checks']['heatmap']=client.get(record['heatmap_url']).status_code==200
            report['checks']['saved_history']=client.get('/api/inspections').json()['data'][0]['id']==record['id']
            response=client.post('/api/assistant',json={'inspection_id':record['id'],'question':'What does this heatmap measure?'})
            response.raise_for_status();answer=response.json()['data']
            assert answer['mode']=='llm',answer
            assert all(s['id']!='dinomaly' for s in answer['evidence'])
            assert answer['claims']
            report['answer']=answer
            report['checks']['bundled_retrieval_and_genuine_generation']=True
            report['checks']['report']=client.get('/api/inspections/'+record['id']+'/report').status_code==200
            report['checks']['csv']=record['id'] in client.get('/api/export.csv').text
        assert all(report['checks'].values())
        report['status']='passed'
        print(json.dumps({'status':report['status'],'checks':report['checks'],'prediction':report['prediction']},indent=2),flush=True)
    except Exception as exc:
        report['status']='failed';report['error']=str(exc)
        raise
    finally:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
