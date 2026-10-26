-- LOCAL ISOLATED SUPABASE ONLY; NOT EXECUTED by the activation preflight.
-- Requires base Auth/MFA + proposed direct-notifications migration in local DB.
-- Run as local administrator with psql ON_ERROR_STOP=1. No HTTP/email calls.
-- Synthetic JWT claims test SQL permissions, not actual Auth sign-in. ROLLBACK.
-- Requires the pg-safeupdate library already loaded in this ISOLATED local DB.
-- Probe below fails closed if its protection is not actually active.
begin;
set local safeupdate.enabled='on';
create temporary table qa_notification_clock_guard (singleton boolean primary key,value integer);
insert into qa_notification_clock_guard values(true,0);
do $safeupdate_probe$ begin
 begin
  update pg_temp.qa_notification_clock_guard set value=1;
  raise exception 'safeupdate is not active; regression test would be invalid';
 exception when sqlstate '21000' then null;
 end;
 update pg_temp.qa_notification_clock_guard set value=1 where singleton;
 if (select value from pg_temp.qa_notification_clock_guard where singleton)<>1 then
  raise exception 'Scoped update failed'; end if;
end; $safeupdate_probe$;
insert into auth.users(id,aud,role,email,email_confirmed_at,raw_app_meta_data,raw_user_meta_data) values
 ('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','authenticated','authenticated','email-dev@example.invalid',now(),'{}','{}'),
 ('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','authenticated','authenticated','email-qa@example.invalid',now(),'{}','{}'),
 ('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','authenticated','authenticated','email-other@example.invalid',now(),'{}','{}');
insert into public.staff_members(user_id,display_name,role) values('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','Email fixture Developer','developer');
insert into public.staff_access_requests(user_id,display_name,version) values
 ('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','Email fixture QA',1),
 ('eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','Email fixture other',2);
insert into public.staff_notification_outbox(id,subject_id,recipient_id,version,kind) values
 ('ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1','eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',1,'requested'),
 ('ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',1,'requested');
set local role anon;
do $$ begin
 begin perform public.defectrag_claim_direct_notifications(1,'ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1');raise exception 'Anonymous claim allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"eaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal1"}',true);
set local role authenticated;
do $$ begin
 begin perform public.defectrag_claim_direct_notifications(1,'ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1');raise exception 'Applicant claim allowed';exception when insufficient_privilege then null;end;
 begin perform 1 from public.staff_notification_outbox;raise exception 'Applicant outbox read allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
update public.notification_dispatch_clock set next_claim_at='-infinity' where singleton;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select set_config('test.email_jobs',public.defectrag_claim_direct_notifications(1,'ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1')::text,true);
do $$ declare j jsonb:=current_setting('test.email_jobs')::jsonb; e jsonb; snapshot jsonb; begin
 if jsonb_array_length(j)<>1 then raise exception 'Expected exactly one selected event';end if;e:=j->0;
 if e->>'event_id'<>'ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1' then raise exception 'Wrong event claimed';end if;
 snapshot:=public.defectrag_prepare_email((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'{"from":"onboarding@resend.dev","to":["email-dev@example.invalid"],"subject":"Fixture","text":"immutable body"}');
 if snapshot->'payload'->>'text'<>'immutable body' then raise exception 'Snapshot missing';end if;
 snapshot:=public.defectrag_prepare_email((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'{"text":"changed body"}');
 if snapshot->'payload'->>'text'<>'immutable body' then raise exception 'Retry changed provider body';end if;
 if public.defectrag_prepare_email((e->>'event_id')::uuid,null,'{}') is not null then raise exception 'Missing lease accepted';end if;
 if public.defectrag_claim_direct_notifications(1,'ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1')<>'[]'::jsonb then raise exception 'Claim clock ignored';end if;
end $$;
reset role;
do $$ begin
 if (select status from public.staff_notification_outbox where id='ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2')<>'queued' then raise exception 'QA maintenance modified unrelated stale event';end if;
end $$;
-- Emulate elapsed time only in rollback fixture; no production clock/state edit.
update public.staff_notification_outbox set email_first_attempt_at=now()-interval '24 hours' where id='ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
set local role service_role;
do $$ declare e jsonb:=(current_setting('test.email_jobs')::jsonb)->0;begin
 if public.defectrag_prepare_email((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'{}') is not null then raise exception 'Expired idempotency ambiguity allowed';end if;
end $$;
reset role;
do $$ begin
 if not exists(select 1 from public.staff_notification_outbox where id='ebbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1' and status='dead' and last_error='email_ambiguity_manual_review') then raise exception 'Expired ambiguity not quarantined';end if;
end $$;
rollback;
