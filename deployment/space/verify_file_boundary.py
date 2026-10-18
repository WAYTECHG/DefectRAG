"""Read-only negative tests: generic Gradio routes must not expose private files."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
import requests

root=Path(__file__).resolve().parents[2]
support=root/'development-support/space'
vision=json.loads((support/'phase2-cloud.json').read_text())
rag=json.loads((support/'phase3-cloud.json').read_text())
owner=hashlib.sha256(vision['session'].encode()).hexdigest()
paths=[f'/app/runtime/space-development/sessions/{owner}/inspection.sqlite3',
       f"/app/runtime/space-development/artifacts/{rag['inspection_id']}.jpg"]
results=[]
for path in paths:
    with requests.get('https://wizzas-defectrag.hf.space/gradio_api/file='+quote(path,safe='/'),timeout=20,stream=True) as response:
        results.append({'kind':'database' if path.endswith('.sqlite3') else 'image','status':response.status_code})
        assert response.status_code in (401,403,404), 'Generic Gradio file route exposed a private artifact'
(support/'file-boundary.json').write_text(json.dumps({'status':'passed','checks':results},indent=2))
print(json.dumps(results))
