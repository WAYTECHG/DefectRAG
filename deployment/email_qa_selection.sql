-- ONE READ-ONLY SELECT. Always returns one diagnostic row, even with no events.
-- Does not claim/reset/send/approve anything or invoke notification worker RPCs.
-- No emails, names, payloads, credentials, user IDs or lease tokens are returned.
-- Event IDs are diagnostic identifiers, NOT approval to send to an applicant.
with rpc_permissions as (
 select count(*)=2 and coalesce(bool_and(p.prosecdef
  and not has_function_privilege('anon',p.oid,'EXECUTE')
  and not has_function_privilege('authenticated',p.oid,'EXECUTE')
  and has_function_privilege('service_role',p.oid,'EXECUTE')),false)
  as worker_permissions_ok
 from pg_proc p where p.oid in (
   to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)'),
  to_regprocedure('public.defectrag_prepare_email(uuid,uuid,jsonb)'))
), events as (
 select o.id,o.kind,o.status,o.attempts,o.created_at,
  r.status as request_status,
  coalesce(r.version=o.version,false) as current_version,
  coalesce(r.display_name='QA Registration',false) as exact_qa_name,
  coalesce(lower(btrim(r.display_name))='qa registration',false) as normalized_qa_name,
  coalesce(s.role='developer' and s.revoked_at is null
   and u.email_confirmed_at is not null,false) as active_verified_developer,
  coalesce(o.next_attempt_at<=now(),false) as retry_due
 from public.staff_notification_outbox o
 left join public.staff_access_requests r on r.user_id=o.subject_id
 left join public.staff_members s on s.user_id=o.recipient_id
 left join auth.users u on u.id=o.recipient_id
), recent as (
 select * from events where kind='requested' order by created_at desc,id limit 20
)
select p.worker_permissions_ok,
 (select count(*) from public.staff_access_requests where status='pending') as pending_requests,
 (select count(*) from public.staff_access_requests
  where lower(btrim(display_name))='qa registration') as known_qa_requests,
 (select count(*) from public.staff_members s join auth.users u on u.id=s.user_id
  where s.role='developer' and s.revoked_at is null
   and u.email_confirmed_at is not null) as active_verified_developers,
 (select count(*) from events) as total_outbox_events,
 (select count(*) from events where kind='requested') as requested_events,
 (select count(*) from events where kind='requested' and request_status='pending'
  and current_version and status='queued' and attempts<8
  and active_verified_developer and exact_qa_name) as original_query_matches,
 (select count(*) from events where kind='requested' and request_status='pending'
  and current_version and status='queued' and attempts<8
  and active_verified_developer and retry_due) as ready_pending_events_any_name,
 coalesce((select jsonb_agg(jsonb_build_object(
  'event_id',id,'delivery_status',status,'attempts',attempts,
  'request_status',request_status,'current_version',current_version,
  'exact_qa_name',exact_qa_name,'normalized_qa_name',normalized_qa_name,
  'active_verified_developer',active_verified_developer,'retry_due',retry_due
 ) order by created_at desc,id) from recent),'[]'::jsonb) as recent_requested_events
from rpc_permissions p;
