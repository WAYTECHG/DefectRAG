-- ONE SELECT ONLY: no secrets, claims, sends, activation or schema changes.
select jsonb_build_object(
 'extensions',(select coalesce(jsonb_object_agg(extname,extversion),'{}') from pg_extension where extname in ('pg_cron','pg_net','supabase_vault')),
 'cron_jobs_available',to_regclass('cron.job') is not null,
 'vault_available',to_regclass('vault.decrypted_secrets') is not null,
 'net_post_available',to_regprocedure('net.http_post(text,jsonb,jsonb,jsonb,integer)') is not null,
 'auth_flags',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'clock_fix_present',(select position($fixed$where singleton;$fixed$ in prosrc)>0 from pg_proc where oid=to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)')),
 'automation_settings_exist',to_regclass('public.notification_automation_settings') is not null,
 'developer_claim_exists',to_regprocedure('public.defectrag_claim_developer_notifications(text)') is not null,
 'queue_counts',(select coalesce(jsonb_agg(t),'[]') from (select kind,status,count(*) from public.staff_notification_outbox group by kind,status order by kind,status) t),
 'active_verified_developers',(select count(*) from public.staff_members m join auth.users u on u.id=m.user_id where m.role='developer' and m.revoked_at is null and u.email_confirmed_at is not null)
) as automation_preflight;
