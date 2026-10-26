"""Reject stale local sync clients instead of serving a broken dashboard."""
import hashlib
import json
from pathlib import Path
from fastapi.responses import FileResponse,HTMLResponse,Response

FIXED=('frontend/index.html','frontend/package.json','frontend/package-lock.json',
       'frontend/vite.config.js','frontend/localBuild.mjs')
TEXT_TYPES={'.js','.mjs','.jsx','.ts','.tsx','.css','.svg','.html','.json','.md','.txt'}

def source_files(root):
    names=set(FIXED)
    for folder in ('frontend/src','frontend/public'):
        for file in (root/folder).rglob('*'):
            if file.is_symlink():raise ValueError('Symlink build input')
            if file.is_file() and file!=root/'frontend/public/config.js':names.add(file.relative_to(root).as_posix())
    return names

def valid_local_build(root,dist):
    try:
        receipt=json.loads((dist/'local-ui-build.json').read_text(encoding='utf8'))
        if not isinstance(receipt,dict) or not isinstance(receipt.get('sources'),dict) or not isinstance(receipt.get('files'),dict):return False
        if receipt['schema']!=1 or receipt['protocol']!=1 or receipt.get('mode')!='production' or set(receipt['sources'])!=source_files(root):return False
        for name,digest in receipt['sources'].items():
            content=(root/name).read_bytes()
            if Path(name).suffix in TEXT_TYPES:content=content.replace(b'\r\n',b'\n')
            if hashlib.sha256(content).hexdigest()!=digest:return False
        files=receipt['files']
        if 'index.html' not in files or not any(n.startswith('assets/') and n.endswith('.js') for n in files):return False
        for name,digest in files.items():
            file=(dist/name).resolve()
            if not file.is_relative_to(dist.resolve()) or not file.is_file():return False
            if hashlib.sha256(file.read_bytes()).hexdigest()!=digest:return False
        return True
    except (OSError,ValueError,KeyError,TypeError):return False

def mount_local_frontend(app,root,dist):
    @app.get('/',include_in_schema=False)
    @app.get('/index.html',include_in_schema=False)
    def dashboard():
        if valid_local_build(root,dist):return FileResponse(dist/'index.html',headers={'Cache-Control':'no-store'})
        return HTMLResponse('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>DefectRAG · Local startup</title><main style="max-width:680px;margin:12vh auto;padding:24px;font-family:system-ui;color:#202744">
<h1>The local dashboard needs a rebuild.</h1><p>This build predates the current synchronization client, or its source files changed.</p>
<p>Stop the local backend with Ctrl+C, then run this in PowerShell from the project folder:</p>
<pre style="padding:18px;background:#f3f1ff;white-space:pre-wrap">&amp; '.\\deployment\\run_local.ps1'</pre>
<p>The launcher backs up the old build and prepares the compatible dashboard. Inspection history, images and account permissions are preserved.</p>
<p>For the two-terminal development setup, open <a href="http://127.0.0.1:5173">the React development dashboard</a>.</p></main>''',status_code=503,headers={'Cache-Control':'no-store'})

    @app.get('/config.js',include_in_schema=False)
    def public_config():
        # Use current public settings, not the old copy embedded in dist. Native
        # authorization UI must agree with the local backend's required checks.
        text=(root/'frontend/public/config.js').read_text(encoding='utf8')
        text+='\nwindow.DEFECTRAG_PUBLIC_CONFIG.authWorkflowEnabled = true;\n'
        return Response(text,media_type='application/javascript',headers={'Cache-Control':'no-store'})

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    ready=valid_local_build(root,root/'frontend/dist')
    print('Local dashboard ready' if ready else 'Local dashboard needs a rebuild')
    raise SystemExit(0 if ready else 1)
