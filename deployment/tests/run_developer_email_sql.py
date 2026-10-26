"""Disposable offline PostgreSQL contracts. Requires cached official postgres:17-alpine.

No production credentials, mounts, published ports, real cron or HTTP. Removes
only the unique test container it creates. Existing n8n/volumes remain untouched.
"""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
NAME = 'defectrag-email-sql-' + uuid.uuid4().hex[:12]
IMAGE = 'postgres:17-alpine'


def command(*args, check=True):
    return subprocess.run(['docker', *args], check=check, capture_output=True, text=True)


def main():
    command('image', 'inspect', IMAGE)  # --pull never below prevents implicit downloads.
    created = False
    outputs = []
    try:
        command('run', '-d', '--pull', 'never', '--network', 'none', '--name', NAME,
                '-e', 'POSTGRES_PASSWORD=isolated-fixture-only', IMAGE)
        created = True
        for _ in range(30):
            ready = command('exec', NAME, 'pg_isready', '-U', 'postgres', check=False)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Local test database did not become ready')
        # Copy ONLY reviewed SQL test inputs; no repository, data, env or secrets mount.
        sources = [
            'deployment/supabase_direct_notifications.sql',
            'deployment/supabase_developer_notifications.sql',
            'deployment/supabase_developer_notification_schedule.sql',
            'deployment/email_automation_enable.sql',
            'deployment/email_automation_pause.sql',
            'deployment/tests/developer_notifications_local.sql',
            'deployment/tests/developer_schedule_local.sql',
        ]
        for source in sources:
            path = ROOT / source
            command('cp', str(path), f'{NAME}:/tmp/{path.name}')
        for script in ['developer_notifications_local.sql', 'developer_schedule_local.sql']:
            result = command('exec', NAME, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1',
                             '-f', '/tmp/' + script, check=False)
            outputs.append({'script': script, 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise RuntimeError(f'{script} failed: {result.stderr}')
        report = {'passed': True, 'image': IMAGE, 'container_network': 'none',
                  'production_access': False, 'native_cron_net_vault_tested': False,
                  'scripts': outputs}
        target = ROOT / 'results/email-automation-readiness-20261022/sql-contract-tests.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
        print(json.dumps({key: value for key, value in report.items() if key != 'scripts'}))
    finally:
        if created:
            command('rm', '-f', NAME)  # Exact generated name; never enumerate/remove other containers.


if __name__ == '__main__':
    main()
