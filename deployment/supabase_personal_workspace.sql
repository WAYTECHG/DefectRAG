-- REVIEW REQUIRED. Execute manually ONCE as project owner, inside SQL Editor.
-- Adds private personal storage. Does NOT move, delete or privatize legacy team
-- records. Does NOT change gallery tables/functions or enroll new staff.
begin;
create table public.personal_inspections (
  id text primary key check(id ~ '^[a-f0-9]{32}$'),
  owner_id uuid not null default auth.uid() references auth.users(id),
  created_at timestamptz not null default now(),
  payload jsonb not null check(jsonb_typeof(payload)='object'),
  conversation jsonb not null default '[]'::jsonb check(jsonb_typeof(conversation)='array'),
  image_path text not null, heatmap_path text not null,
  archived_at timestamptz, archived_by uuid references auth.users(id)
);
create index personal_recent on public.personal_inspections(owner_id,created_at desc);
alter table public.personal_inspections enable row level security;
revoke all on public.personal_inspections from public,anon,authenticated;
grant select,insert on public.personal_inspections to authenticated;
create policy personal_owner_read on public.personal_inspections for select to authenticated
  using(public.defectrag_is_staff() and owner_id=auth.uid());
create policy personal_owner_insert on public.personal_inspections for insert to authenticated with check(
  public.defectrag_is_staff() and owner_id=auth.uid() and archived_at is null and archived_by is null
  and payload->>'id'=id and image_path like auth.uid()::text||'/'||id||'/%'
  and heatmap_path like auth.uid()::text||'/'||id||'/%');

create table public.personal_notes (
  id uuid primary key default gen_random_uuid(),
  inspection_id text not null references public.personal_inspections(id),
  author_id uuid not null default auth.uid() references auth.users(id),
  body text not null check(char_length(body) between 1 and 2000),
  created_at timestamptz not null default now()
);
alter table public.personal_notes enable row level security;
revoke all on public.personal_notes from public,anon,authenticated;
grant select,insert on public.personal_notes to authenticated;
create policy personal_notes_owner_read on public.personal_notes for select to authenticated using(
  public.defectrag_is_staff() and author_id=auth.uid() and exists(
    select 1 from public.personal_inspections i where i.id=inspection_id and i.owner_id=auth.uid()));
create policy personal_notes_owner_insert on public.personal_notes for insert to authenticated with check(
  public.defectrag_is_staff() and author_id=auth.uid() and exists(
    select 1 from public.personal_inspections i where i.id=inspection_id and i.owner_id=auth.uid() and i.archived_at is null));

create table public.personal_audit (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id),
  inspection_id text not null references public.personal_inspections(id),
  actor_id uuid not null references auth.users(id), action text not null,
  created_at timestamptz not null default now()
);
alter table public.personal_audit enable row level security;
revoke all on public.personal_audit from public,anon,authenticated;
grant select on public.personal_audit to authenticated;
create policy personal_audit_owner_read on public.personal_audit for select to authenticated
  using(public.defectrag_is_staff() and owner_id=auth.uid());

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('personal-inspections','personal-inspections',false,10485760,array['image/jpeg'])
on conflict(id) do nothing;
create policy personal_artifact_read on storage.objects for select to authenticated using(
  bucket_id='personal-inspections' and public.defectrag_is_staff()
  and (storage.foldername(name))[1]=auth.uid()::text);
create policy personal_artifact_insert on storage.objects for insert to authenticated with check(
  bucket_id='personal-inspections' and public.defectrag_is_staff()
  and (storage.foldername(name))[1]=auth.uid()::text);
-- No UPDATE or DELETE grants/policies. Immutable content-addressed images.

create or replace function public.defectrag_personal_action(
  p_id text,p_action text,p_question text default '',p_answer jsonb default '{}'::jsonb)
