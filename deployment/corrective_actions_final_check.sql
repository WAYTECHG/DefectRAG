-- SELECT ONLY: final native-QA preservation and automation checks.
with installed as (
-- READ ONLY: installation, disabled automation and preservation in one result.
SELECT jsonb_build_object(
 'security',(SELECT corrective_action_security FROM (
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
) as corrective_action_security
) s),
 'automation_enabled',(SELECT automation_enabled FROM public.corrective_action_settings WHERE singleton),
 'new_record_counts',jsonb_build_object('cases',(SELECT count(*) FROM public.corrective_actions),'history',(SELECT count(*) FROM public.corrective_action_history),'events',(SELECT count(*) FROM public.corrective_action_events),'effects',(SELECT count(*) FROM public.corrective_action_effects)),
 'preservation',(SELECT stage1_preflight FROM (
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
) as stage1_preflight
) p)
) AS corrective_install_check
), qa_result as (
-- SELECT ONLY. Dedicated disposable case; no row payloads, recipients or leases.
-- Run after the native live QA lifecycle; never claims events or activates delivery.
with qa as (
 select * from public.corrective_actions
 where id='7ce36833-4300-4c7f-a3df-b9b8356a0d1d'::uuid
)
select jsonb_build_object(
 'case_count',(select count(*) from qa),
 'automation_enabled',(select automation_enabled from public.corrective_action_settings where singleton),
 'case',(select jsonb_build_object('id',id,'state',state,'version',version,
   'resolved',resolved_at is not null,'closed',closed_at is not null,
   'owner_matches_supervisor',owner_id=supervisor_id) from qa),
 'audit',(select jsonb_build_object('rows',count(*),'distinct_versions',count(distinct h.version),
   'first_version',min(h.version),'last_version',max(h.version),
   'actors',count(distinct h.actor_id))
   from public.corrective_action_history h join qa q on q.id=h.case_id),
 'events',(select jsonb_build_object('rows',count(*),'attempts',coalesce(sum(e.attempts),0),
   'all_queued',coalesce(bool_and(e.status='queued'),false))
   from public.corrective_action_events e join qa q on q.id=e.case_id),
 'effects',(select count(*) from public.corrective_action_effects f
   join public.corrective_action_events e on e.id=f.event_id join qa q on q.id=e.case_id),
 'qa_records',jsonb_build_object(
   'personal',(select count(*) from public.personal_inspections i join qa q on q.inspection_id=i.id),
   'team',(select count(*) from public.shared_inspections i join qa q on q.inspection_id=i.id),
   'personal_notes',(select count(*) from public.personal_notes n join qa q on q.inspection_id=n.inspection_id),
   'team_notes',(select count(*) from public.staff_notes n join qa q on q.inspection_id=n.inspection_id),
   'private_objects',(select count(*) from storage.objects o join qa q on split_part(o.name,'/',2)=q.inspection_id where o.bucket_id='personal-inspections'),
   'team_objects',(select count(*) from storage.objects o join qa q on split_part(o.name,'/',2)=q.inspection_id where o.bucket_id='team-inspections')),
 'non_qa_counts',jsonb_build_object(
   'personal',(select count(*) from public.personal_inspections i where not exists(select 1 from qa q where q.inspection_id=i.id)),
   'team',(select count(*) from public.shared_inspections i where not exists(select 1 from qa q where q.inspection_id=i.id)),
   'personal_notes',(select count(*) from public.personal_notes n where not exists(select 1 from qa q where q.inspection_id=n.inspection_id)),
   'team_notes',(select count(*) from public.staff_notes n where not exists(select 1 from qa q where q.inspection_id=n.inspection_id)),
   'gallery',(select count(*) from public.defectrag_gallery_entries),
   'staff',(select count(*) from public.staff_members),
   'pending_requests',(select count(*) from public.staff_access_requests where status='pending'))
) as corrective_live_qa_check
)
select jsonb_build_object(
  'installation',(select corrective_install_check from installed),
  'qa',(select corrective_live_qa_check from qa_result)
) as corrective_final_check;
