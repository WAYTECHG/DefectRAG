-- REVIEW / MANUAL EXECUTION ONLY. No activation, staff grants or data deletion.
-- Prerequisites: personal workspace + native auth/MFA migrations already applied.
begin;
alter table public.personal_inspections add column sync_version bigint not null default 1;
create index personal_sync_owner_id on public.personal_inspections(owner_id,id);
create table public.personal_sync_receipts (
 owner_id uuid not null references auth.users(id), operation_id uuid not null,
 inspection_id text not null, request_hash text not null, version bigint not null,
 created_at timestamptz not null default now(), primary key(owner_id,operation_id)
);
alter table public.personal_sync_receipts enable row level security;
revoke all on public.personal_sync_receipts from public,anon,authenticated;

create function public.defectrag_personal_sync_version() returns trigger
language plpgsql set search_path='' as $$
begin new.sync_version=old.sync_version+1; return new; end; $$;
revoke all on function public.defectrag_personal_sync_version() from public,anon,authenticated;
create trigger personal_sync_version before update on public.personal_inspections
 for each row execute function public.defectrag_personal_sync_version();

-- Native cloud review-note inserts must also invalidate stale local revisions.
create function public.defectrag_personal_sync_note_version() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 update public.personal_inspections set sync_version=sync_version where id=new.inspection_id;
 return new;
end; $$;
revoke all on function public.defectrag_personal_sync_note_version() from public,anon,authenticated;
create trigger personal_sync_note_version after insert on public.personal_notes
 for each row execute function public.defectrag_personal_sync_note_version();

create function public.defectrag_personal_sync_apply(
 p_operation uuid,p_id text,p_base bigint,p_action text,p_data jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.personal_inspections; receipt public.personal_sync_receipts;
 fingerprint text; result_version bigint;
begin
 if not public.defectrag_is_staff() or auth.uid() is null then
  raise insufficient_privilege using message='Approved account and required MFA needed'; end if;
 if p_operation is null or p_id is null or p_id!~'^[a-f0-9]{32}$' or p_base is null or p_base<0
  or p_action is null or p_action not in ('create','conversation','review','acknowledge','archive','restore')
  or p_data is null or jsonb_typeof(p_data)<>'object' or octet_length(p_data::text)>1000000 then
  raise exception 'Invalid bounded synchronization operation'; end if;
 fingerprint=encode(sha256(convert_to(jsonb_build_array(p_id,p_base,p_action,p_data)::text,'UTF8')),'hex');
 -- Serialize retries for one inspection, including concurrent first insertion.
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_id,0));
 select * into receipt from public.personal_sync_receipts where owner_id=auth.uid() and operation_id=p_operation;
 if found then
  if receipt.request_hash<>fingerprint then raise exception 'Operation ID reused with different contents'; end if;
  return jsonb_build_object('version',receipt.version,'replayed',true);
 end if;
 select * into r from public.personal_inspections where id=p_id for update;
 if r.id is not null and r.owner_id<>auth.uid() then
  raise insufficient_privilege using message='Personal inspection unavailable'; end if;
 if p_action='create' then
  if r.id is not null or p_base<>0 then return jsonb_build_object('conflict',true); end if;
  if p_data->'record'->>'id' is distinct from p_id or
   coalesce(p_data->'record'->>'category','') not in ('pcb1','capsules','cashew','candle','chewinggum','fryum','macaroni1','macaroni2','pcb2','pcb3','pcb4','pipe_fryum') or
   coalesce(p_data->'record'->>'verdict','') not in ('Good','Anomalous','Uncertain') or
   (p_data->>'image_path') is null or (p_data->>'heatmap_path') is null or
   (p_data->>'image_path')!~('^'||auth.uid()::text||'/'||p_id||'/image-[a-f0-9]{64}\.jpg$') or
   (p_data->>'heatmap_path')!~('^'||auth.uid()::text||'/'||p_id||'/heatmap-[a-f0-9]{64}\.jpg$') or
   not exists(select 1 from storage.objects where bucket_id='personal-inspections' and name=p_data->>'image_path') or
   not exists(select 1 from storage.objects where bucket_id='personal-inspections' and name=p_data->>'heatmap_path') then
   raise exception 'Owned immutable inspection artifacts required'; end if;
  insert into public.personal_inspections(id,owner_id,created_at,payload,image_path,heatmap_path)
   values(p_id,auth.uid(),(p_data->'record'->>'created_at')::timestamptz,
    (p_data->'record')-'owner_id'-'workspace'-'storage'-'image_url'-'heatmap_url'-'report_url',p_data->>'image_path',p_data->>'heatmap_path');
 else
  if r.id is null then return jsonb_build_object('conflict',true); end if;
  if r.sync_version<>p_base or (r.archived_at is not null and p_action<>'restore') then
   return jsonb_build_object('conflict',true); end if;
  if p_action='conversation' then
   perform public.defectrag_personal_action(p_id,'conversation',p_data->>'question',p_data->'answer');
  elsif p_action='acknowledge' then
   perform public.defectrag_personal_action(p_id,'acknowledge');
  elsif p_action='review' then
   if coalesce(char_length(p_data->>'body'),0) not between 1 and 2000 then raise exception 'Invalid review'; end if;
   insert into public.personal_notes(id,inspection_id,author_id,body)
    values(p_operation,p_id,auth.uid(),p_data->>'body');
  else
   perform public.defectrag_personal_archive(array[p_id],p_action='restore');
  end if;
 end if;
 select sync_version into result_version from public.personal_inspections where id=p_id;
 insert into public.personal_sync_receipts(owner_id,operation_id,inspection_id,request_hash,version)
  values(auth.uid(),p_operation,p_id,fingerprint,result_version);
 return jsonb_build_object('version',result_version,'replayed',false);
end; $$;
revoke all on function public.defectrag_personal_sync_apply(uuid,text,bigint,text,jsonb) from public,anon,authenticated;
grant execute on function public.defectrag_personal_sync_apply(uuid,text,bigint,text,jsonb) to authenticated;
-- The function still freshly checks approved membership + current MFA. No service key.
commit;
