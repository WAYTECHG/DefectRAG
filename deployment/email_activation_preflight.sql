-- READ ONLY. Run before approving direct-notifications migration.
-- Return metadata/counts only; never paste keys, email addresses or payloads.
select registration_enabled,mfa_required
from public.defectrag_auth_settings where singleton;

select to_regclass('public.staff_notification_outbox') as outbox,
 to_regclass('public.notification_dispatch_clock') as new_clock,
 to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)') as new_claim,
 to_regprocedure('public.defectrag_prepare_email(uuid,uuid,jsonb)') as new_prepare;

select column_name,data_type,is_nullable from information_schema.columns
where table_schema='public' and table_name='staff_notification_outbox'
order by ordinal_position;

select c.relname,c.relrowsecurity,c.relforcerowsecurity,
 has_table_privilege('anon',c.oid,'SELECT') as anon_read,
 has_table_privilege('authenticated',c.oid,'SELECT') as signed_in_read,
 has_table_privilege('authenticated',c.oid,'UPDATE') as signed_in_update
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in ('staff_notification_outbox','notification_dispatch_clock');

select p.oid::regprocedure as function_signature,p.prosecdef as security_definer,p.proconfig as function_settings,
 has_function_privilege('anon',p.oid,'EXECUTE') as anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') as signed_in_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') as service_execute
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname in ('defectrag_claim_notifications','defectrag_finish_notification',
 'defectrag_claim_direct_notifications','defectrag_prepare_email','defectrag_notification_status','defectrag_can_manage_access');

select o.kind,o.status,count(*) as event_count
from public.staff_notification_outbox o group by o.kind,o.status order by o.kind,o.status;

-- Identifies only the existing controlled QA display name, without returning PII.
-- If this name is not the authorized test account, stop and choose it privately.
select count(*) as eligible_qa_events from public.staff_notification_outbox o
join public.staff_access_requests r on r.user_id=o.subject_id and r.version=o.version
join public.staff_members s on s.user_id=o.recipient_id
join auth.users u on u.id=s.user_id
where r.display_name='QA Registration' and r.status='pending' and o.kind='requested'
and o.status='queued' and o.attempts<8 and s.role='developer' and s.revoked_at is null and u.email_confirmed_at is not null;

select extname from pg_extension where extname in ('pg_cron','pg_net','supabase_vault');
-- Inspect existing scheduled job names/statuses in the dashboard separately;
-- do not export cron command text or Vault decrypted values.
