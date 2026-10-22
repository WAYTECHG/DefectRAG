-- REVIEW ONLY. ACTIVATES recurring delivery: explicit separate approval required.
-- Prerequisite: reviewed extensions/migrations, exact worker bundle/config,
-- saved private Vault bearer, disabled-job verification and recipient match.
-- Keep Edge DEFECTRAG_NOTIFICATIONS_ENABLED=0 until this transaction is verified.
-- No backlog before the initial activation timestamp is eligible.
begin;
set local lock_timeout='5s';
do $$ begin
 if (select count(*) from vault.secrets where name='defectrag_notification_worker_bearer')<>1
 then raise exception 'STOP: Vault worker credential missing/duplicated';end if;
 if (select count(*) from cron.job where jobname='defectrag-developer-notifications')<>1
 then raise exception 'STOP: exact inactive job missing/duplicated';end if;
 if exists(select 1 from cron.job where jobname='defectrag-developer-notifications'
  and (active or schedule<>'*/5 * * * *' or command<>'select public.defectrag_enqueue_developer_notifications();' or username<>current_user))
 then raise exception 'STOP: schedule differs or is already active';end if;
 if not exists(select 1 from public.notification_automation_settings where singleton and not enabled)
 then raise exception 'STOP: database dispatch is missing or already enabled';end if;
 update public.notification_automation_settings set enabled=true,enabled_at=coalesce(enabled_at,clock_timestamp()) where singleton;
 perform cron.alter_job((select jobid from cron.job where jobname='defectrag-developer-notifications'),active:=true);
end $$;
commit;
