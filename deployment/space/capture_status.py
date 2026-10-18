"""Bounded authenticated status/log capture; prints only a compact summary."""
import argparse
import json
from pathlib import Path
import time
import requests
from huggingface_hub import HfApi,get_token

parser=argparse.ArgumentParser()
parser.add_argument('--name',required=True)
parser.add_argument('--logs',choices=('run','build'),default='run')
args=parser.parse_args()
out=Path(__file__).resolve().parents[2]/'development-support/space'
api=HfApi()
runtime=api.get_space_runtime('Wizzas/DefectRAG').raw
(out/(args.name+'-runtime.json')).write_text(json.dumps(runtime,indent=2))
lines=[]
try:
    with requests.get(f'https://huggingface.co/api/spaces/Wizzas/DefectRAG/logs/{args.logs}',
                      headers={'Authorization':'Bearer '+get_token()},stream=True,timeout=(15,5)) as response:
        response.raise_for_status()
        start=time.monotonic()
        for line in response.iter_lines(chunk_size=1):
            if line:
                lines.append(line.decode('utf8',errors='replace'))
            if len(lines)>2500 or time.monotonic()-start>18:
                break
except requests.RequestException:
    pass
text='\n'.join(lines)
(out/(args.name+'-'+args.logs+'.log')).write_text(text,encoding='utf8')
print(json.dumps({'stage':runtime.get('stage'),'commit':runtime.get('sha'),'log_lines':len(lines),
    'sse_missing_session_errors':text.count('response already started'),
    'last_log_entries':lines[-6:]},ensure_ascii=True))
