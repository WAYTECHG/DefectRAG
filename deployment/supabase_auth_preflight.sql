-- READ-ONLY CATALOG REVIEW, NOT A MIGRATION. Prepared, NOT executed by Codex.
-- Run manually as the project SQL owner only when ready to review live drift.
-- No account rows, MFA seeds, keys, images or inspection data selected.
-- Review policy metadata privately: custom policy expressions can contain literals.
-- Resolve missing objects/collisions/unknown policies BEFORE running migration.
begin read only;

-- Read-only server metadata and migration operator context (no account rows).
select current_user as migration_operator,current_setting('server_version') as postgres_version;

-- 1. Required relations and existing RLS configuration.
with expected(schema_name,table_name) as (values
  ('public','staff_members'),('public','shared_inspections'),('public','staff_notes'),
  ('public','team_audit'),('public','personal_inspections'),('public','personal_notes'),
  ('public','personal_audit'),('public','defectrag_gallery_config'),
  ('public','defectrag_gallery_entries'),('public','defectrag_gallery_publishers'),
  ('storage','objects'),('storage','buckets'),('auth','users'),('auth','mfa_factors'))
select e.*,c.oid is not null as present,c.relrowsecurity as rls_enabled,
  c.relforcerowsecurity as force_rls,pg_get_userbyid(c.relowner) as owner
from expected e left join pg_class c on c.oid=to_regclass(format('%I.%I',e.schema_name,e.table_name))
order by schema_name,table_name;

-- 2. Required column shapes. Null expected_type means inspect native enum type.
with expected(schema_name,table_name,column_name,expected_type) as (values
  ('public','staff_members','user_id','uuid'),('public','staff_members','display_name','text'),
  ('public','staff_members','role','text'),('public','shared_inspections','id','text'),
  ('public','shared_inspections','owner_id','uuid'),('public','shared_inspections','payload','jsonb'),
  ('public','shared_inspections','conversation','jsonb'),('public','shared_inspections','image_path','text'),
  ('public','shared_inspections','heatmap_path','text'),('public','shared_inspections','archived_at','timestamp with time zone'),
  ('public','personal_inspections','id','text'),('public','personal_inspections','owner_id','uuid'),
  ('public','personal_inspections','payload','jsonb'),('public','personal_inspections','conversation','jsonb'),
  ('public','personal_inspections','image_path','text'),('public','personal_inspections','heatmap_path','text'),
  ('public','personal_inspections','archived_at','timestamp with time zone'),
  ('public','staff_notes','author_id','uuid'),('public','staff_notes','inspection_id','text'),
  ('public','personal_notes','author_id','uuid'),('public','personal_notes','inspection_id','text'),
  ('public','personal_audit','owner_id','uuid'),('public','personal_audit','actor_id','uuid'),
  ('auth','users','id','uuid'),('auth','users','email','text'),
  ('auth','users','email_confirmed_at','timestamp with time zone'),
  ('auth','mfa_factors','user_id','uuid'),('auth','mfa_factors','factor_type',null),
  ('auth','mfa_factors','status',null))
select e.*,a.attname is not null as present,format_type(a.atttypid,a.atttypmod) as actual_type,
  case when a.attname is null then false when e.expected_type is null then null
    else format_type(a.atttypid,a.atttypmod)=e.expected_type end as type_matches
from expected e left join pg_attribute a
  on a.attrelid=to_regclass(format('%I.%I',e.schema_name,e.table_name))
    and a.attname=e.column_name and a.attnum>0 and not a.attisdropped
order by schema_name,table_name,column_name;

-- Full private-table shape, including required fields beyond the core checks.
select table_schema,table_name,ordinal_position,column_name,udt_schema,udt_name,is_nullable
from information_schema.columns where table_schema='public' and table_name in (
  'staff_members','shared_inspections','staff_notes','team_audit',
  'personal_inspections','personal_notes','personal_audit')
order by table_name,ordinal_position;

-- Native enum support needed by the MFA helper (no enrolled-factor data).
select t.typname,e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid
  join pg_namespace n on n.oid=t.typnamespace
where n.nspname='auth' and t.typname in ('factor_type','factor_status')
order by t.typname,e.enumsortorder;

