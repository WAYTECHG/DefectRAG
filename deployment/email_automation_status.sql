-- ONE SELECT ONLY after installation. No secrets, claims, retry or dispatch calls.
select jsonb_build_object(
 'settings',(select jsonb_build_object('enabled',enabled,'enabled_at',enabled_at,'budget_day',budget_day,'claims_today',claims_today,'last_enqueued_at',last_enqueued_at) from public.notification_automation_settings where singleton),
 'job',(select jsonb_build_object('count',count(*),'active',coalesce(bool_or(active),false),'five_minute_schedule',coalesce(bool_and(schedule='*/5 * * * *'),false),'expected_command',coalesce(bool_and(command='select public.defectrag_enqueue_developer_notifications();'),false)) from cron.job where jobname='defectrag-developer-notifications'),
 'vault_worker_secret_present',(select count(*)=1 from vault.secrets where name='defectrag_notification_worker_bearer'),
 'worker_rpc_permissions',(select jsonb_build_object('security_definer',prosecdef,'anonymous',has_function_privilege('anon',oid,'EXECUTE'),'signed_in',has_function_privilege('authenticated',oid,'EXECUTE'),'worker',has_function_privilege('service_role',oid,'EXECUTE')) from pg_proc where oid=to_regprocedure('public.defectrag_claim_developer_notifications(text)')),
 'scheduler_permissions',(select jsonb_build_object('anonymous',has_function_privilege('anon',oid,'EXECUTE'),'signed_in',has_function_privilege('authenticated',oid,'EXECUTE'),'worker',has_function_privilege('service_role',oid,'EXECUTE')) from pg_proc where oid=to_regprocedure('public.defectrag_enqueue_developer_notifications()')),
 'recent_http',(select coalesce(jsonb_agg(t),'[]') from (select l.request_id,l.created_at,r.status_code,r.timed_out,r.error_msg is not null as error_present from public.notification_automation_http_log l left join net._http_response r on r.id=l.request_id order by l.created_at desc limit 10) t),
 'auth_flags',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton)
) as automation_status;