returns integer language plpgsql security definer set search_path='' as $$
declare r public.personal_inspections;
begin
  if not public.defectrag_is_staff() then raise insufficient_privilege using message='Approved staff required'; end if;
  select * into r from public.personal_inspections where id=p_id and owner_id=auth.uid() and archived_at is null for update;
  if r.id is null then raise insufficient_privilege using message='Active personal inspection unavailable'; end if;
  if p_action='conversation' then
    if p_question is null or char_length(p_question) not between 3 and 1200 or
       p_answer is null or jsonb_typeof(p_answer)<>'object' or octet_length(p_answer::text)>40000 then
      raise exception 'Invalid bounded conversation'; end if;
    update public.personal_inspections set conversation=conversation||jsonb_build_array(
      jsonb_build_object('role','user','question',p_question,'created_at',now(),'actor_id',auth.uid()),
      p_answer||jsonb_build_object('role','assistant','created_at',now(),'actor_id',auth.uid())) where id=p_id;
  elsif p_action='acknowledge' then
    if coalesce((r.payload->>'alert_acknowledged')::boolean,false) then return 1; end if;
    update public.personal_inspections set payload=payload||jsonb_build_object(
      'alert_acknowledged',true,'alert_acknowledged_by',auth.uid(),'alert_acknowledged_at',now()) where id=p_id;
  else raise exception 'Invalid personal action'; end if;
  insert into public.personal_audit(owner_id,inspection_id,actor_id,action) values(auth.uid(),p_id,auth.uid(),p_action);
  return 1;
end; $$;

create or replace function public.defectrag_personal_archive(p_ids text[],p_restore boolean default false)
returns integer language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_is_staff() or coalesce(cardinality(p_ids),0) not between 1 and 500 then
    raise insufficient_privilege using message='Approved owner and 1-500 IDs required'; end if;
  -- No developer exception: application developers cannot read another user's
  -- personal records. Owners can recover their own records; team recovery stays
  -- developer-only through the pre-existing team RPC.
  with updated as (
    update public.personal_inspections set archived_at=case when p_restore then null else now() end,
      archived_by=case when p_restore then null else auth.uid() end
    where id=any(p_ids) and owner_id=auth.uid() and ((p_restore and archived_at is not null) or (not p_restore and archived_at is null))
    returning id
  ) insert into public.personal_audit(owner_id,inspection_id,actor_id,action)
    select auth.uid(),id,auth.uid(),case when p_restore then 'restore' else 'archive' end from updated;
  get diagnostics changed=row_count;
  return changed;
end; $$;

create or replace function public.defectrag_share_personal(
  p_id text,p_image_path text,p_heatmap_path text,p_include_conversation boolean default false)
returns boolean language plpgsql security definer set search_path='' as $$
declare r public.personal_inspections; other_owner uuid;
begin
  if not public.defectrag_is_staff() then raise insufficient_privilege using message='Approved staff required'; end if;
  select * into r from public.personal_inspections where id=p_id and owner_id=auth.uid() and archived_at is null for update;
  if r.id is null then raise insufficient_privilege using message='Active personal inspection unavailable'; end if;
  select owner_id into other_owner from public.shared_inspections where id=p_id;
  if other_owner is not null then
    if other_owner<>auth.uid() then raise insufficient_privilege using message='Inspection ID conflict'; end if;
    return false; -- Do not overwrite a colleague's subsequent team conversation.
  end if;
  if p_image_path is null or p_heatmap_path is null or
     p_image_path not like auth.uid()::text||'/'||p_id||'/%' or
     p_heatmap_path not like auth.uid()::text||'/'||p_id||'/%' or
     not exists(select 1 from storage.objects where bucket_id='team-inspections' and name=p_image_path) or
     not exists(select 1 from storage.objects where bucket_id='team-inspections' and name=p_heatmap_path) then
    raise exception 'Uploaded team artifacts required'; end if;
  insert into public.shared_inspections(id,owner_id,created_at,payload,conversation,image_path,heatmap_path)
    values(r.id,auth.uid(),r.created_at,r.payload-'alert_acknowledged'-'alert_acknowledged_by'-'alert_acknowledged_at',
      case when p_include_conversation then r.conversation else '[]'::jsonb end,p_image_path,p_heatmap_path);
  insert into public.personal_audit(owner_id,inspection_id,actor_id,action) values(auth.uid(),p_id,auth.uid(),'share_with_team');
  return true;
end; $$;

