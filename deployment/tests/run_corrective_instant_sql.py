"""Doorbell migration contracts ONLY, cached PostgreSQL17 / network none / no live keys."""
from pathlib import Path
import json
import re
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'postgres:17-alpine'

# Recording stand-ins for Supabase Vault and pg_net; nothing leaves the container.
STUBS = r"""
create schema vault;
create table vault.secrets_t(name text primary key, decrypted_secret text);
create view vault.decrypted_secrets as select name, decrypted_secret from vault.secrets_t;
create schema net;
create table net.calls(id bigserial primary key, url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer);
create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
returns bigint language plpgsql as $$
declare id bigint;
begin
 if current_setting('test.net_fail', true)='1' then raise exception 'simulated network failure'; end if;
 insert into net.calls(url,body,params,headers,timeout_milliseconds) values(url,body,params,headers,timeout_milliseconds) returning calls.id into id;
 return id;
end; $$;
"""
SNAPSHOT = ("create table {t} as select oid,proname,proacl,replace(prosrc,E'\\r\\n',E'\\n') as prosrc from pg_proc where pronamespace='public'::regnamespace;\n"
            "create table {t}_pol as select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) as hash from pg_policies p where schemaname='public';\n")
SAME = ("do $$ begin if exists(select 1 from {t} b join pg_proc p on p.oid=b.oid where b.proacl is distinct from p.proacl "
        "or b.prosrc is distinct from replace(p.prosrc,E'\\r\\n',E'\\n')) "
        "or (select count(*) from pg_proc where pronamespace='public'::regnamespace and proname not like 'cc\\_%' and oid not in (select oid from {t})) <> {extra} "
        "or (select hash from {t}_pol) is distinct from (select md5(coalesce(string_agg(row_to_json(p)::text,',' order by schemaname,tablename,policyname),'')) from pg_policies p where schemaname='public') "
        "then raise exception '{msg}'; end if; end $$;\n")


def main():
    name = 'defectrag-ca-ring-' + uuid.uuid4().hex[:12]
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
        # Same bootstrap as the reviewed runners, then everything already live.
        old = (ROOT/'deployment/tests/run_corrective_actions_sql.py').read_text(encoding='utf8')
        bootstrap = re.search(r'bootstrap = r"""(.*?)"""', old, re.S).group(1)
        auth = (ROOT/'deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
        for fn in ['defectrag_has_aal2', 'defectrag_is_staff', 'defectrag_is_developer']:
            bootstrap += '\n' + re.search(r'create(?: or replace)? function public\.'+fn+r'\(\).*?\$\$;', auth, re.S).group(0)
        bootstrap += '\n\\ir supabase_corrective_actions.sql\n\\ir supabase_corrective_actions_qa.sql\n\\ir supabase_corrective_actions_owner_cc.sql\n'
        bootstrap += STUBS
        bootstrap += SNAPSHOT.format(t='ring_baseline')
        bootstrap += '\\ir supabase_corrective_actions_instant.sql\n'
        # Only the doorbell function is new; every existing body, ACL and policy is identical.
        bootstrap += SAME.format(t='ring_baseline', extra=1, msg='Unexpected RPC/ACL/policy change')
        bootstrap += '\\ir corrective_actions_instant_local.sql\n'
        bootstrap += '\\ir corrective_actions_instant_rollback_REVIEW_ONLY.sql\n'
        bootstrap += SAME.format(t='ring_baseline', extra=0, msg='Rollback did not restore the previous state')
        bootstrap += ("do $$ begin if exists(select 1 from pg_trigger where tgname='defectrag_ca_ring_on_event') then raise exception 'Trigger left behind'; end if; end $$;\n"
                      "select 'INSTANT_ROLLBACK_PASS';\n")
        for relative in ['deployment/supabase.sql', 'deployment/supabase_corrective_actions.sql',
                         'deployment/supabase_corrective_actions_qa.sql', 'deployment/supabase_corrective_actions_owner_cc.sql',
                         'deployment/supabase_corrective_actions_instant.sql', 'deployment/corrective_actions_instant_rollback_REVIEW_ONLY.sql',
                         'deployment/tests/corrective_actions_instant_local.sql']:
            source = ROOT/relative
            docker('cp', str(source), name+':/tmp/'+source.name)
        with tempfile.TemporaryDirectory(prefix='defectrag-ca-ring-') as directory:
            p = Path(directory)/'bootstrap.sql'; p.write_text(bootstrap, encoding='utf8')
            docker('cp', str(p), name+':/tmp/bootstrap.sql')
        r = docker('exec', name, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/bootstrap.sql', check=False)
        passed = r.returncode == 0 and 'INSTANT_CONTRACTS_PASS' in r.stdout and 'INSTANT_ROLLBACK_PASS' in r.stdout
        folder = ROOT/'results/corrective-actions-instant'; folder.mkdir(parents=True, exist_ok=True)
        report = {'passed': passed, 'network': 'none', 'image': IMAGE, 'production_access': False,
                  'vault_and_pg_net': 'recording stand-ins', 'stdout': r.stdout, 'stderr': r.stderr}
        (folder/'isolated-sql.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
        if not passed:
            raise RuntimeError(r.stderr[-3000:] or 'Doorbell contracts failed')
        print('Doorbell SQL contracts, ACL/policy preservation and exact rollback: PASS. Real Vault/pg_net NOT tested.')
    finally:
        if created:
            docker('rm', '-f', name)


if __name__ == '__main__':
    main()
