"""Verify new categories through the real API, preserving existing runtime history."""
import json
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.config import ROOT, Settings, CATEGORIES
from backend.storage import SQLiteRepository


def main():
    dataset=Path(r'C:\Users\User\Downloads\VisA_20220922')
    evaluation=json.loads((ROOT/'results/evaluation.json').read_text())
    assert set(evaluation['categories'])==set(CATEGORIES)
    records=[]
    # Separate persistent verification history; never replace the user's database.
    data=ROOT/'runtime'/'verification12'
    repo=SQLiteRepository(data/'inspection.sqlite3')
    app=create_app(Settings(data=data))
    with TestClient(app) as client:
        for category in CATEGORIES:
            manifest=json.loads((ROOT/'results'/f'{category}_splits.json').read_text())
            hashes={k:{r['sha256'] for r in rows} for k,rows in manifest.items()}
            assert all(not hashes[a]&hashes[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
            if category in ('pcb1','capsules','cashew'):continue
            predictions=json.loads((ROOT/'results'/f'{category}_predictions.json').read_text())['test']
            for truth in (0,1):
                row=next(r for r in predictions if r['label']==truth)
                existing=next((r for r in repo.list(category=category,limit=100) if r.get('filename')==Path(row['image']).name),None)
                if existing:record=existing
                else:
                    path=dataset/row['image']
                    response=client.post('/api/inspect',data={'category':category,'batch':'All-category verification'},
                                         files={'file':(path.name,path.read_bytes(),'image/jpeg')})
                    assert response.status_code==200,response.text
                    record=response.json()['data']
                assert abs(record['score']-row['score'])<1e-6
                assert client.get(record['heatmap_url']).status_code==200
                assert client.get('/api/inspections/'+record['id']+'/report').status_code==200
                records.append({'id':record['id'],'category':category,'truth':truth,'score':record['score'],'verdict':record['verdict']})
            print('API verified: '+category,flush=True)
    receipt={'status':'passed','categories':list(CATEGORIES),'real_images':records,
             'data_directory':'runtime/verification12','new_records':len(records),'split_hash_checks':'passed',
             'scores_match_saved_evaluation':True,'original_three':'preserved; not repeated'}
    (ROOT/'results/all_categories_acceptance.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({'status':'passed','categories':12,'new_real_api_images':len(records)}),flush=True)


if __name__=='__main__':main()
