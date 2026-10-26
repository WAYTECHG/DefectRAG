-- READ ONLY: run AFTER the manually applied personal sync migration.
-- One metadata result; no inspection payloads, identities, tokens or mutations.
select jsonb_build_object(
 'auth_settings',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'sync_column',(select jsonb_build_object('type',data_type,'nullable',is_nullable,'default',column_default) from information_schema.columns where table_schema='public' and table_name='personal_inspections' and column_name='sync_version'),
 'tables',(select jsonb_agg(jsonb_build_object('name',c.relname,'rls',c.relrowsecurity,
   'anon_select',has_table_privilege('anon',c.oid,'SELECT'),'anon_insert',has_table_privilege('anon',c.oid,'INSERT'),
   'authenticated_select',has_table_privilege('authenticated',c.oid,'SELECT'),'authenticated_insert',has_table_privilege('authenticated',c.oid,'INSERT'),
   'authenticated_update',has_table_privilege('authenticated',c.oid,'UPDATE'),'authenticated_delete',has_table_privilege('authenticated',c.oid,'DELETE'),
   'public_grants',(select count(*) from aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a where a.grantee=0)))
   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('personal_inspections','personal_notes','personal_sync_receipts')),
 'functions',(select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,'security_definer',p.prosecdef,'config',p.proconfig,
   'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
   'public_execute',exists(select 1 from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a where a.grantee=0 and a.privilege_type='EXECUTE')))
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('defectrag_personal_sync_apply','defectrag_personal_sync_version','defectrag_personal_sync_note_version')),
 'triggers',(select jsonb_agg(jsonb_build_object('name',t.tgname,'enabled',t.tgenabled,'definition',pg_get_triggerdef(t.oid))) from pg_trigger t where not t.tgisinternal and t.tgname in ('personal_sync_version','personal_sync_note_version')),
 'policies',(select jsonb_agg(jsonb_build_object('schema',schemaname,'table',tablename,'name',policyname,'permissive',permissive,'roles',roles,'command',cmd,'using',qual,'check',with_check)) from pg_policies where (schemaname='public' and tablename in ('personal_inspections','personal_notes','personal_sync_receipts')) or (schemaname='storage' and tablename='objects')),
 'private_bucket',(select not public from storage.buckets where id='personal-inspections'),
 'owner_scan_index',exists(select 1 from pg_indexes where schemaname='public' and tablename='personal_inspections' and indexname='personal_sync_owner_id'),
 'staff_guard_definition',(select pg_get_functiondef(to_regprocedure('public.defectrag_is_staff()'))),
 'aal2_guard_definition',(select pg_get_functiondef(to_regprocedure('public.defectrag_has_aal2()'))),
 'sync_apply_definition',(select pg_get_functiondef(to_regprocedure('public.defectrag_personal_sync_apply(uuid,text,bigint,text,jsonb)')))
) as personal_sync_postflight;