create or replace function public.defectrag_workspace_stats(p_scope text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare result jsonb;
begin
  if not public.defectrag_is_staff() or p_scope not in ('personal','team') or p_scope is null then
    raise insufficient_privilege using message='Approved staff and valid workspace required'; end if;
  with source as (
    select payload,archived_at from public.personal_inspections where p_scope='personal' and owner_id=auth.uid()
    union all
    select payload,archived_at from public.shared_inspections where p_scope='team'
  ), active as (select payload from source where archived_at is null),
  batches as (select coalesce(payload->>'batch','') as batch,count(*) total,
    count(*) filter(where payload->>'verdict'='Anomalous') anomalous,
    count(*) filter(where payload->>'verdict'='Uncertain') uncertain from active group by coalesce(payload->>'batch',''))
  select jsonb_build_object('total',(select count(*) from active),'counts',jsonb_build_object(
    'Good',(select count(*) from active where payload->>'verdict'='Good'),
    'Anomalous',(select count(*) from active where payload->>'verdict'='Anomalous'),
    'Uncertain',(select count(*) from active where payload->>'verdict'='Uncertain')),
    'batches',coalesce((select jsonb_agg(to_jsonb(batches)) from batches),'[]'::jsonb),
    'archived_total',(select count(*) from source where archived_at is not null),'failed_requests',null,'workspace',p_scope)
    into result;
  return result;
end; $$;

-- Audit future inserts, including direct RLS-authorized browser writes. No
-- historical actor/time is invented and no legacy record is changed.
create or replace function public.defectrag_workspace_insert_audit()
returns trigger language plpgsql security definer set search_path='' as $$
begin
  if tg_table_name='personal_inspections' then
    insert into public.personal_audit(owner_id,inspection_id,actor_id,action) values(new.owner_id,new.id,auth.uid(),'create');
  elsif tg_table_name='personal_notes' then
    insert into public.personal_audit(owner_id,inspection_id,actor_id,action) values(new.author_id,new.inspection_id,auth.uid(),'review_note');
  elsif tg_table_name='shared_inspections' then
    insert into public.team_audit(actor_id,action,inspection_ids) values(auth.uid(),'share',array[new.id]);
  elsif tg_table_name='staff_notes' then
    insert into public.team_audit(actor_id,action,inspection_ids) values(auth.uid(),'review_note',array[new.inspection_id]);
  end if;
  return new;
end; $$;
create trigger personal_creation_audit after insert on public.personal_inspections for each row execute function public.defectrag_workspace_insert_audit();
create trigger personal_review_audit after insert on public.personal_notes for each row execute function public.defectrag_workspace_insert_audit();
create trigger team_sharing_audit after insert on public.shared_inspections for each row execute function public.defectrag_workspace_insert_audit();
create trigger team_review_audit after insert on public.staff_notes for each row execute function public.defectrag_workspace_insert_audit();

-- Same existing RPC signature and staff boundary, now adds actor/time and an
-- idempotent audit event. Previously acknowledged rows are not backfilled.
create or replace function public.defectrag_acknowledge_review(p_id text)
returns integer language plpgsql security definer set search_path='' as $$
declare r public.shared_inspections;
begin
  if not public.defectrag_is_staff() then raise insufficient_privilege using message='Approved staff required'; end if;
  select * into r from public.shared_inspections where id=p_id and archived_at is null for update;
  if r.id is null then return 0; end if;
  if coalesce((r.payload->>'alert_acknowledged')::boolean,false) then return 1; end if;
  update public.shared_inspections set payload=payload||jsonb_build_object(
    'alert_acknowledged',true,'alert_acknowledged_by',auth.uid(),'alert_acknowledged_at',now()) where id=p_id;
  insert into public.team_audit(actor_id,action,inspection_ids) values(auth.uid(),'acknowledge',array[p_id]);
  return 1;
end; $$;

revoke all on function public.defectrag_personal_action(text,text,text,jsonb),
  public.defectrag_personal_archive(text[],boolean),public.defectrag_share_personal(text,text,text,boolean),
  public.defectrag_workspace_stats(text),public.defectrag_acknowledge_review(text),
  public.defectrag_workspace_insert_audit() from public,anon,authenticated;
grant execute on function public.defectrag_personal_action(text,text,text,jsonb),
  public.defectrag_personal_archive(text[],boolean),public.defectrag_share_personal(text,text,text,boolean),
  public.defectrag_workspace_stats(text),public.defectrag_acknowledge_review(text) to authenticated;
commit;

-- After successful manual execution AND application deployment, set HF variable
-- DEFECTRAG_PERSONAL_WORKSPACE=1. Do not enable before the SQL succeeds.
-- Existing users still require the existing staff allowlist. No public signup.
