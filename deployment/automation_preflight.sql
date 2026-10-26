-- READ ONLY metadata. Do not paste keys, applicant rows or auth.users results.
select name,setting from pg_settings where name in ('server_version','server_version_num');
select to_regclass('public.staff_access_requests') as requests,
 to_regclass('public.staff_notification_outbox') as notifications,
 to_regclass('public.shared_inspections') as team_inspections,
 to_regclass('public.staff_notes') as human_reviews,
 to_regclass('public.personal_inspections') as personal,
 to_regclass('public.corrective_actions') as proposed_cases;
select table_name,column_name,data_type from information_schema.columns
where table_schema='public' and table_name in ('staff_members','staff_access_requests','staff_notification_outbox','shared_inspections','staff_notes')
order by table_name,ordinal_position;
select p.oid::regprocedure as function,p.prosecdef as security_definer,
 has_function_privilege('anon',p.oid,'execute') as anon_execute,
 has_function_privilege('authenticated',p.oid,'execute') as authenticated_execute,
 has_function_privilege('service_role',p.oid,'execute') as service_execute
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname in ('defectrag_has_aal2','defectrag_is_staff','defectrag_can_manage_access','defectrag_claim_notifications','defectrag_finish_notification','defectrag_claim_direct_notifications','defectrag_prepare_email','defectrag_ca_staff','defectrag_ca_effect','defectrag_ca_finish');
select registration_enabled,mfa_required from public.defectrag_auth_settings where singleton;
select kind,status,count(*) as events from public.staff_notification_outbox group by kind,status;
select schemaname,tablename,policyname,roles,cmd from pg_policies
where schemaname='public' and (tablename like 'corrective_action%' or tablename='staff_notification_outbox');
