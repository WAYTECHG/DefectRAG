-- REVIEW ONLY. DESTRUCTIVE: separate approval and private backup REQUIRED.
-- Exact target: saputangan1404@gmail.com, disposable QA Staff account only.
-- Deletes precisely SIX QA metadata rows: membership1/request1/audit2/outbox2.
-- Does NOT delete auth.users, images, inspections, other accounts or schema.
-- After successful approved execution, manually delete this exact Auth account
-- through Supabase Dashboard. Never delete a Developer account or use CASCADE.
-- Notifications must remain disabled and no notification worker may be running.
begin;
set local lock_timeout='5s';
set local statement_timeout='20s';
do $qa_cleanup$
declare
 qa_id uuid;
 qa_count bigint;
 removed_count bigint;
 dependency record;
begin
 if (select count(*) from auth.users where lower(email)='saputangan1404@gmail.com')<>1 then
  raise exception 'STOP: expected exactly one target Auth account';
 end if;
 select id into strict qa_id from auth.users
 where lower(email)='saputangan1404@gmail.com' for update;
 -- Lock target parent rows; new FK-linked inserts/role changes must wait.
 perform 1 from public.staff_members where user_id=qa_id for update;
 perform 1 from public.staff_access_requests where user_id=qa_id for update;
 if not exists(select 1 from public.staff_members where user_id=qa_id
  and role='staff' and revoked_at is null) then
  raise exception 'STOP: target must still be active Staff, never Developer';
 end if;
 if not exists(select 1 from public.staff_access_requests where user_id=qa_id
  and status='approved') then raise exception 'STOP: target request changed'; end if;
 if (select count(*) from public.staff_access_audit where subject_id=qa_id)<>2
 or (select count(*) from public.staff_notification_outbox where subject_id=qa_id)<>2 then
  raise exception 'STOP: expected two QA audit rows and two QA notification rows';
 end if;
 if exists(select 1 from public.staff_access_audit where actor_id=qa_id and subject_id<>qa_id)
 or exists(select 1 from public.staff_notification_outbox where recipient_id=qa_id and subject_id<>qa_id)
 or exists(select 1 from public.staff_access_requests where decided_by=qa_id)
 or exists(select 1 from public.staff_members where revoked_by=qa_id) then
  raise exception 'STOP: target has additional decision/audit/recipient dependencies';
 end if;
 if exists(select 1 from public.staff_notification_outbox where subject_id=qa_id
  and (status not in ('queued','superseded') or attempts<>0 or delivered_at is not null
   or lease_token is not null or lease_until is not null or email_payload is not null
   or email_first_attempt_at is not null)) then
  raise exception 'STOP: notification was attempted/prepared/leased or changed';
 end if;
 -- Refuse unknown incoming links or custom triggers on rows being deleted.
 if exists(select 1 from pg_constraint k where k.contype='f'
  and k.confrelid in ('public.staff_members'::regclass,'public.staff_access_requests'::regclass,
   'public.staff_access_audit'::regclass,'public.staff_notification_outbox'::regclass)
  and not(k.confrelid='public.staff_access_requests'::regclass
   and k.conrelid='public.staff_notification_outbox'::regclass
   and k.conkey=array[(select attnum from pg_attribute
    where attrelid=k.conrelid and attname='subject_id')]::smallint[]
   and k.confkey=array[(select attnum from pg_attribute
    where attrelid=k.confrelid and attname='user_id')]::smallint[]
   and k.confdeltype='a' and k.confupdtype='a')) then
  raise exception 'STOP: unexpected incoming dependency needs review';
 end if;
 if exists(select 1 from pg_trigger where not tgisinternal and tgenabled<>'D'
  and tgrelid in ('public.staff_members'::regclass,'public.staff_access_requests'::regclass,
   'public.staff_access_audit'::regclass,'public.staff_notification_outbox'::regclass)) then
  raise exception 'STOP: custom trigger needs review';
 end if;
 -- Inspect live single-column Auth FK links, including optional workspace tables.
 for dependency in
  select n.nspname,c.relname,a.attname,k.conkey
  from pg_constraint k join pg_class c on c.oid=k.conrelid
  join pg_namespace n on n.oid=c.relnamespace
  join pg_attribute a on a.attrelid=c.oid and a.attnum=k.conkey[1]
  where k.contype='f' and k.confrelid='auth.users'::regclass and n.nspname<>'auth'
 loop
  if cardinality(dependency.conkey)<>1 then raise exception 'STOP: composite Auth dependency'; end if;
  if dependency.nspname='public' and (
   (dependency.relname='staff_members' and dependency.attname='user_id') or
   (dependency.relname='staff_access_requests' and dependency.attname='user_id') or
   (dependency.relname='staff_access_audit' and dependency.attname in ('subject_id','actor_id')) or
   (dependency.relname='staff_notification_outbox' and dependency.attname='recipient_id')) then
   continue;
  end if;
  execute format('select count(*) from %I.%I where %I=$1',
   dependency.nspname,dependency.relname,dependency.attname) into qa_count using qa_id;
  if qa_count<>0 then raise exception 'STOP: linked data in %.% (%) needs review',
   dependency.nspname,dependency.relname,dependency.attname; end if;
 end loop;
 if exists(select 1 from storage.objects where split_part(name,'/',1)=qa_id::text) then
  raise exception 'STOP: target has stored artifacts';
 end if;
 -- Supabase versions differ: inspect either ownership column without assuming type.
 for dependency in select attname from pg_attribute
  where attrelid='storage.objects'::regclass and attname in ('owner','owner_id')
   and not attisdropped
 loop
  execute format('select count(*) from storage.objects where %I::text=$1',dependency.attname)
   into qa_count using qa_id::text;
  if qa_count<>0 then raise exception 'STOP: target owns Storage objects'; end if;
 end loop;
 delete from public.staff_notification_outbox where subject_id=qa_id;
 get diagnostics removed_count=row_count;
 if removed_count<>2 then raise exception 'STOP: notification count changed'; end if;
 delete from public.staff_access_audit where subject_id=qa_id;
 get diagnostics removed_count=row_count;
 if removed_count<>2 then raise exception 'STOP: audit count changed'; end if;
 delete from public.staff_access_requests where user_id=qa_id;
 get diagnostics removed_count=row_count;
 if removed_count<>1 then raise exception 'STOP: request count changed'; end if;
 delete from public.staff_members where user_id=qa_id and role='staff';
 get diagnostics removed_count=row_count;
 if removed_count<>1 then raise exception 'STOP: membership count changed'; end if;
 raise notice 'Six QA metadata rows removed; Auth account remains for separate Dashboard deletion.';
end;
$qa_cleanup$;
commit;
