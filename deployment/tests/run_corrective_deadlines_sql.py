"""Focused existing deadline scheduler audit; cached PG17, network NONE, no live keys."""
from pathlib import Path
import json
import re
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'postgres:17-alpine'


def main():
    name = 'defectrag-ca-deadline-' + uuid.uuid4().hex[:12]
    created = False
    def docker(*args, check=True):
        return subprocess.run(['docker', *args], capture_output=True, text=True, check=check)
    try:
        docker('image', 'inspect', IMAGE)
        docker('run', '-d', '--pull', 'never', '--network', 'none', '--name', name,
               '-e', 'POSTGRES_PASSWORD=isolated-fixture-only', IMAGE)
        created = True
        for _ in range(30):
            if docker('exec', name, 'pg_isready', '-U', 'postgres', check=False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Isolated PostgreSQL unavailable')
        old = (ROOT/'deployment/tests/run_corrective_actions_sql.py').read_text(encoding='utf8')
        bootstrap = re.search(r'bootstrap = r"""(.*?)"""', old, re.S).group(1)
        auth = (ROOT/'deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
        for fn in ('defectrag_has_aal2', 'defectrag_is_staff', 'defectrag_is_developer'):
            bootstrap += '\n' + re.search(r'create(?: or replace)? function public\.'+fn+r'\(\).*?\$\$;', auth, re.S).group(0)
        bootstrap += '\n\\ir supabase_corrective_actions.sql\n\\ir corrective_actions_deadlines_local.sql\n'
        for relative in ('deployment/supabase.sql', 'deployment/supabase_corrective_actions.sql',
                         'deployment/tests/corrective_actions_deadlines_local.sql'):
            p = ROOT/relative
            docker('cp', str(p), name+':/tmp/'+p.name)
        with tempfile.TemporaryDirectory(prefix='defectrag-deadline-') as directory:
            p = Path(directory)/'bootstrap.sql'; p.write_text(bootstrap, encoding='utf8')
            docker('cp', str(p), name+':/tmp/bootstrap.sql')
        r = docker('exec', name, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/bootstrap.sql', check=False)
        folder = ROOT/'results/corrective-actions-one-event-20261025'; folder.mkdir(exist_ok=True)
        report = {'passed': r.returncode == 0, 'network': 'none', 'image': IMAGE,
                  'production_access': False, 'native_auth_tested': False,
                  'completed_old_suites_repeated': False, 'stdout': r.stdout, 'stderr': r.stderr}
        (folder/'deadline-contracts.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
        if r.returncode:
            raise RuntimeError(r.stderr or 'Deadline assertion failed')
        print('Focused existing deadline scheduler contracts: PASS; no production access.')
    finally:
        if created:
            docker('rm', '-f', name)


if __name__ == '__main__':
    main()
