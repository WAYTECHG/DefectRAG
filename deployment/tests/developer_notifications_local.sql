-- ISOLATED DISPOSABLE DATABASE ONLY. Synthetic users; no provider/network calls.
-- Minimal contract fixture, NOT a substitute for real Supabase Auth/RLS tests.
\set ON_ERROR_STOP on
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth;
create function auth.role() returns text language sql stable as $$
 select current_setting('request.jwt.claims',true)::jsonb->>'role'; $$;
grant usage on schema auth to anon,authenticated,service_role;
create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz);
create table public.staff_members(user_id uuid primary key,role text,revoked_at timestamptz);
create table public.staff_access_requests(user_id uuid primary key,display_name text,status text,version integer,created_at timestamptz default now());
create table public.staff_notification_outbox(
 id uuid primary key,subject_id uuid,recipient_id uuid,version integer,kind text,status text default 'queued',
 attempts integer default 0,next_attempt_at timestamptz default now(),lease_token uuid,lease_until timestamptz,
 last_error text,created_at timestamptz default now(),delivered_at timestamptz);
\ir supabase_direct_notifications.sql
\ir supabase_developer_notifications.sql

begin;
insert into auth.users values
 ('10000000-0000-4000-8000-000000000001','developer@example.invalid',now()),
 ('10000000-0000-4000-8000-000000000002','applicant@example.invalid',now()),
 ('10000000-0000-4000-8000-000000000003','other@example.invalid',now());
insert into public.staff_members values('10000000-0000-4000-8000-000000000001','developer',null);
insert into public.staff_access_requests values('10000000-0000-4000-8000-000000000002','Fixture','pending',2,now());
-- One due valid row plus old backlog, applicant mail, other recipient and stale version.
insert into public.staff_notification_outbox(id,subject_id,recipient_id,version,kind,created_at) values
 ('20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001',2,'requested',now()),
 ('20000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001',2,'requested',now()-interval '1 day'),
 ('20000000-0000-4000-8000-000000000003','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000002',2,'approved',now()),
 ('20000000-0000-4000-8000-000000000004','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000003',2,'requested',now()),
 ('20000000-0000-4000-8000-000000000005','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001',1,'requested',now());
do $$ begin
 if has_function_privilege('anon','public.defectrag_claim_developer_notifications(text)','EXECUTE')
 or has_function_privilege('authenticated','public.defectrag_claim_developer_notifications(text)','EXECUTE')
 or not has_function_privilege('service_role','public.defectrag_claim_developer_notifications(text)','EXECUTE')
 then raise exception 'RPC grants invalid'; end if;
 if has_table_privilege('authenticated','public.notification_automation_settings','SELECT')
 or has_table_privilege('service_role','public.notification_automation_settings','UPDATE')
 then raise exception 'Private settings exposed'; end if;
end $$;
set local role anon;
do $$ begin
 begin perform public.defectrag_claim_developer_notifications('developer@example.invalid');
 raise exception 'Anonymous access allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated"}',true);
set local role authenticated;
do $$ begin
 begin perform public.defectrag_claim_developer_notifications('developer@example.invalid');
 raise exception 'Authenticated access allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Disabled gate bypass';end if;
end $$;
reset role;
update public.notification_automation_settings set enabled=true,enabled_at=now()-interval '1 minute',claims_today=80 where singleton;
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Daily cap bypass';end if;
end $$;
reset role;
-- Yesterday's cap resets today; one valid event is leased.
update public.notification_automation_settings set budget_day=(now() at time zone 'UTC')::date-1 where singleton;
set local role service_role;
select set_config('test.developer_jobs',public.defectrag_claim_developer_notifications('DEVELOPER@example.invalid')::text,true);
do $$ declare jobs jsonb:=current_setting('test.developer_jobs')::jsonb;begin
 if jsonb_array_length(jobs)<>1 or jobs->0->>'event_id'<>'20000000-0000-4000-8000-000000000001' then raise exception 'Wrong event selected';end if;
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Duplicate active lease';end if;
end $$;
reset role;
do $$ begin
 if (select claims_today from public.notification_automation_settings where singleton)<>1 then raise exception 'Daily accounting invalid';end if;
 if exists(select 1 from public.staff_notification_outbox where id<>'20000000-0000-4000-8000-000000000001' and (status<>'queued' or attempts<>0)) then raise exception 'Unrelated rows changed';end if;
end $$;
-- Failed attempt remains queued until backoff, then consumes another daily slot.
update public.staff_notification_outbox set status='queued',lease_token=null,lease_until=null,next_attempt_at=now()+interval '1 hour' where id='20000000-0000-4000-8000-000000000001';
update public.notification_dispatch_clock set next_claim_at='-infinity' where singleton;
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Backoff ignored';end if;
end $$;
reset role;
update public.staff_notification_outbox set next_attempt_at=now()-interval '1 minute' where id='20000000-0000-4000-8000-000000000001';
set local role service_role;
do $$ begin
 if jsonb_array_length(public.defectrag_claim_developer_notifications('developer@example.invalid'))<>1 then raise exception 'Due retry not selected';end if;
end $$;
reset role;
do $$ begin
 if (select claims_today from public.notification_automation_settings where singleton)<>2
 or (select attempts from public.staff_notification_outbox where id='20000000-0000-4000-8000-000000000001')<>2
 then raise exception 'Retry daily accounting incorrect';end if;
end $$;
-- Successful sent status excludes future claims; no duplicate event reset in production.
update public.staff_notification_outbox set status='sent',lease_token=null,lease_until=null where id='20000000-0000-4000-8000-000000000001';
update public.notification_dispatch_clock set next_claim_at='-infinity' where singleton;
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Sent event repeated';end if;
end $$;
reset role;
-- Test revocation and non-Pending/current-version boundaries without any send.
update public.staff_notification_outbox set status='queued' where id='20000000-0000-4000-8000-000000000001';
update public.staff_members set revoked_at=now() where user_id='10000000-0000-4000-8000-000000000001';
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Revoked developer selected';end if;
end $$;
reset role;
update public.staff_members set revoked_at=null where user_id='10000000-0000-4000-8000-000000000001';
update public.staff_access_requests set status='approved' where user_id='10000000-0000-4000-8000-000000000002';
set local role service_role;
do $$ begin
 if public.defectrag_claim_developer_notifications('developer@example.invalid')<>'[]'::jsonb then raise exception 'Non-Pending request selected';end if;
end $$;
reset role;
rollback;
select 'developer notification SQL contract tests passed' as result;
