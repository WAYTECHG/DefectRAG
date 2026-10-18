-- DefectRAG: one organisation's allowlisted staff, private artifacts and recoverable history.
-- Run once in your own Supabase SQL Editor. No service-role key belongs in the frontend.
begin;
create table if not exists public.staff_members (
  user_id uuid primary key references auth.users(id),
  display_name text not null,
  role text not null default 'staff' check (role in ('staff','developer'))
);
alter table public.staff_members enable row level security;
create or replace function public.defectrag_is_staff() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.staff_members where user_id=auth.uid());
$$;
create or replace function public.defectrag_is_developer() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.staff_members where user_id=auth.uid() and role='developer');
$$;
revoke all on function public.defectrag_is_staff(),public.defectrag_is_developer() from public;
grant execute on function public.defectrag_is_staff(),public.defectrag_is_developer() to authenticated;
drop policy if exists staff_directory on public.staff_members;
create policy staff_directory on public.staff_members for select to authenticated using(public.defectrag_is_staff());
revoke all on public.staff_members from anon,authenticated;
grant select on public.staff_members to authenticated;

create table if not exists public.shared_inspections (
  id text primary key check(id ~ '^[0-9a-f]{32}$'),
  owner_id uuid not null default auth.uid() references auth.users(id),
  created_at timestamptz not null default now(),
  payload jsonb not null check(jsonb_typeof(payload)='object'),
  conversation jsonb not null default '[]'::jsonb check(jsonb_typeof(conversation)='array'),
  image_path text not null,
  heatmap_path text not null,
  archived_at timestamptz,
  archived_by uuid references auth.users(id)
);
alter table public.shared_inspections enable row level security;
revoke all on public.shared_inspections from anon,authenticated;
grant select,insert on public.shared_inspections to authenticated;
drop policy if exists staff_read on public.shared_inspections;
create policy staff_read on public.shared_inspections for select to authenticated
  using(public.defectrag_is_staff() and (archived_at is null or public.defectrag_is_developer()));
drop policy if exists staff_insert on public.shared_inspections;
create policy staff_insert on public.shared_inspections for insert to authenticated with check(
  public.defectrag_is_staff() and owner_id=auth.uid() and archived_at is null and archived_by is null
  and image_path like auth.uid()::text||'/'||id||'/%'
  and heatmap_path like auth.uid()::text||'/'||id||'/%'
  and payload->>'id'=id);
create index if not exists shared_inspections_recent on public.shared_inspections(created_at desc);

create table if not exists public.staff_notes (
  id uuid primary key default gen_random_uuid(),
  inspection_id text not null references public.shared_inspections(id),
  author_id uuid not null default auth.uid() references auth.users(id),
  body text not null check(char_length(body) between 1 and 2000),
  created_at timestamptz not null default now()
);
alter table public.staff_notes enable row level security;
revoke all on public.staff_notes from anon,authenticated;
grant select,insert on public.staff_notes to authenticated;
drop policy if exists staff_notes_read on public.staff_notes;
create policy staff_notes_read on public.staff_notes for select to authenticated using(
  public.defectrag_is_staff() and exists(select 1 from public.shared_inspections i where i.id=inspection_id));
drop policy if exists staff_notes_insert on public.staff_notes;
create policy staff_notes_insert on public.staff_notes for insert to authenticated with check(
  public.defectrag_is_staff() and author_id=auth.uid() and exists(
    select 1 from public.shared_inspections i where i.id=inspection_id and i.archived_at is null));

create table if not exists public.team_audit (
  id uuid primary key default gen_random_uuid(),actor_id uuid references auth.users(id),
  action text not null,inspection_ids text[] not null,created_at timestamptz not null default now()
);
alter table public.team_audit enable row level security;
revoke all on public.team_audit from anon,authenticated;
grant select on public.team_audit to authenticated;
drop policy if exists developer_audit on public.team_audit;
create policy developer_audit on public.team_audit for select to authenticated using(public.defectrag_is_developer());

create or replace function public.archive_team_inspections(p_ids text[]) returns integer
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_is_staff() or coalesce(cardinality(p_ids),0) not between 1 and 500 then
    raise exception 'Approved staff and 1-500 inspection IDs required'; end if;
  if exists(select 1 from public.shared_inspections where id=any(p_ids) and owner_id<>auth.uid())
     and not public.defectrag_is_developer() then raise exception 'Only your own records can be archived'; end if;
  update public.shared_inspections set archived_at=now(),archived_by=auth.uid()
    where id=any(p_ids) and archived_at is null;
  get diagnostics changed=row_count;
  insert into public.team_audit(actor_id,action,inspection_ids) values(auth.uid(),'archive',p_ids);
  return changed;
end; $$;
create or replace function public.restore_team_inspections(p_ids text[]) returns integer
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_is_developer() or coalesce(cardinality(p_ids),0) not between 1 and 500 then
    raise exception 'Developer role and 1-500 inspection IDs required'; end if;
  update public.shared_inspections set archived_at=null,archived_by=null where id=any(p_ids) and archived_at is not null;
  get diagnostics changed=row_count;
  insert into public.team_audit(actor_id,action,inspection_ids) values(auth.uid(),'restore',p_ids);
  return changed;
end; $$;
revoke all on function public.archive_team_inspections(text[]),public.restore_team_inspections(text[]) from public;
grant execute on function public.archive_team_inspections(text[]),public.restore_team_inspections(text[]) to authenticated;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('team-inspections','team-inspections',false,10485760,array['image/jpeg','image/png','image/webp'])
on conflict(id) do nothing;
drop policy if exists team_artifacts_read on storage.objects;
create policy team_artifacts_read on storage.objects for select to authenticated using(
  bucket_id='team-inspections' and public.defectrag_is_staff());
drop policy if exists team_artifacts_insert on storage.objects;
create policy team_artifacts_insert on storage.objects for insert to authenticated with check(
  bucket_id='team-inspections' and public.defectrag_is_staff() and (storage.foldername(name))[1]=auth.uid()::text);
-- No client DELETE or UPDATE policies: archival never removes original artifacts.
commit;

-- After creating/inviting users in Authentication > Users, add them here in SQL Editor:
-- insert into public.staff_members(user_id,display_name,role)
-- values('USER_UUID_FROM_AUTH','Your name','developer');
-- Other colleagues use role 'staff'. Do not expose signup as staff auto-enrolment.
