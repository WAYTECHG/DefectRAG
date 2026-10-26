"""New QA extension contracts ONLY, cached PostgreSQL17 / network none / no live keys."""
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
    name = 'defectrag-ca-qa-' + uuid.uuid4().hex[:12]
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
            raise RuntimeError('Isolated PostgreSQL startup failed')
        # Reuse only the existing bootstrap literal, not its completed old test suites.
        old = (ROOT/'deployment/tests/run_corrective_actions_sql.py').read_text(encoding='utf8')
        bootstrap = re.search(r'bootstrap = r"""(.*?)"""', old, re.S).group(1)
        auth = (ROOT/'deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
        for fn in ['defectrag_has_aal2', 'defectrag_is_staff', 'defectrag_is_developer']:
            bootstrap += '\n' + re.search(r'create(?: or replace)? function public\.'+fn+r'\(\).*?\$\$;', auth, re.S).group(0)
        bootstrap += '\n\\ir supabase_corrective_actions.sql\n'
        # Preserve old ACL/policy/RPC metadata, except the one reviewed gate body.
        bootstrap += "create table qa_baseline as select oid,proacl,prosrc from pg_proc where pronamespace='public'::regnamespace;\n"
        bootstrap += "create table qa_policy_baseline as select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) as hash from pg_policies p where schemaname in ('public','storage');\n"
        bootstrap += '\\ir supabase_corrective_actions_qa.sql\n\\ir corrective_actions_qa_local.sql\n'
        bootstrap += "do $$ begin if exists(select 1 from qa_baseline b join pg_proc p on p.oid=b.oid where b.proacl is distinct from p.proacl or (p.proname<>'defectrag_ca_effect' and b.prosrc is distinct from p.prosrc)) then raise exception 'Existing RPC/ACL changed'; end if; if (select hash from qa_policy_baseline)<>(select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) from pg_policies p where schemaname in ('public','storage') and tablename<>'corrective_action_qa_runs') then raise exception 'Existing policy changed'; end if; end $$;\n"
        bootstrap += '\\pset format unaligned\n\\ir corrective_actions_qa_postflight.sql\n\\pset format aligned\n'
        bootstrap += '\\ir corrective_actions_qa_rollback_REVIEW_ONLY.sql\n'
        # Windows source checkouts and generated rollback can differ only in CRLF.
        bootstrap += "do $$ begin if exists(select 1 from qa_baseline b join pg_proc p on p.oid=b.oid where b.proacl is distinct from p.proacl or replace(b.prosrc,E'\\r\\n',E'\\n') is distinct from replace(p.prosrc,E'\\r\\n',E'\\n')) or to_regclass('public.corrective_action_qa_runs') is null then raise exception 'Rollback did not restore baseline or removed QA audit table'; end if; end $$;\n"
        for relative in ['deployment/supabase.sql', 'deployment/supabase_corrective_actions.sql',
                         'deployment/supabase_corrective_actions_qa.sql', 'deployment/tests/corrective_actions_qa_local.sql',
                         'deployment/corrective_actions_qa_rollback_REVIEW_ONLY.sql',
                         'deployment/corrective_actions_qa_postflight.sql']:
            source = ROOT/relative
            docker('cp', str(source), name+':/tmp/'+source.name)
        with tempfile.TemporaryDirectory(prefix='defectrag-ca-qa-') as directory:
            p = Path(directory)/'bootstrap.sql'; p.write_text(bootstrap, encoding='utf8')
            docker('cp', str(p), name+':/tmp/bootstrap.sql')
        r = docker('exec', name, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/bootstrap.sql', check=False)
        folder = ROOT/'results/corrective-actions-qa-preparation-20261025'; folder.mkdir(exist_ok=True)
        postflight = next((json.loads(line) for line in r.stdout.splitlines() if line.strip().startswith('{"mfa_required"')), None)
        passed = r.returncode == 0 and postflight is not None and all(v is True for v in postflight.values())
        report = {'passed': passed, 'postflight': postflight, 'network': 'none', 'image': IMAGE,
                  'production_access': False, 'native_auth_tested': False,
                  'old_completed_test_suites_repeated': False, 'stdout': r.stdout, 'stderr': r.stderr}
        (folder/'isolated-sql.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
        if not passed:
            raise RuntimeError(r.stderr or 'Read-only postflight mismatch')
        print('New scoped-QA SQL contracts and old policy/ACL/RPC preservation: PASS. Native live Auth NOT tested.')
    finally:
        if created:
            docker('rm', '-f', name)


if __name__ == '__main__':
    main()
