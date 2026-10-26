-- REVIEW ONLY: separate approval required; installs an INACTIVE five-minute job.
-- Requires pg_cron, pg_net and Vault already enabled, plus developer migration.
-- No extension installation, Vault write, credential literal, send or activation.
begin;
set local lock_timeout='5s';
set local statement_timeout='20s';
do $$ begin
 if to_regclass('cron.job') is null or to_regclass('vault.decrypted_secrets') is null
 or to_regprocedure('net.http_post(text,jsonb,jsonb,jsonb,integer)') is null
 or to_regclass('public.notification_automation_settings') is null
 then raise exception 'STOP: scheduler prerequisites missing'; end if;
 if exists(select 1 from cron.job where jobname='defectrag-developer-notifications')
 then raise exception 'STOP: job already exists; inspect instead of replacing'; end if;
end $$;
create table public.notification_automation_http_log (
 request_id bigint primary key, created_at timestamptz not null default now()
);
alter table public.notification_automation_http_log enable row level security;
revoke all on public.notification_automation_http_log from public,anon,authenticated,service_role;
create function public.defectrag_enqueue_developer_notifications() returns bigint
language plpgsql security definer set search_path='' as $$
declare cfg public.notification_automation_settings; bearer text; request_id bigint;
begin
 select * into strict cfg from public.notification_automation_settings where singleton for update;
 if not cfg.enabled or cfg.enabled_at is null or cfg.last_enqueued_at>now()-interval '2 minutes'
 or cfg.budget_day=(now() at time zone 'UTC')::date and cfg.claims_today>=80
 then return null; end if;
 -- Avoid network traffic when there is no current, due Developer request.
 if not exists(select 1 from public.staff_notification_outbox o
  join public.staff_access_requests r on r.user_id=o.subject_id and r.version=o.version and r.status='pending'
  join public.staff_members m on m.user_id=o.recipient_id and m.role='developer' and m.revoked_at is null
  join auth.users u on u.id=m.user_id and u.email_confirmed_at is not null
  where o.kind='requested' and o.created_at>=cfg.enabled_at and o.attempts<8
   and (o.status='queued' and o.next_attempt_at<=now() or o.status='sending' and o.lease_until<now()))
 then return null; end if;
 -- Count and value are used internally only; never output or log credentials.
 if (select count(*) from vault.decrypted_secrets where name='defectrag_notification_worker_bearer')<>1
 then raise exception 'Notification worker Vault secret missing or duplicated'; end if;
 select decrypted_secret into bearer from vault.decrypted_secrets where name='defectrag_notification_worker_bearer';
 if bearer is null or length(bearer)<32 then raise exception 'Notification worker Vault secret invalid'; end if;
 select net.http_post(
  url:='https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/hyper-worker',
  headers:=jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||bearer),
  body:='{}'::jsonb,timeout_milliseconds:=110000) into request_id;
 insert into public.notification_automation_http_log(request_id) values(request_id);
 update public.notification_automation_settings set last_enqueued_at=now() where singleton;
 return request_id;
end; $$;
-- Cron's existing postgres owner executes this. No browser/worker role may call it.
revoke all on function public.defectrag_enqueue_developer_notifications() from public,anon,authenticated,service_role;
do $$ declare new_job bigint; begin
 select cron.schedule('defectrag-developer-notifications','*/5 * * * *',
  'select public.defectrag_enqueue_developer_notifications();') into new_job;
 perform cron.alter_job(new_job,active:=false);
end $$;
commit;
