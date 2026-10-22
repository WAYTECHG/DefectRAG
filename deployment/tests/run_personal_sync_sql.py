"""Test actual additive SQL in a disposable, offline cached PostgreSQL container."""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
def main():
    name='defectrag-sync-sql-'+uuid.uuid4().hex[:12];created=False
    def command(*args,check=True):return subprocess.run(['docker',*args],check=check,capture_output=True,text=True)
    try:
        command('image','inspect','postgres:17-alpine')
        command('run','-d','--pull','never','--network','none','--name',name,'-e','POSTGRES_PASSWORD=isolated-fixture-only','postgres:17-alpine');created=True
        for _ in range(30):
            if command('exec',name,'pg_isready','-U','postgres',check=False).returncode==0:break
            time.sleep(1)
        else:raise RuntimeError('Test database not ready')
        for relative in ('deployment/supabase_personal_workspace.sql','deployment/supabase_personal_sync.sql','deployment/tests/personal_sync_local.sql'):
            source=ROOT/relative;command('cp',str(source),name+':/tmp/'+source.name)
        result=command('exec',name,'psql','-U','postgres','-v','ON_ERROR_STOP=1','-f','/tmp/personal_sync_local.sql',check=False)
        report={'passed':result.returncode==0,'image':'postgres:17-alpine','network':'none','production_access':False,'native_supabase_tested':False,'stdout':result.stdout,'stderr':result.stderr}
        target=ROOT/'results/local-cloud-sync-20261022/sql-contracts.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,indent=2)+'\n')
        if result.returncode:raise RuntimeError(result.stderr)
        print('Actual personal workspace + additive sync SQL passed isolated PostgreSQL17 contracts.')
    finally:
        if created:command('rm','-f',name)  # Only this exact generated test container; no volumes/mounts.
if __name__=='__main__':main()
