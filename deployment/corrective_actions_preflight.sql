-- SELECT ONLY. No migration, claims, secrets, user details or notification payloads.
-- An empty new_objects/new_functions result is required before a FIRST install.
-- Counts/fingerprints are a preservation baseline, NOT a database backup.
select jsonb_build_object(
 'checked_at',now(),'postgres_version',current_setting('server_version'),
 'bootstrap_role',(select rolname from pg_roles where oid=10),
 'new_objects',(select coalesce(jsonb_agg(c.relname order by c.relname),'[]') from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relname in ('corrective_action_settings','corrective_actions','corrective_action_history','corrective_action_events','corrective_action_effects')),
 'new_functions',(select coalesce(jsonb_agg(p.oid::regprocedure::text order by p.proname),'[]') from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('defectrag_ca_staff','defectrag_ca_visible','defectrag_create_corrective_action','defectrag_update_corrective_action','defectrag_ca_schedule','defectrag_ca_claim','defectrag_ca_effect','defectrag_ca_finish')),
 'schema_usage',jsonb_build_object('authenticated',has_schema_privilege('authenticated','public','USAGE'),'service_role',has_schema_privilege('service_role','public','USAGE')),
 'auth_settings',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'dependencies',(select jsonb_agg(jsonb_build_object('table',table_name,'column',column_name,'type',data_type) order by table_name,ordinal_position) from information_schema.columns
 where table_schema='public' and table_name in ('shared_inspections','staff_notes','staff_members')),
 'referenced_keys',(select jsonb_agg(jsonb_build_object('table',conrelid::regclass::text,'definition',pg_get_constraintdef(oid))) from pg_constraint
 where contype in ('p','u') and conrelid in ('auth.users'::regclass,'public.staff_members'::regclass,'public.shared_inspections'::regclass,'public.staff_notes'::regclass)),
 'existing_policy_fingerprint',(select md5(coalesce(string_agg(row_to_json(p)::text,'|' order by schemaname,tablename,policyname),'')) from pg_policies p where schemaname in ('public','storage') and tablename not in ('corrective_action_settings','corrective_actions','corrective_action_history','corrective_action_events','corrective_action_effects')),
 'existing_trigger_fingerprint',(select md5(coalesce(string_agg(pg_get_triggerdef(t.oid),'|' order by n.nspname,c.relname,t.tgname),'')) from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where not t.tgisinternal and n.nspname in ('public','storage') and c.relname not in ('corrective_action_settings','corrective_actions','corrective_action_history','corrective_action_events','corrective_action_effects')),
 'existing_rpc_fingerprint',(select md5(coalesce(string_agg(p.oid::regprocedure::text||pg_get_functiondef(p.oid)||coalesce(p.proacl::text,''),'|' order by p.proname,p.oid),'')) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public'
 and p.proname in ('defectrag_is_staff','defectrag_is_developer','defectrag_has_aal2','defectrag_auth_status','defectrag_personal_sync_apply','defectrag_personal_action','defectrag_share_personal','defectrag_append_conversation','defectrag_acknowledge_review','defectrag_can_manage_access','defectrag_workspace_stats')),
 'existing_table_grants',(select jsonb_agg(jsonb_build_object('table',c.relname,'rls',c.relrowsecurity,'acl',c.relacl::text) order by c.relname) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('staff_members','staff_access_requests','shared_inspections','staff_notes','personal_inspections','personal_notes','personal_sync_receipts','defectrag_gallery_entries','staff_notification_outbox','notification_automation_settings')),
 'baseline_counts',jsonb_build_object('team',(select count(*) from public.shared_inspections),'team_notes',(select count(*) from public.staff_notes),'personal',(select count(*) from public.personal_inspections),'personal_notes',(select count(*) from public.personal_notes),'gallery',(select count(*) from public.defectrag_gallery_entries),'staff',(select count(*) from public.staff_members),'pending_requests',(select count(*) from public.staff_access_requests where status='pending')),
 'staff_fingerprint',(select md5(coalesce(string_agg(row_to_json(s)::text,'|' order by user_id),'')) from public.staff_members s),
 'private_bucket_inventory',(select jsonb_agg(jsonb_build_object('bucket',b.id,'public',b.public,'objects',(select count(*) from storage.objects o where o.bucket_id=b.id))) from storage.buckets b where b.id in ('personal-inspections','team-inspections')),
 'developer_email_automation',(select enabled from public.notification_automation_settings where singleton),
 'developer_email_cron',(select coalesce(jsonb_agg(jsonb_build_object('name',jobname,'active',active,'schedule',schedule)),'[]') from cron.job where jobname='defectrag-developer-notifications')
) as stage1_preflight;
