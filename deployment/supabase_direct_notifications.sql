-- REVIEW ONLY. Additive; requires the already-applied supabase_auth_mfa.sql.
-- No scheduler, secrets, email dispatch or authentication flag changes here.
begin;
alter table public.staff_notification_outbox add column email_payload jsonb;
alter table public.staff_notification_outbox add column email_first_attempt_at timestamptz;
create table public.notification_dispatch_clock (
 singleton boolean primary key default true check(singleton),
 next_claim_at timestamptz not null default '-infinity'
);
insert into public.notification_dispatch_clock(singleton) values(true);
alter table public.notification_dispatch_clock enable row level security;
revoke all on public.notification_dispatch_clock from public,anon,authenticated,service_role;

create function public.defectrag_claim_direct_notifications(p_limit integer default 1,p_event uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare result jsonb;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 -- One globally serialized claim per 30 seconds, including concurrent workers.
 perform 1 from public.notification_dispatch_clock where singleton for update;
 if exists(select 1 from public.notification_dispatch_clock where next_claim_at>now()) then return '[]'::jsonb; end if;
 update public.staff_notification_outbox o set status='superseded',lease_token=null,lease_until=null
 where (p_event is null or o.id=p_event) and o.status in ('queued','sending','dead') and (not exists(select 1 from public.staff_access_requests r where r.user_id=o.subject_id and r.version=o.version)
 or (o.kind='requested' and not exists(select 1 from public.staff_members where user_id=o.recipient_id and role='developer' and revoked_at is null)));
 update public.staff_notification_outbox set status='dead',lease_token=null,lease_until=null
 where (p_event is null or id=p_event) and attempts>=8 and (status='queued' or status='sending' and lease_until<now());
 with selected as (select o.id from public.staff_notification_outbox o
  where (p_event is null or o.id=p_event) and o.attempts<8 and
  (o.status='queued' and o.next_attempt_at<=now() or o.status='sending' and o.lease_until<now())
  order by o.created_at limit 1 for update skip locked), claimed as (
   update public.staff_notification_outbox o set status='sending',attempts=attempts+1,
   lease_token=gen_random_uuid(),lease_until=now()+interval '5 minutes'
   from selected where o.id=selected.id returning o.*)
 select coalesce(jsonb_agg(jsonb_build_object('event_id',c.id,'lease_token',c.lease_token,'request_id',c.subject_id,
  'version',c.version,'kind',c.kind,'recipient_email',u.email,'display_name',r.display_name,'requested_at',r.created_at,
  'applicant_email',case when c.kind='requested' then a.email else null end)), '[]'::jsonb)
 into result from claimed c join public.staff_access_requests r on r.user_id=c.subject_id
 join auth.users u on u.id=c.recipient_id and u.email_confirmed_at is not null join auth.users a on a.id=c.subject_id;
 if jsonb_array_length(result)>0 then
  update public.notification_dispatch_clock set next_claim_at=now()+interval '30 seconds' where singleton;
 end if;
 return result;
end; $$;

create function public.defectrag_prepare_email(p_id uuid,p_lease uuid,p_payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare o public.staff_notification_outbox;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 select * into o from public.staff_notification_outbox where id=p_id for update;
 if not found or o.status<>'sending' or o.lease_token is distinct from p_lease or o.lease_until<=now() then return null; end if;
 -- Never automatically resend outside the provider's idempotency window,
 -- including manual dead-letter retry. A fresh event requires human resolution.
 if o.email_first_attempt_at is not null and o.email_first_attempt_at<now()-interval '23 hours' then
  update public.staff_notification_outbox set status='dead',last_error='email_ambiguity_manual_review',lease_token=null,lease_until=null where id=p_id;
  return null;
 end if;
 if not exists(select 1 from public.staff_access_requests where user_id=o.subject_id and version=o.version)
 or (o.kind='requested' and not exists(select 1 from public.staff_members where user_id=o.recipient_id and role='developer' and revoked_at is null)) then
  update public.staff_notification_outbox set status='superseded',lease_token=null,lease_until=null where id=p_id;
  return null;
 end if;
 if o.email_payload is not null and o.email_payload->'to' is distinct from
 (select jsonb_build_array(email) from auth.users where id=o.recipient_id and email_confirmed_at is not null) then
  update public.staff_notification_outbox set status='dead',last_error='email_recipient_changed_manual_review',lease_token=null,lease_until=null where id=p_id;
  return null;
 end if;
 if o.email_payload is null then
  if jsonb_typeof(p_payload) is distinct from 'object' or octet_length(p_payload::text)>8192
   or p_payload->'to' is distinct from (select jsonb_build_array(email) from auth.users where id=o.recipient_id and email_confirmed_at is not null)
   then raise exception 'Invalid email snapshot'; end if;
  update public.staff_notification_outbox set email_payload=p_payload,email_first_attempt_at=now() where id=p_id;
  o.email_payload:=p_payload;
 end if;
 return jsonb_build_object('payload',o.email_payload);
end; $$;
revoke all on function public.defectrag_claim_direct_notifications(integer,uuid),public.defectrag_prepare_email(uuid,uuid,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.defectrag_claim_direct_notifications(integer,uuid),public.defectrag_prepare_email(uuid,uuid,jsonb) to service_role;
commit;
