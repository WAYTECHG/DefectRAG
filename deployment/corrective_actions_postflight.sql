-- READ ONLY. Run after the separately approved corrective-action migration.
-- One result set; no account rows, notification payloads, keys or leases.
with target_tables as (
 select c.* from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relname in ('corrective_action_settings',
 'corrective_actions','corrective_action_history','corrective_action_events','corrective_action_effects')
), target_functions as (
 select p.* from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('defectrag_ca_staff','defectrag_ca_visible',
 'defectrag_create_corrective_action','defectrag_update_corrective_action',
 'defectrag_ca_schedule','defectrag_ca_claim','defectrag_ca_effect','defectrag_ca_finish')
)
select jsonb_build_object(
 'tables_present',(select count(*)=5 from target_tables),
 'rls_enabled',(select count(*)=5 and bool_and(relrowsecurity) from target_tables),
 'no_browser_direct_writes',(select count(*)=5 and bool_and(
 not has_table_privilege('authenticated',oid,'INSERT') and
 not has_table_privilege('authenticated',oid,'UPDATE') and
 not has_table_privilege('authenticated',oid,'DELETE') and
 not has_any_column_privilege('anon',oid,'SELECT')) from target_tables),
 'functions_present',(select count(*)=8 from target_functions),
 'assigned_editor_guard_present',(select count(*)=1 and bool_and(
 strpos(pg_get_functiondef(oid),'auth.uid() is distinct from c.owner_id and auth.uid() is distinct from c.supervisor_id')>0 and
 strpos(pg_get_functiondef(oid),'not coalesce(public.defectrag_is_developer(),false)')>0)
 from target_functions where proname='defectrag_update_corrective_action'),
 'definer_functions_fixed_search_path',(select count(*)=8 and bool_and(prosecdef and 'search_path=""'=any(proconfig)) from target_functions),
 'worker_rpcs_service_only',(select count(*)=4 and bool_and(
 has_function_privilege('service_role',oid,'EXECUTE') and
 not has_function_privilege('anon',oid,'EXECUTE') and
 not has_function_privilege('authenticated',oid,'EXECUTE')) from target_functions
 where proname in ('defectrag_ca_schedule','defectrag_ca_claim','defectrag_ca_effect','defectrag_ca_finish')),
 'staff_rpcs_authenticated_only',(select count(*)=4 and bool_and(
 has_function_privilege('authenticated',oid,'EXECUTE') and
 not has_function_privilege('anon',oid,'EXECUTE') and
 not has_function_privilege('service_role',oid,'EXECUTE')) from target_functions
 where proname in ('defectrag_ca_staff','defectrag_ca_visible','defectrag_create_corrective_action','defectrag_update_corrective_action')),
 'hidden_columns_not_granted',(select count(*)=4 and bool_and(not has_column_privilege('authenticated',table_schema||'.'||table_name,column_name,'SELECT'))
 from information_schema.columns where table_schema='public' and
 (table_name='corrective_action_events' and column_name in ('lease_token','lease_until')
 or table_name='corrective_action_effects' and column_name='receipt'
 or table_name='corrective_action_settings' and column_name='automation_enabled')),
 'policies',(select coalesce(jsonb_agg(jsonb_build_object('table',tablename,'name',policyname,'command',cmd,'roles',roles,'using',qual)),'[]')
 from pg_policies where schemaname='public' and tablename like 'corrective_action%'),
 'mfa_required',(select mfa_required from public.defectrag_auth_settings where singleton)
) as corrective_action_security;
-- Also inspect automation_enabled=false using an owner-only SELECT after the
-- table exists. This query deliberately remains safe before installation.