-- 3. Exact existing RPC signatures, owners, definer/invoker and grants.
with expected(signature) as (values
  ('public.defectrag_is_staff()'),('public.defectrag_is_developer()'),
  ('public.archive_team_inspections(text[])'),('public.restore_team_inspections(text[])'),
  ('public.defectrag_append_conversation(text,text,jsonb)'),('public.defectrag_acknowledge_review(text)'),
  ('public.defectrag_personal_action(text,text,text,jsonb)'),('public.defectrag_personal_archive(text[],boolean)'),
  ('public.defectrag_share_personal(text,text,text,boolean)'),('public.defectrag_workspace_stats(text)'),
  ('public.defectrag_gallery_read(uuid,integer)'),
  ('public.defectrag_gallery_write(text,text,text,text,jsonb,text,text,uuid,boolean)'),
  ('auth.uid()'),('auth.jwt()'),('auth.role()'))
select e.signature,p.oid is not null as present,p.prosecdef as security_definer,
  pg_get_userbyid(p.proowner) as owner,p.proconfig,p.proacl
from expected e left join pg_proc p on p.oid=to_regprocedure(e.signature)
order by e.signature;

-- Expand function ACLs, including implicit PUBLIC EXECUTE when proacl is NULL.
-- A null ACL does NOT mean no execution privilege. Review unexpected roles and
-- overloaded RPCs in addition to the exact-signature presence checks above.
select n.nspname as schema_name,p.proname,pg_get_function_identity_arguments(p.oid) as arguments,
  case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end as grantee,
  a.privilege_type,p.prosecdef as security_definer,p.proconfig,
  pg_get_userbyid(p.proowner) as function_owner
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
where n.nspname='public' and (p.proname like 'defectrag\_%' escape '\'
  or p.proname in ('archive_team_inspections','restore_team_inspections'))
order by schema_name,p.proname,arguments,grantee;

-- Inspect every applicable policy; unexpected permissive/anon policies need review.
select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
from pg_policies where (schemaname='public' and tablename in (
  'staff_members','shared_inspections','staff_notes','team_audit',
  'personal_inspections','personal_notes','personal_audit',
  'defectrag_gallery_config','defectrag_gallery_entries','defectrag_gallery_publishers'))
  or (schemaname='storage' and tablename='objects')
order by schemaname,tablename,policyname;

select table_schema,table_name,grantee,privilege_type
from information_schema.table_privileges where table_schema in ('public','storage')
  and table_name in ('staff_members','shared_inspections','staff_notes','team_audit',
    'personal_inspections','personal_notes','personal_audit','objects',
    'defectrag_gallery_config','defectrag_gallery_entries','defectrag_gallery_publishers')
  and grantee in ('PUBLIC','anon','authenticated','service_role')
order by table_schema,table_name,grantee,privilege_type;

-- Private buckets must exist and have public=false. No object rows selected.
select id,public,file_size_limit,allowed_mime_types from storage.buckets
where id in ('team-inspections','personal-inspections') order by id;

-- 4. These are expected ABSENT before the first auth migration. Presence means
-- STOP and reconcile the exact installed version; do not blindly rerun old SQL.
select c.relname as existing_auth_object from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind in ('r','p') and c.relname in (
  'defectrag_auth_settings','staff_access_requests','staff_access_audit','staff_notification_outbox');
select attname as existing_auth_column from pg_attribute
where attrelid=to_regclass('public.staff_members') and attname in ('revoked_at','revoked_by') and not attisdropped;
select tablename,policyname from pg_policies where policyname in ('staff_auth_guard','private_artifact_auth_guard');
select p.proname,pg_get_function_identity_arguments(p.oid) as arguments
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname in ('defectrag_has_aal2','defectrag_can_manage_access',
  'defectrag_auth_status','defectrag_request_access','defectrag_access_directory','defectrag_decide_access',
  'defectrag_configure_auth','defectrag_claim_notifications','defectrag_finish_notification',
  'defectrag_retry_notification','defectrag_notification_status');

-- Role availability; no credentials or role password fields.
select rolname from pg_roles where rolname in ('anon','authenticated','service_role');
rollback;
