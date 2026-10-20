-- ONE SELECT ONLY: identify controlled QA event + inspect new worker RPC grants.
-- Does NOT claim/reset/send/approve anything. No email address or payload output.
select o.id as qa_event_id,o.status as delivery_status,o.attempts,
 r.status as request_status,
 (select count(*)=2 and coalesce(bool_and(p.prosecdef
  and not has_function_privilege('anon',p.oid,'EXECUTE')
  and not has_function_privilege('authenticated',p.oid,'EXECUTE')
  and has_function_privilege('service_role',p.oid,'EXECUTE')),false)
  from pg_proc p where p.oid in (
   to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)'),
   to_regprocedure('public.defectrag_prepare_email(uuid,uuid,jsonb)'))
 ) as worker_permissions_ok
from public.staff_notification_outbox o
join public.staff_access_requests r on r.user_id=o.subject_id and r.version=o.version
join public.staff_members s on s.user_id=o.recipient_id
join auth.users u on u.id=s.user_id
where r.display_name='QA Registration' and r.status='pending'
and o.kind='requested' and o.status='queued' and o.attempts<8
and s.role='developer' and s.revoked_at is null and u.email_confirmed_at is not null
order by o.created_at;
