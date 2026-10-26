-- READ ONLY. No password hashes, Vault values, SQL query text, or client IPs.
-- This is a baseline, not a backup or proof of absence of offline clients.
select jsonb_build_object(
 'checked_at',now(),'server_version',current_setting('server_version'),
 'auth_flags',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'record_counts',jsonb_build_object('personal',(select count(*) from public.personal_inspections),'team',(select count(*) from public.shared_inspections),'team_notes',(select count(*) from public.staff_notes),'gallery',(select count(*) from public.defectrag_gallery_entries),'staff',(select count(*) from public.staff_members)),
 'staff_fingerprint',(select md5(coalesce(string_agg(row_to_json(s)::text,'|' order by user_id),'')) from public.staff_members s),
 'developer_notifications_enabled',(select enabled from public.notification_automation_settings where singleton),
 'developer_scheduler',(select coalesce(jsonb_agg(jsonb_build_object('active',active,'schedule',schedule,'expected_command',btrim(command)='select public.defectrag_enqueue_developer_notifications();')),'[]') from cron.job where jobname='defectrag-developer-notifications'),
 'postgres_clients',(select coalesce(jsonb_agg(to_jsonb(a)),'[]') from (
 select coalesce(nullif(application_name,''),'unspecified') as application,state,count(*) as connections
 from pg_stat_activity where datname=current_database() and usename='postgres' and backend_type='client backend' and pid<>pg_backend_pid()
 group by application_name,state order by application_name,state) a),
 'corrective_tables_installed',(select count(*) from pg_tables where schemaname='public' and tablename in ('corrective_action_settings','corrective_actions','corrective_action_history','corrective_action_events','corrective_action_effects'))
) as rotation_baseline;
