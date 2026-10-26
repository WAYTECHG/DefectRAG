-- REVIEW ONLY. Separate production approval required. No sends or activation.
-- Prerequisite: existing auth/direct-email SQL and approved clock WHERE fix.
-- Does not change existing functions, records, auth flags, staff or storage RLS.
begin;
set local lock_timeout='5s';
set local statement_timeout='20s';
do $$ begin
 if to_regprocedure('public.defectrag_prepare_email(uuid,uuid,jsonb)') is null
 or not exists(select 1 from pg_proc where oid=to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)')
  and position($fixed$update public.notification_dispatch_clock set next_claim_at=now()+interval '30 seconds' where singleton;$fixed$ in prosrc)>0)
 then raise exception 'STOP: direct email prerequisites/clock fix missing'; end if;
end $$;
create table public.notification_automation_settings (
 singleton boolean primary key default true check(singleton),
 enabled boolean not null default false,
 enabled_at timestamptz,
 budget_day date not null default (now() at time zone 'UTC')::date,
 claims_today integer not null default 0 check(claims_today between 0 and 80),
 last_enqueued_at timestamptz,
 check(not enabled or enabled_at is not null)
);
insert into public.notification_automation_settings(singleton) values(true);
alter table public.notification_automation_settings enable row level security;
revoke all on public.notification_automation_settings from public,anon,authenticated,service_role;

-- Exact recipient is server configuration, not caller-supplied frontend input.
-- Filtering BEFORE claiming prevents unrelated applicant events being consumed.
-- A maximum 80 leased attempts/day (including retries) leaves provider headroom;
-- this is application-local and does not account for other uses of the Resend key.
create function public.defectrag_claim_developer_notifications(p_recipient text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare cfg public.notification_automation_settings; selected_id uuid; jobs jsonb;
 today date := (now() at time zone 'UTC')::date;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 if p_recipient is null or length(p_recipient)>254 or p_recipient!~'^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'
 then raise exception 'Invalid developer recipient'; end if;
 select * into strict cfg from public.notification_automation_settings where singleton for update;
 if not cfg.enabled or cfg.enabled_at is null then return '[]'::jsonb; end if;
 if cfg.budget_day<>today then
  update public.notification_automation_settings set budget_day=today,claims_today=0 where singleton;
  cfg.claims_today:=0;
 end if;
 if cfg.claims_today>=80 then return '[]'::jsonb; end if;
 select o.id into selected_id from public.staff_notification_outbox o
 join public.staff_access_requests r on r.user_id=o.subject_id and r.version=o.version and r.status='pending'
 join public.staff_members m on m.user_id=o.recipient_id and m.role='developer' and m.revoked_at is null
 join auth.users u on u.id=m.user_id and u.email_confirmed_at is not null
 where o.kind='requested' and lower(u.email)=lower(p_recipient) and o.created_at>=cfg.enabled_at
  and o.attempts<8 and (o.status='queued' and o.next_attempt_at<=now() or o.status='sending' and o.lease_until<now())
 order by o.created_at,o.id limit 1 for update of o skip locked;
 if selected_id is null then return '[]'::jsonb; end if;
 jobs:=public.defectrag_claim_direct_notifications(1,selected_id);
 if jsonb_array_length(jobs)>0 then
  update public.notification_automation_settings set claims_today=claims_today+1 where singleton;
 end if;
 return jobs;
end; $$;
revoke all on function public.defectrag_claim_developer_notifications(text) from public,anon,authenticated,service_role;
grant execute on function public.defectrag_claim_developer_notifications(text) to service_role;
commit;
