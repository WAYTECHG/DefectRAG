-- ONE SELECT ONLY, before/after the separately approved clock correction.
-- Does not invoke the claim function, prepare mail, change flags or send.
with fn as (
 select * from pg_proc where oid=to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)')
)
select
 position($old$update public.notification_dispatch_clock set next_claim_at=now()+interval '30 seconds';$old$ in p.prosrc)>0 as unsafe_clock_statement_present,
 position($fixed$update public.notification_dispatch_clock set next_claim_at=now()+interval '30 seconds' where singleton;$fixed$ in p.prosrc)>0 as scoped_clock_statement_present,
 p.prosecdef as security_definer,
 pg_get_userbyid(p.proowner) as function_owner,
 has_function_privilege('anon',p.oid,'EXECUTE') as anonymous_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') as signed_in_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') as worker_execute,
 (select registration_enabled and mfa_required from public.defectrag_auth_settings where singleton) as registration_and_mfa_enabled,
 (select jsonb_build_object('status',o.status,'attempts',o.attempts,'request_status',r.status,
  'has_membership',exists(select 1 from public.staff_members m where m.user_id=o.subject_id))
  from public.staff_notification_outbox o join public.staff_access_requests r on r.user_id=o.subject_id
  where o.id='3d25e7b3-04c4-43c8-a49e-e473be3bcbdc'::uuid) as qa_event
from fn p;
