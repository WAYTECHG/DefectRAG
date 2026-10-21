-- READ ONLY: run once in the existing project's Supabase SQL Editor.
-- Exact QA target only. No deletion, permission change, RPC call or email send.
-- Counts and constraint metadata only; no email, UUID or private payload output.
-- This is NOT deletion approval or proof that all dependencies can be erased.
with target as (
 select id from auth.users where lower(email)='saputangan1404@gmail.com'
), dependencies as (
 select ns.nspname as schema_name,c.relname as table_name,k.conname as constraint_name,
  pg_get_constraintdef(k.oid) as definition
 from pg_constraint k
 join pg_class c on c.oid=k.conrelid
 join pg_namespace ns on ns.oid=c.relnamespace
 where k.contype='f' and ns.nspname not in ('auth','pg_catalog','information_schema')
 and k.confrelid in ('auth.users'::regclass,'public.staff_members'::regclass,
  'public.staff_access_requests'::regclass,'public.personal_inspections'::regclass,
  'public.shared_inspections'::regclass,'public.staff_notes'::regclass)
)
select
 (select count(*) from target) as matching_auth_accounts,
 (select coalesce(jsonb_agg(s.role),'[]'::jsonb) from public.staff_members s
  where s.user_id in (select id from target)) as target_roles,
 jsonb_build_object(
  'staff_members',(select count(*) from public.staff_members where user_id in (select id from target)),
  'access_requests',(select count(*) from public.staff_access_requests where user_id in (select id from target)),
  'access_audit',(select count(*) from public.staff_access_audit where subject_id in (select id from target) or actor_id in (select id from target)),
  'notification_events',(select count(*) from public.staff_notification_outbox where subject_id in (select id from target) or recipient_id in (select id from target)),
  'active_notification_leases',(select count(*) from public.staff_notification_outbox where (subject_id in (select id from target) or recipient_id in (select id from target)) and status='sending'),
  'personal_inspections',(select count(*) from public.personal_inspections where owner_id in (select id from target)),
  'team_inspections',(select count(*) from public.shared_inspections where owner_id in (select id from target)),
  'personal_notes',(select count(*) from public.personal_notes where author_id in (select id from target)),
  'team_notes',(select count(*) from public.staff_notes where author_id in (select id from target)),
  'personal_audit',(select count(*) from public.personal_audit where owner_id in (select id from target) or actor_id in (select id from target)),
  'team_audit',(select count(*) from public.team_audit where actor_id in (select id from target)),
  'decisions_on_other_accounts',(select count(*) from public.staff_access_requests where decided_by in (select id from target) and user_id not in (select id from target)),
  'revocations_of_other_accounts',(select count(*) from public.staff_members where revoked_by in (select id from target) and user_id not in (select id from target)),
  'personal_archiver_references',(select count(*) from public.personal_inspections where archived_by in (select id from target)),
  'team_archiver_references',(select count(*) from public.shared_inspections where archived_by in (select id from target)),
  'storage_path_matches',(select count(*) from storage.objects o where exists(select 1 from target t where split_part(o.name,'/',1)=t.id::text))
 ) as linked_record_counts,
 coalesce((select jsonb_agg(to_jsonb(d) order by schema_name,table_name,constraint_name)
  from dependencies d),'[]'::jsonb) as dependency_constraints;
-- Storage paths cover the application's UUID-prefixed artifacts, not every
-- possible owner record. Review storage ownership, indirect/optional tables,
-- triggers and retention requirements before drafting any destructive cleanup.
