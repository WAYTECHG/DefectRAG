-- Disposable PostgreSQL only. Synthetic native-Auth/Storage contracts, no network.
\set ON_ERROR_STOP on
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth; create schema storage;
grant usage on schema auth,storage to anon,authenticated,service_role;
create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('qa.uid',true),'')::uuid $$;
create table public.staff_members(user_id uuid primary key,role text,revoked_at timestamptz);
create function public.defectrag_is_staff() returns boolean language sql stable security definer set search_path='' as $$
 select coalesce(current_setting('qa.aal',true),'')='aal2' and exists(select 1 from public.staff_members where user_id=auth.uid() and revoked_at is null) $$;
create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(bucket_id text,name text,primary key(bucket_id,name));
alter table storage.objects enable row level security;
grant select,insert on storage.objects to authenticated;
create function storage.foldername(text) returns text[] language sql immutable as $$ select (string_to_array($1,'/'))[1:array_length(string_to_array($1,'/'),1)-1] $$;
create table public.shared_inspections(id text primary key,owner_id uuid,created_at timestamptz,payload jsonb,conversation jsonb,image_path text,heatmap_path text,archived_at timestamptz);
create table public.staff_notes(id uuid primary key,inspection_id text,author_id uuid,body text,created_at timestamptz);
create table public.team_audit(actor_id uuid,action text,inspection_ids text[]);
\ir supabase_personal_workspace.sql
\ir supabase_personal_sync.sql

insert into auth.users values('11111111-1111-4111-8111-111111111111'),('22222222-2222-4222-8222-222222222222'),('33333333-3333-4333-8333-333333333333');
insert into public.staff_members values('11111111-1111-4111-8111-111111111111','staff',null),('22222222-2222-4222-8222-222222222222','developer',null);
insert into storage.objects values
 ('personal-inspections','11111111-1111-4111-8111-111111111111/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/image-'||repeat('c',64)||'.jpg'),
 ('personal-inspections','11111111-1111-4111-8111-111111111111/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/heatmap-'||repeat('d',64)||'.jpg');

begin;
set local role authenticated;
set local qa.uid='11111111-1111-4111-8111-111111111111';set local qa.aal='aal2';
do $$ declare data jsonb; result jsonb; begin
 data=jsonb_build_object('record',jsonb_build_object('id',repeat('a',32),'category','pcb1','verdict','Anomalous','score',0.2,'threshold',0.1,'created_at','2026-10-22T00:00:00Z'),
  'image_path','11111111-1111-4111-8111-111111111111/'||repeat('a',32)||'/image-'||repeat('c',64)||'.jpg',
  'heatmap_path','11111111-1111-4111-8111-111111111111/'||repeat('a',32)||'/heatmap-'||repeat('d',64)||'.jpg');
 result=public.defectrag_personal_sync_apply('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',repeat('a',32),0,'create',data);
 if result->>'version'<>'1' then raise exception 'Create revision failed'; end if;
 result=public.defectrag_personal_sync_apply('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',repeat('a',32),0,'create',data);
 if result->>'replayed'<>'true' or (select count(*) from public.personal_inspections)<>1 then raise exception 'Duplicate create'; end if;
 begin
  perform public.defectrag_personal_sync_apply('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',repeat('a',32),0,'create',data||'{"changed":true}'::jsonb);
  raise exception 'Changed replay accepted';
 exception when raise_exception then if sqlerrm='Changed replay accepted' then raise; end if; end;
 perform public.defectrag_personal_action(repeat('a',32),'conversation','Cloud question','{"answer":"Fixture"}');
 if (select sync_version from public.personal_inspections)<>2 then raise exception 'Native cloud update not versioned'; end if;
 result=public.defectrag_personal_sync_apply('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',repeat('a',32),1,'acknowledge','{}');
 if result->>'conflict'<>'true' then raise exception 'Stale write accepted'; end if;
 result=public.defectrag_personal_sync_apply('cccccccc-cccc-4ccc-8ccc-cccccccccccc',repeat('a',32),2,'review','{"body":"Fixture review"}');
 if result->>'version'<>'3' then raise exception 'Review did not advance parent revision'; end if;
 perform public.defectrag_personal_archive(array[repeat('a',32)],false);
 if (select sync_version from public.personal_inspections)<>4 then raise exception 'Archive not versioned'; end if;
 result=public.defectrag_personal_sync_apply('dddddddd-dddd-4ddd-8ddd-dddddddddddd',repeat('a',32),4,'restore','{}');
 if result->>'version'<>'5' or (select archived_at from public.personal_inspections) is not null then raise exception 'Restore failed'; end if;
end $$;

-- The Developer account has no exception to another owner's personal records.
set local qa.uid='22222222-2222-4222-8222-222222222222';
do $$ begin
 if exists(select 1 from public.personal_inspections) then raise exception 'Cross-owner RLS leak'; end if;
 if exists(select 1 from storage.objects) then raise exception 'Cross-owner image RLS leak'; end if;
 begin
  perform public.defectrag_personal_sync_apply(gen_random_uuid(),repeat('a',32),5,'acknowledge','{}');
  raise exception 'Cross-owner RPC accepted';
 exception when insufficient_privilege then null; end;
end $$;
set local qa.uid='33333333-3333-4333-8333-333333333333';
do $$ begin
 begin perform public.defectrag_personal_sync_apply(gen_random_uuid(),repeat('a',32),5,'acknowledge','{}');raise exception 'Pending applicant accepted';exception when insufficient_privilege then null;end;
end $$;
set local qa.uid='11111111-1111-4111-8111-111111111111';set local qa.aal='aal1';
do $$ begin
 if exists(select 1 from public.personal_inspections) then raise exception 'AAL1 read accepted'; end if;
 begin perform public.defectrag_personal_sync_apply(gen_random_uuid(),repeat('a',32),5,'acknowledge','{}');raise exception 'AAL1 write accepted';exception when insufficient_privilege then null;end;
end $$;
reset role;
do $$ begin
 if has_function_privilege('anon','public.defectrag_personal_sync_apply(uuid,text,bigint,text,jsonb)','EXECUTE') then raise exception 'Anonymous RPC grant'; end if;
 if has_table_privilege('authenticated','public.personal_sync_receipts','SELECT') then raise exception 'Private receipt table exposed'; end if;
 if (select count(*) from public.personal_sync_receipts)<>3 then raise exception 'Conflicts/retries created receipts'; end if;
end $$;
rollback;
select 'personal sync owner/MFA/RLS/CAS/replay/archive contracts passed' as result;
