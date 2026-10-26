-- REVIEW ONLY: reversible pause; no data/extension/job deletion.
-- Also set Edge DEFECTRAG_NOTIFICATIONS_ENABLED=0 first where possible.
begin;
update public.notification_automation_settings set enabled=false where singleton;
do $$ begin
 perform cron.alter_job(jobid,active:=false) from cron.job where jobname='defectrag-developer-notifications';
end $$;
commit;
