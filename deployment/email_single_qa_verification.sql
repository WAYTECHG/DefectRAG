-- ONE READ-ONLY SELECT. Run BEFORE the one authorized send and AFTER delivery0.
-- Save both metadata rows for comparison. Never invokes worker/provider/RPCs.
-- No email addresses, private payloads, credentials or lease tokens are output.
with event as (
 select o.*,r.status as request_status,r.version as current_request_version,
  u.email_confirmed_at is not null as applicant_confirmed,
  lower(u.email)='wilbertandrewyonathan@gmail.com' as exact_qa_account,
  exists(select 1 from public.staff_members m where m.user_id=o.subject_id) as has_membership,
  exists(select 1 from public.staff_members m join auth.users d on d.id=m.user_id
   where m.user_id=o.recipient_id and m.role='developer' and m.revoked_at is null
    and d.email_confirmed_at is not null) as active_verified_developer
 from public.staff_notification_outbox o
 join public.staff_access_requests r on r.user_id=o.subject_id
 join auth.users u on u.id=o.subject_id
 where o.id='3d25e7b3-04c4-43c8-a49e-e473be3bcbdc'::uuid
)
select (select count(*) from event) as matching_events,
 coalesce((select bool_and(exact_qa_account and applicant_confirmed
  and request_status='pending' and not has_membership) from event),false) as applicant_still_pending_without_staff,
 coalesce((select bool_and(kind='requested' and version=current_request_version
  and active_verified_developer) from event),false) as current_developer_request_event,
 coalesce((select jsonb_agg(jsonb_build_object(
  'event_id',id,'status',status,'attempts',attempts,'request_status',request_status,
  'delivered_at',delivered_at,'last_error',last_error,
  'email_snapshot_present',email_payload is not null,
  'snapshot_fingerprint',md5(email_payload::text),
  'first_attempt_at',email_first_attempt_at,
  'claimable_now',attempts<8 and (status='queued' and next_attempt_at<=now()
   or status='sending' and lease_until<now()),
  'provider_idempotency_key','defectrag/'||id::text
 )) from event),'[]'::jsonb) as event_checks,
 (select count(*) from public.staff_notification_outbox
  where id<>'3d25e7b3-04c4-43c8-a49e-e473be3bcbdc'::uuid) as unrelated_event_count,
 (select md5(coalesce(jsonb_agg(jsonb_build_array(id,status,attempts,next_attempt_at,
   lease_until,delivered_at,last_error,version,kind) order by id)::text,'[]'))
  from public.staff_notification_outbox
  where id<>'3d25e7b3-04c4-43c8-a49e-e473be3bcbdc'::uuid) as unrelated_metadata_fingerprint;
-- sent means provider ACCEPTED + outbox acknowledgment, not inbox delivery.
-- Fingerprints compare metadata only. They do not prove a provider replay test.
