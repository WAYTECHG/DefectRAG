"""Local startup regression: old clients cannot loop on missing sync headers."""
import hashlib
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.local_frontend import FIXED,source_files,valid_local_build,mount_local_frontend

def fixture_build(root):
    for name in FIXED:
        file=root/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'source\n')
    public=root/'frontend/public';public.mkdir();(public/'config.js').write_text('window.DEFECTRAG_PUBLIC_CONFIG={};')
    src=root/'frontend/src';src.mkdir();(src/'main.jsx').write_bytes(b'client\n')
    dist=root/'frontend/dist';(dist/'assets').mkdir(parents=True)
    (dist/'index.html').write_text('<script src="./assets/client.js"></script>')
    (dist/'assets/client.js').write_text('real compiled artifact fixture')
    receipt={'schema':1,'protocol':1,'mode':'production',
             'sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in source_files(root)},
             'files':{n:hashlib.sha256((dist/n).read_bytes()).hexdigest() for n in ('index.html','assets/client.js')}}
    (dist/'local-ui-build.json').write_text(json.dumps(receipt))
    return dist

def test_missing_or_stale_bundle_is_actionable_not_the_old_dashboard(tmp_path):
    dist=tmp_path/'frontend/dist';app=FastAPI();mount_local_frontend(app,tmp_path,dist)
    with TestClient(app) as client:
        for endpoint in ('/','/index.html'):
            result=client.get(endpoint)
            assert result.status_code==503 and 'run_local.ps1' in result.text
            assert result.headers['cache-control']=='no-store'
            assert '/assets/' not in result.text

def test_current_bundle_and_live_public_config_are_served(tmp_path):
    dist=fixture_build(tmp_path);assert valid_local_build(tmp_path,dist)
    app=FastAPI();mount_local_frontend(app,tmp_path,dist)
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        config=client.get('/config.js')
        assert 'authWorkflowEnabled = true' in config.text
        assert config.headers['cache-control']=='no-store'
        (tmp_path/'frontend/public/config.js').write_text('window.DEFECTRAG_PUBLIC_CONFIG={registrationEnabled:false};')
        assert valid_local_build(tmp_path,dist),'public config is served live without a rebuild'
        assert 'registrationEnabled:false' in client.get('/config.js').text
        (tmp_path/'frontend/src/main.jsx').write_text('new incompatible source')
        assert client.get('/').status_code==503

def test_modified_outputs_new_inputs_and_unsafe_receipts_fail_closed(tmp_path):
    dist=fixture_build(tmp_path)
    file=dist/'assets/client.js';before=file.read_bytes();file.write_text('stale compiled transport')
    assert not valid_local_build(tmp_path,dist)
    file.write_bytes(before);assert valid_local_build(tmp_path,dist)
    receipt_file=dist/'local-ui-build.json';receipt=json.loads(receipt_file.read_text());receipt['mode']='showcase';receipt_file.write_text(json.dumps(receipt))
    assert not valid_local_build(tmp_path,dist),'a read-only showcase must not replace the inspection dashboard'
    receipt['mode']='production';receipt_file.write_text(json.dumps(receipt))
    (tmp_path/'frontend/src/new.jsx').write_text('new source')
    assert not valid_local_build(tmp_path,dist)
    (tmp_path/'frontend/src/new.jsx').unlink()
    receipt=json.loads((dist/'local-ui-build.json').read_text());receipt['files']['../outside.js']='a'*64
    (dist/'local-ui-build.json').write_text(json.dumps(receipt))
    assert not valid_local_build(tmp_path,dist)
    receipt['sources']=sorted(receipt['sources'])
    (dist/'local-ui-build.json').write_text(json.dumps(receipt))
    assert not valid_local_build(tmp_path,dist),'malformed receipt shows rebuild guidance, not a server error'
