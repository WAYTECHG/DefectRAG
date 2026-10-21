-- ONE READ-ONLY SELECT for the new user-controlled pending QA account.
-- Does NOT claim/send/approve/reset/delete anything. No notification payload,
-- email output, account UUID, recipient UUID, lease token or secret is returned.
-- Database eligibility is not provider/Resend-recipient verification or send approval.
with target as (
 select id,email_confirmed_at is not null as email_confirmed
 from auth.users where lower(email)='wilbertandrewyonathan@gmail.com'
), events as (
 select o.id,o.status,o.attempts,r.status as request_status,
  coalesce(o.version=r.version,false) as current_version,
  coalesce(s.role='developer' and s.revoked_at is null
   and u.email_confirmed_at is not null,false) as active_verified_developer,
  coalesce(t.email_confirmed and r.status='pending' and o.version=r.version
   and o.status='queued' and o.attempts=0 and o.next_attempt_at<=now()
   and o.delivered_at is null and o.lease_token is null and o.lease_until is null
   and o.email_payload is null and o.email_first_attempt_at is null
   and s.role='developer' and s.revoked_at is null and u.email_confirmed_at is not null
   and not exists(select 1 from public.staff_members m where m.user_id=t.id),false)
   as database_eligible
 from target t join public.staff_access_requests r on r.user_id=t.id
 join public.staff_notification_outbox o on o.subject_id=r.user_id and o.kind='requested'
 left join public.staff_members s on s.user_id=o.recipient_id
 left join auth.users u on u.id=o.recipient_id
), grants as (
 select count(*)=2 and coalesce(bool_and(p.prosecdef
  and not has_function_privilege('anon',p.oid,'EXECUTE')
  and not has_function_privilege('authenticated',p.oid,'EXECUTE')
  and has_function_privilege('service_role',p.oid,'EXECUTE')),false) as worker_permissions_ok
 from pg_proc p where p.oid in (
  to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)'),
  to_regprocedure('public.defectrag_prepare_email(uuid,uuid,jsonb)'))
)
select (select count(*) from target) as matching_auth_accounts,
 coalesce((select bool_and(email_confirmed) from target),false) as email_confirmed,
 (select status from public.staff_access_requests where user_id in(select id from target) limit 1) as request_status,
 (select count(*) from public.staff_members where user_id in(select id from target)) as staff_memberships,
 g.worker_permissions_ok,
 (select count(*) from events where database_eligible) as eligible_event_count,
 case when (select count(*) from target)=1 and g.worker_permissions_ok
  and (select count(*) from events where database_eligible)=1
  then (select id from events where database_eligible limit 1) else null end as qa_event_id,
 coalesce((select jsonb_agg(jsonb_build_object(
  'event_id',id,'status',status,'attempts',attempts,'request_status',request_status,
  'current_version',current_version,'active_verified_developer',active_verified_developer,
  'database_eligible',database_eligible) order by id) from events),'[]'::jsonb) as event_checks
from grants g;
