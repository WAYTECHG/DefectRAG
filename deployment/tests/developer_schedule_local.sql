-- DISPOSABLE LOCAL DATABASE ONLY, AFTER developer_notifications_local.sql.
-- Real PostgreSQL function/grant execution; fake cron/net/Vault contracts.
-- Does NOT test native pg_cron/pg_net execution, HTTP or real credentials.
\set ON_ERROR_STOP on
create schema cron;
create schema net;
create schema vault;
create table cron.job(jobid bigint generated always as identity primary key,jobname text,schedule text,command text,active boolean,username text default current_user);
create function cron.schedule(text,text,text) returns bigint language sql as $$
 insert into cron.job(jobname,schedule,command,active) values($1,$2,$3,true) returning jobid; $$;
create function cron.alter_job(job_id bigint,active boolean) returns void language sql as $$
 update cron.job set active=$2 where jobid=$1; $$;
create table vault.decrypted_secrets(name text,decrypted_secret text);
create view vault.secrets as select name from vault.decrypted_secrets;
create table net.fixture_requests(id bigint generated always as identity primary key,url text,body jsonb,headers jsonb,timeout_ms integer);
create function net.http_post(url text,body jsonb default '{}',params jsonb default '{}',headers jsonb default '{}',timeout_milliseconds integer default 1000)
returns bigint language sql as $$
 insert into net.fixture_requests(url,body,headers,timeout_ms) values($1,$2,$4,$5) returning id; $$;
\ir supabase_developer_notification_schedule.sql
do $$ begin
 if (select active from cron.job where jobname='defectrag-developer-notifications') then raise exception 'Job activated by installation';end if;
 if has_function_privilege('anon','public.defectrag_enqueue_developer_notifications()','EXECUTE')
 or has_function_privilege('authenticated','public.defectrag_enqueue_developer_notifications()','EXECUTE')
 or has_function_privilege('service_role','public.defectrag_enqueue_developer_notifications()','EXECUTE')
 then raise exception 'Scheduler exposed';end if;
 if public.defectrag_enqueue_developer_notifications() is not null then raise exception 'Disabled scheduler sent';end if;
end $$;
insert into auth.users values
 ('30000000-0000-4000-8000-000000000001','developer@example.invalid',now()),
 ('30000000-0000-4000-8000-000000000002','applicant@example.invalid',now());
insert into public.staff_members values('30000000-0000-4000-8000-000000000001','developer',null);
insert into public.staff_access_requests values('30000000-0000-4000-8000-000000000002','Fixture','pending',1,now());
insert into public.staff_notification_outbox(id,subject_id,recipient_id,version,kind) values
 ('40000000-0000-4000-8000-000000000001','30000000-0000-4000-8000-000000000002','30000000-0000-4000-8000-000000000001',1,'requested');
update public.notification_automation_settings set enabled=true,enabled_at=now()-interval '1 minute' where singleton;
do $$ begin
 begin perform public.defectrag_enqueue_developer_notifications();raise exception 'Missing Vault credential allowed';
 exception when raise_exception then if sqlerrm<>'Notification worker Vault secret missing or duplicated' then raise;end if;end;
 if exists(select 1 from net.fixture_requests) then raise exception 'Network queued without credential';end if;
end $$;
insert into vault.decrypted_secrets values('defectrag_notification_worker_bearer','fixture-worker-bearer-not-a-real-secret-32-chars');
do $$ declare fixture_request_id bigint;begin
 fixture_request_id:=public.defectrag_enqueue_developer_notifications();
 if fixture_request_id is null or not exists(select 1 from net.fixture_requests where fixture_requests.id=fixture_request_id
  and url='https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/hyper-worker'
  and headers->>'Authorization'='Bearer fixture-worker-bearer-not-a-real-secret-32-chars'
  and body='{}'::jsonb and timeout_ms=110000) then raise exception 'Incorrect dispatch contract';end if;
 if public.defectrag_enqueue_developer_notifications() is not null then raise exception 'Enqueue throttle bypass';end if;
 if (select count(*) from public.notification_automation_http_log)<>1 then raise exception 'Request ID not recorded';end if;
 if exists(select 1 from cron.job where command like '%fixture-worker%' or command like '%Bearer%') then raise exception 'Credential in cron command';end if;
end $$;
update public.notification_automation_settings set last_enqueued_at=null,claims_today=80 where singleton;
do $$ begin
 if public.defectrag_enqueue_developer_notifications() is not null then raise exception 'Scheduler daily cap bypass';end if;
end $$;
update public.notification_automation_settings set claims_today=0 where singleton;
update public.staff_access_requests set status='approved' where user_id='30000000-0000-4000-8000-000000000002';
do $$ begin
 if public.defectrag_enqueue_developer_notifications() is not null then raise exception 'No-due-work scheduler invoked';end if;
 if (select count(*) from net.fixture_requests)<>1 then raise exception 'Unexpected extra dispatch';end if;
end $$;
select 'scheduler SQL contracts passed; native extensions/network NOT tested' as result;
update public.notification_automation_settings set enabled=false,enabled_at=null where singleton;
\ir email_automation_enable.sql
do $$ begin
 if not exists(select 1 from public.notification_automation_settings where singleton and enabled and enabled_at is not null) then raise exception 'Activation failed';end if;
 if not (select active from cron.job where jobname='defectrag-developer-notifications') then raise exception 'Cron activation failed';end if;
 if (select count(*) from net.fixture_requests)<>1 then raise exception 'Activation itself dispatched';end if;
end $$;
\ir email_automation_pause.sql
do $$ begin
 if exists(select 1 from public.notification_automation_settings where enabled) or exists(select 1 from cron.job where active) then raise exception 'Pause failed';end if;
end $$;
select 'guarded activation and non-destructive pause contracts passed' as result;
