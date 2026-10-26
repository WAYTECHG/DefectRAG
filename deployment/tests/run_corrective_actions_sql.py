"""Offline contract tests; never connects to real Supabase or sends notifications.

Uses cached official PostgreSQL 17, no network, mounts or published ports. Native
Auth tables/JWT issuance are fixtures. Actual base + corrective SQL and the three
current Auth helper definitions are tested, not a replacement implementation.
"""
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
    name = 'defectrag-ca-sql-' + uuid.uuid4().hex[:12]
    created = False

    def command(*args, check=True):
        return subprocess.run(['docker', *args], capture_output=True, text=True, check=check)

    try:
        command('image', 'inspect', IMAGE)
        command('run', '-d', '--pull', 'never', '--network', 'none', '--name', name,
                '-e', 'POSTGRES_PASSWORD=isolated-fixture-only', IMAGE)
        created = True
        for _ in range(30):
            if command('exec', name, 'pg_isready', '-U', 'postgres', check=False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Isolated database did not become ready')

        auth_source = (ROOT / 'deployment/supabase_auth_mfa.sql').read_text(encoding='utf8')
        helpers = []
        for function in ('defectrag_has_aal2', 'defectrag_is_staff', 'defectrag_is_developer'):
            # SQL bodies end at their own $$ delimiter, not at a nested statement.
            match = re.search(r'create(?: or replace)? function public\.' + function
                              + r'\(\).*?\$\$;', auth_source, re.S)
            if not match:
                raise RuntimeError('Auth helper not found: ' + function)
            helpers.append(match.group(0))
        bootstrap = r"""\set ON_ERROR_STOP on
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth; create schema storage;
grant usage on schema auth,storage to anon,authenticated,service_role;
create table auth.users(id uuid primary key,aud text,role text,email text,email_confirmed_at timestamptz,raw_app_meta_data jsonb,raw_user_meta_data jsonb);
create table auth.mfa_factors(id uuid primary key,user_id uuid references auth.users(id),factor_type text,status text,secret text);
create function auth.jwt() returns jsonb language sql stable as $$select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb$$;
create function auth.uid() returns uuid language sql stable as $$select (auth.jwt()->>'sub')::uuid$$;
create function auth.role() returns text language sql stable as $$select auth.jwt()->>'role'$$;
create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(bucket_id text,name text,primary key(bucket_id,name));
alter table storage.objects enable row level security;
grant select,insert on storage.objects to authenticated;
create function storage.foldername(text) returns text[] language sql immutable as $$select (string_to_array($1,'/'))[1:array_length(string_to_array($1,'/'),1)-1]$$;
\ir supabase.sql
alter table public.staff_members add column revoked_at timestamptz;
alter table public.staff_members add column revoked_by uuid references auth.users(id);
create table public.defectrag_auth_settings(singleton boolean primary key default true,mfa_required boolean not null);
insert into public.defectrag_auth_settings values(true,true);
""" + '\n'.join(helpers) + '\n\\ir supabase_corrective_actions.sql\n\\ir corrective_actions_local.sql\n\\ir corrective_actions_editors_local.sql\n'
        for relative in ('deployment/supabase.sql', 'deployment/supabase_corrective_actions.sql',
                         'deployment/tests/corrective_actions_local.sql',
                         'deployment/tests/corrective_actions_editors_local.sql',
                         'deployment/corrective_actions_postflight.sql'):
            source = ROOT / relative
            command('cp', str(source), name + ':/tmp/' + source.name)
        with tempfile.TemporaryDirectory(prefix='defectrag-ca-fixture-') as directory:
            source = Path(directory) / 'bootstrap.sql'
            source.write_text(bootstrap, encoding='utf8')
            command('cp', str(source), name + ':/tmp/bootstrap.sql')
        result = command('exec', name, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1',
                         '-f', '/tmp/bootstrap.sql', check=False)
        report = {'passed': result.returncode == 0, 'image': IMAGE, 'network': 'none',
                  'production_access': False, 'native_supabase_auth_tested': False,
                  'stdout': result.stdout, 'stderr': result.stderr}
        if result.returncode == 0:
            postflight = command('exec', name, 'psql', '-U', 'postgres', '-At',
                                 '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/corrective_actions_postflight.sql')
            checks = json.loads(postflight.stdout)
            report['postflight'] = checks
            report['passed'] = all(value is True for key, value in checks.items() if key != 'policies')
        target = ROOT / 'results/corrective-actions-editors-20261024/local-sql-contracts.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
        if not report['passed']:
            raise RuntimeError(result.stderr or 'Postflight metadata assertion failed')
        print('Corrective-action PostgreSQL contracts passed; native live Auth NOT tested.')
    finally:
        if created:
            command('rm', '-f', name)  # Only the exact unique container created above.


if __name__ == '__main__':
    main()
