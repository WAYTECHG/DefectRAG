-- READ ONLY. Private backup of the SIX QA metadata rows before approved cleanup.
-- Export this ONE JSON result privately (not chat/GitHub/project/runtime folders).
-- May contain personal data and email bodies. It is not an Auth credentials backup.
-- Deleting the Auth account later cannot be undone with this metadata export.
with target as (
 select id from auth.users where lower(email)='saputangan1404@gmail.com'
)
select jsonb_build_object(
 'exported_at',now(),
 'staff_members',(select coalesce(jsonb_agg(to_jsonb(s)),'[]'::jsonb)
  from public.staff_members s where user_id in(select id from target)),
 'staff_access_requests',(select coalesce(jsonb_agg(to_jsonb(r)),'[]'::jsonb)
  from public.staff_access_requests r where user_id in(select id from target)),
 'staff_access_audit',(select coalesce(jsonb_agg(to_jsonb(a)),'[]'::jsonb)
  from public.staff_access_audit a where subject_id in(select id from target)),
 'staff_notification_outbox',(select coalesce(jsonb_agg(to_jsonb(o)),'[]'::jsonb)
  from public.staff_notification_outbox o where subject_id in(select id from target))
) as private_qa_metadata_backup;
