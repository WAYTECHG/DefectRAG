-- DefectRAG: opt-in public demo gallery. Run manually as project owner.
-- Additive: no staff tables, storage buckets, existing functions or policies changed.
begin;
create table if not exists public.defectrag_gallery_config (
  singleton boolean primary key default true check (singleton),
  key_hash text not null check (key_hash ~ '^[a-f0-9]{64}$')
);
create table if not exists public.defectrag_gallery_entries (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  measurement jsonb not null,
  image text not null check (length(image) between 1 and 160000),
  heatmap text not null check (length(heatmap) between 1 and 160000),
  visible boolean not null default true
);
create table if not exists public.defectrag_gallery_publishers (
  public_id uuid primary key references public.defectrag_gallery_entries(id),
  owner_hash text not null,
  source_hash text not null,
  unique(owner_hash, source_hash)
);
alter table public.defectrag_gallery_config enable row level security;
alter table public.defectrag_gallery_entries enable row level security;
alter table public.defectrag_gallery_publishers enable row level security;
-- No direct client access, including owner/source hashes and secret hashes.
revoke all on public.defectrag_gallery_config, public.defectrag_gallery_entries,
  public.defectrag_gallery_publishers from public, anon, authenticated;

create or replace function public.defectrag_gallery_configure(p_key text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'Expected 64 lowercase hex characters'; end if;
  insert into public.defectrag_gallery_config(singleton,key_hash)
    values(true,encode(sha256(convert_to(p_key,'UTF8')),'hex'))
    on conflict(singleton) do update set key_hash=excluded.key_hash;
end; $$;
revoke all on function public.defectrag_gallery_configure(text) from public, anon, authenticated;
-- Only the SQL Editor/project owner can configure this capability.

create or replace function public.defectrag_gallery_read(p_id uuid default null, p_offset integer default 0)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(item order by created_at desc, id desc),'[]'::jsonb)
  from (
    select e.id,e.created_at,
      jsonb_build_object('id',e.id,'created_at',e.created_at,'measurement',e.measurement)
      || case when p_id is not null then jsonb_build_object('image',e.image,'heatmap',e.heatmap)
         else '{}'::jsonb end as item
    from public.defectrag_gallery_entries e
    where e.visible and (p_id is null or e.id=p_id)
    order by e.created_at desc,e.id desc
    limit case when p_id is null then 12 else 1 end
    offset case when p_id is null then greatest(0,least(coalesce(p_offset,0),100)) else 0 end
  ) listed;
$$;
revoke all on function public.defectrag_gallery_read(uuid,integer) from public;
grant execute on function public.defectrag_gallery_read(uuid,integer) to anon,authenticated;

create or replace function public.defectrag_gallery_write(
  p_key text, p_action text, p_owner text, p_source text default '',
  p_payload jsonb default '{}'::jsonb, p_image text default '', p_heatmap text default '',
  p_id uuid default null, p_moderator boolean default false)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare entry public.defectrag_gallery_entries; public_identifier uuid;
begin
  if p_key is null or not exists (
    select 1 from public.defectrag_gallery_config
    where key_hash=encode(sha256(convert_to(p_key,'UTF8')),'hex')
  ) then raise insufficient_privilege using message='Gallery capability required'; end if;
  if p_owner is null or p_owner !~ '^[a-f0-9]{64}$' then
    raise exception 'Invalid publisher';
  end if;
  -- Serialize capacity and duplicate checks, including concurrent Space workers.
  perform pg_advisory_xact_lock(1877446019);
  if p_action='remove' then
    update public.defectrag_gallery_entries e set visible=false
    where e.id=p_id and (p_moderator is true or exists (
      select 1 from public.defectrag_gallery_publishers p where p.public_id=e.id and p.owner_hash=p_owner
    )) returning e.id into public_identifier;
    if public_identifier is null then raise exception 'Item unavailable or unauthorized'; end if;
    return jsonb_build_object('removed',true);
  end if;
  if p_source is null or p_source !~ '^[a-f0-9]{64}$' then raise exception 'Invalid source'; end if;
  select e.* into entry from public.defectrag_gallery_entries e
    join public.defectrag_gallery_publishers p on p.public_id=e.id
    where p.owner_hash=p_owner and p.source_hash=p_source;
  if p_action='status' then
    if entry.id is null then return null; end if;
    return jsonb_build_object('id',entry.id,'visible',entry.visible);
  end if;
  if p_action<>'publish' then raise exception 'Invalid action'; end if;
  if entry.id is not null then return jsonb_build_object('id',entry.id,'visible',entry.visible); end if;
  if (select count(*) from public.defectrag_gallery_entries)>=100 or
     (select count(*) from public.defectrag_gallery_publishers where owner_hash=p_owner)>=5 then
    raise exception 'Gallery capacity reached';
  end if;
  if jsonb_typeof(p_payload)<>'object' or octet_length(p_payload::text)>8000 or
    p_payload->>'category' is null or p_payload->>'category' not in
      ('pcb1','pcb2','pcb3','pcb4','capsules','cashew','candle','chewinggum','fryum','pipe_fryum','macaroni1','macaroni2') or
    p_payload->>'verdict' is null or p_payload->>'verdict' not in ('Good','Anomalous','Uncertain') or
    jsonb_typeof(p_payload->'score') is distinct from 'number' or
    jsonb_typeof(p_payload->'threshold') is distinct from 'number' or
    exists (select 1 from jsonb_object_keys(p_payload) k where k not in
      ('category','verdict','score','threshold','uncertainty_margin','model_id','localization','scope')) or
    p_image is null or p_heatmap is null or
    length(p_image) not between 1 and 160000 or length(p_heatmap) not between 1 and 160000 or
    p_image !~ '^[A-Za-z0-9+/]+={0,2}$' or p_heatmap !~ '^[A-Za-z0-9+/]+={0,2}$'
  then raise exception 'Invalid public snapshot'; end if;
  insert into public.defectrag_gallery_entries(measurement,image,heatmap)
    values(p_payload,p_image,p_heatmap) returning id into public_identifier;
  insert into public.defectrag_gallery_publishers(public_id,owner_hash,source_hash)
    values(public_identifier,p_owner,p_source);
  return jsonb_build_object('id',public_identifier,'visible',true);
end; $$;
revoke all on function public.defectrag_gallery_write(text,text,text,text,jsonb,text,text,uuid,boolean) from public;
-- API accepts anon calls, but every status/write/removal requires the private,
-- dedicated gallery capability. Anonymous visitors never receive this key.
grant execute on function public.defectrag_gallery_write(text,text,text,text,jsonb,text,text,uuid,boolean) to anon,authenticated;
commit;

-- AFTER reviewing/running the migration, configure the independently generated
-- secret using SQL Editor. Replace the placeholder; do NOT commit the real key:
-- select public.defectrag_gallery_configure('PASTE_64_CHARACTER_GALLERY_KEY');
-- Put that SAME value into HF Space Settings > Secrets: DEFECTRAG_GALLERY_KEY.
-- Also set HF variable DEFECTRAG_GALLERY_ENABLED=1, then restart the Space.
