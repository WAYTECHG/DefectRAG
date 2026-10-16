"""Read existing local inspection evidence and capture one raw Qwen response."""
import json
from pathlib import Path
import httpx
from backend.config import ROOT
from backend.rag import PROMPT

def main():
    with httpx.Client(timeout=100,trust_env=False) as client:
        base='http://127.0.0.1:8766'
        health=client.get(base+'/api/health');health.raise_for_status()
        records=client.get(base+'/api/inspections?category=pcb1').json()['data']
        record=records[-1]
        question='Explain this anomaly score and its limitations.'
        response=client.post(base+'/api/retrieve',json={'question':question+' pcb1 anomaly inspection'})
        response.raise_for_status();evidence=response.json()['data']
        fields={k:record.get(k) for k in ('category','verdict','score','threshold','scope','localization')}
        prompt=PROMPT.format(inspection=json.dumps(fields),history='[]',question=question,evidence=json.dumps(evidence))
        response=client.post('http://127.0.0.1:11434/api/generate',json={'model':'qwen2.5:3b','prompt':prompt,'stream':False,'format':'json','keep_alive':'2m','options':{'temperature':0,'num_predict':450,'num_ctx':4096}})
        response.raise_for_status()
        body=response.json()
        report={'inspection_id':record['id'],'question':question,'evidence':evidence,'raw_response':body}
        (ROOT/'results'/'rag_diagnostic.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({'response':body.get('response'),'done_reason':body.get('done_reason'),'prompt_eval_count':body.get('prompt_eval_count'),'eval_count':body.get('eval_count')},indent=2),flush=True)
if __name__=='__main__':main()
