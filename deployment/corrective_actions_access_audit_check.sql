-- SELECT ONLY. Reconcile membership-count drift since the installation baseline.
-- Returns action metadata/booleans only; no email, account IDs or payloads.
with qa_actors as (
 select distinct actor_id from public.corrective_action_history
 where case_id='7ce36833-4300-4c7f-a3df-b9b8356a0d1d'::uuid
)
select jsonb_build_object(
 'since','2026-10-24T08:07:40.58763+00:00',
 'changes',coalesce((select jsonb_agg(jsonb_build_object(
   'action',a.action,'version',a.version,'at',a.created_at,
   'actor_is_active_developer',exists(select 1 from public.staff_members s
     where s.user_id=a.actor_id and s.role='developer' and s.revoked_at is null),
   'subject_is_qa_actor',exists(select 1 from qa_actors q where q.actor_id=a.subject_id),
   'subject_current_status',(select r.status from public.staff_access_requests r where r.user_id=a.subject_id)
 ) order by a.created_at) from public.staff_access_audit a
 where a.created_at>='2026-10-24T08:07:40.58763+00:00'::timestamptz),'[]'::jsonb)
) as access_audit_check;
