"""Read public configuration/service metadata without printing credentials."""
import json
from pathlib import Path
import re
import requests
from huggingface_hub import HfApi

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'development-support/space'
OUT.mkdir(parents=True,exist_ok=True)
text=Path(r'C:\Users\User\Desktop\DefectRAG-v2\frontend\public\config.js').read_text()
config={key:re.search(key+r'''\s*:\s*['"]([^'"]+)''',text).group(1)
        for key in ('supabaseUrl','supabasePublishableKey')}
assert config['supabaseUrl'].startswith('https://')
key=config['supabasePublishableKey']
assert key.startswith('sb_publishable_'), 'Review key type; never publish a service credential'
headers={'apikey':key}
result={'supabase_project_url':config['supabaseUrl'],'publishable_key_configured':True,'tables':{}}
for table in ('staff_members','shared_inspections','staff_notes'):
    response=requests.get(config['supabaseUrl']+'/rest/v1/'+table,params={'select':'*','limit':'0'},headers=headers,timeout=20)
    result['tables'][table]={'status':response.status_code}
    if not response.ok:
        result['tables'][table]['code']=response.json().get('code')
auth=requests.get(config['supabaseUrl']+'/auth/v1/settings',headers=headers,timeout=20)
result['auth_settings_status']=auth.status_code
api=HfApi()
model=api.model_info('Qwen/Qwen3-4B-Instruct-2507',files_metadata=True)
result['qwen_candidate']={'repo':model.id,'revision':model.sha,
    'safetensors_bytes':sum(f.size or 0 for f in model.siblings if f.rfilename.endswith('.safetensors'))}
(OUT/'service-probe.json').write_text(json.dumps(result,indent=2))
(OUT/'ui-dist/config.js').write_text('window.DEFECTRAG_PUBLIC_CONFIG='+json.dumps(config)+';')
print(json.dumps(result,indent=2))
