"""Owner-CC migration contracts ONLY, cached PostgreSQL17 / network none / no live keys."""
from pathlib import Path
import json
import re
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'postgres:17-alpine'
CHANGED = ('defectrag_ca_effect', 'defectrag_ca_qa_effect')


def main():
    name = 'defectrag-ca-cc-' + uuid.uuid4().hex[:12]
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
        # Same bootstrap as the reviewed QA runner: base schema, MFA helpers, CA, then QA.
        old = (ROOT/'deployment/tests/run_corrective_actions_sql.py').read_text(encoding='utf8')
        bootstrap = re.search(r'bootstrap = r"""(.*?)"""', old, re.S).group(1)
        auth = (ROOT/'deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
        for fn in ['defectrag_has_aal2', 'defectrag_is_staff', 'defectrag_is_developer']:
            bootstrap += '\n' + re.search(r'create(?: or replace)? function public\.'+fn+r'\(\).*?\$\$;', auth, re.S).group(0)
        bootstrap += '\n\\ir supabase_corrective_actions.sql\n\\ir supabase_corrective_actions_qa.sql\n'
        bootstrap += "create table cc_baseline as select oid,proname,proacl,replace(prosrc,E'\\r\\n',E'\\n') as prosrc from pg_proc where pronamespace='public'::regnamespace;\n"
        bootstrap += "create table cc_policy_baseline as select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) as hash from pg_policies p where schemaname='public';\n"
        bootstrap += '\\ir supabase_corrective_actions_owner_cc.sql\n'
        # Only the two reviewed bodies may change; every ACL and policy stays identical.
        bootstrap += ("do $$ begin if exists(select 1 from cc_baseline b join pg_proc p on p.oid=b.oid where b.proacl is distinct from p.proacl "
                      "or (b.proname not in ('defectrag_ca_effect','defectrag_ca_qa_effect') and b.prosrc is distinct from replace(p.prosrc,E'\\r\\n',E'\\n'))) "
                      "or (select hash from cc_policy_baseline) is distinct from (select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) from pg_policies p where schemaname='public') "
                      "then raise exception 'Unexpected RPC/ACL/policy change'; end if; end $$;\n")
        bootstrap += '\\ir corrective_actions_owner_cc_local.sql\n'
        # Rollback restores the exact previous bodies.
        bootstrap += '\\ir corrective_actions_owner_cc_rollback_REVIEW_ONLY.sql\n'
        bootstrap += ("do $$ begin if exists(select 1 from cc_baseline b join pg_proc p on p.oid=b.oid where b.proacl is distinct from p.proacl "
                      "or b.prosrc is distinct from replace(p.prosrc,E'\\r\\n',E'\\n')) then raise exception 'Rollback did not restore previous bodies'; end if; end $$;\n"
                      "select 'OWNER_CC_ROLLBACK_PASS';\n")
        for relative in ['deployment/supabase.sql', 'deployment/supabase_corrective_actions.sql',
                         'deployment/supabase_corrective_actions_qa.sql', 'deployment/supabase_corrective_actions_owner_cc.sql',
                         'deployment/corrective_actions_owner_cc_rollback_REVIEW_ONLY.sql',
                         'deployment/tests/corrective_actions_owner_cc_local.sql']:
            source = ROOT/relative
            docker('cp', str(source), name+':/tmp/'+source.name)
        with tempfile.TemporaryDirectory(prefix='defectrag-ca-cc-') as directory:
            p = Path(directory)/'bootstrap.sql'; p.write_text(bootstrap, encoding='utf8')
            docker('cp', str(p), name+':/tmp/bootstrap.sql')
        r = docker('exec', name, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/bootstrap.sql', check=False)
        passed = r.returncode == 0 and 'OWNER_CC_CONTRACTS_PASS' in r.stdout and 'OWNER_CC_ROLLBACK_PASS' in r.stdout
        folder = ROOT/'results/corrective-actions-owner-cc'; folder.mkdir(parents=True, exist_ok=True)
        report = {'passed': passed, 'network': 'none', 'image': IMAGE, 'production_access': False,
                  'native_auth_tested': False, 'changed_functions': list(CHANGED), 'stdout': r.stdout, 'stderr': r.stderr}
        (folder/'isolated-sql.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
        if not passed:
            raise RuntimeError(r.stderr[-3000:] or 'Owner-CC contracts failed')
        print('Owner-CC SQL contracts, ACL/policy preservation and exact rollback: PASS. Native live Auth NOT tested.')
    finally:
        if created:
            docker('rm', '-f', name)


if __name__ == '__main__':
    main()
