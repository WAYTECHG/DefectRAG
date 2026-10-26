-- REVIEW ONLY: NOT EXECUTED. Apply after all previously reviewed workspace SQL.
-- New switches default OFF. No account is enrolled, approved or revoked here.
-- Existing tables/records and public Gallery grants remain intact.
begin;
create table public.defectrag_auth_settings (
  singleton boolean primary key default true check(singleton),
  registration_enabled boolean not null default false,
  mfa_required boolean not null default false
);
insert into public.defectrag_auth_settings(singleton) values(true);
alter table public.defectrag_auth_settings enable row level security;
revoke all on public.defectrag_auth_settings from public,anon,authenticated,service_role;

alter table public.staff_members add column revoked_at timestamptz;
alter table public.staff_members add column revoked_by uuid references auth.users(id);

create table public.staff_access_requests (
  user_id uuid primary key references auth.users(id),
  display_name text not null check(char_length(display_name) between 1 and 80),
  status text not null default 'pending' check(status in ('pending','approved','rejected','revoked')),
  version integer not null default 1 check(version>0),
  created_at timestamptz not null default now(),
  decided_at timestamptz, decided_by uuid references auth.users(id)
);
create table public.staff_access_audit (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references auth.users(id),
  actor_id uuid not null references auth.users(id),
  action text not null, version integer not null,
  created_at timestamptz not null default now()
);
create table public.staff_notification_outbox (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references public.staff_access_requests(user_id),
  recipient_id uuid not null references auth.users(id),
  version integer not null, kind text not null check(kind in ('requested','approved','rejected','revoked')),
  status text not null default 'queued' check(status in ('queued','sending','sent','dead','superseded')),
  attempts integer not null default 0,
  next_attempt_at timestamptz not null default now(),
  lease_token uuid, lease_until timestamptz,
  last_error text, created_at timestamptz not null default now(), delivered_at timestamptz,
  unique(subject_id,version,kind,recipient_id)
);
create index staff_notification_due on public.staff_notification_outbox(status,next_attempt_at);
alter table public.staff_access_requests enable row level security;
alter table public.staff_access_audit enable row level security;
alter table public.staff_notification_outbox enable row level security;
revoke all on public.staff_access_requests,public.staff_access_audit,public.staff_notification_outbox from public,anon,authenticated,service_role;

-- Claims come from the Supabase-validated JWT, never client-provided JSON.
-- Check that a verified native TOTP factor still exists: factor removal must not
-- let a previously issued AAL2 JWT alone pass this application's boundary.
create function public.defectrag_has_aal2() returns boolean
language sql stable security definer set search_path='' as $$
  select coalesce(auth.jwt()->>'aal'='aal2',false) and exists(
    select 1 from auth.mfa_factors f where f.user_id=auth.uid()
      and f.factor_type='totp' and f.status='verified');
$$;
create or replace function public.defectrag_is_staff() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.staff_members s where s.user_id=auth.uid() and s.revoked_at is null)
    and exists(select 1 from public.defectrag_auth_settings c where c.singleton
      and (not c.mfa_required or public.defectrag_has_aal2()));
$$;
create or replace function public.defectrag_is_developer() returns boolean
language sql stable security definer set search_path='' as $$
  select public.defectrag_is_staff() and exists(select 1 from public.staff_members
    where user_id=auth.uid() and role='developer' and revoked_at is null);
$$;
create function public.defectrag_can_manage_access() returns boolean
language sql stable security definer set search_path='' as $$
  select public.defectrag_is_developer() and public.defectrag_has_aal2();
$$;

-- No private directory/data is returned at AAL1: only the caller's posture.
create function public.defectrag_auth_status() returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare s public.staff_members; r public.staff_access_requests; c public.defectrag_auth_settings;
begin
  if auth.uid() is null then raise insufficient_privilege using message='Sign in required'; end if;
  select * into s from public.staff_members where user_id=auth.uid();
  select * into r from public.staff_access_requests where user_id=auth.uid();
  select * into strict c from public.defectrag_auth_settings where singleton;
  return jsonb_build_object('user_id',auth.uid(),'display_name',s.display_name,'role',s.role,
    'approved',s.user_id is not null and s.revoked_at is null,
    'revoked',s.revoked_at is not null,'request_status',r.status,'request_version',r.version,
    'email_verified',exists(select 1 from auth.users where id=auth.uid() and email_confirmed_at is not null),
    'aal2',public.defectrag_has_aal2(),'mfa_required',c.mfa_required,
    'registration_enabled',c.registration_enabled,'authorized',public.defectrag_is_staff());
end; $$;

create function public.defectrag_request_access(p_display_name text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r public.staff_access_requests; subject uuid:=auth.uid();
begin
  if subject is null or not exists(select 1 from auth.users where id=subject and email_confirmed_at is not null)
    then raise insufficient_privilege using message='Verified email required'; end if;
  if not exists(select 1 from public.defectrag_auth_settings where singleton and registration_enabled)
    then raise insufficient_privilege using message='Registration is not enabled'; end if;
  if p_display_name is null or char_length(btrim(p_display_name)) not between 1 and 80
    then raise exception 'Display name must contain 1-80 characters'; end if;
  -- Serialize registration and all decisions for this identity, including absent rows.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(subject::text,0));
  if exists(select 1 from public.staff_members where user_id=subject)
    then return public.defectrag_auth_status(); end if;
  select * into r from public.staff_access_requests where user_id=subject for update;
  if r.user_id is not null then return public.defectrag_auth_status(); end if;
  insert into public.staff_access_requests(user_id,display_name) values(subject,btrim(p_display_name));
  insert into public.staff_access_audit(subject_id,actor_id,action,version) values(subject,subject,'requested',1);
  insert into public.staff_notification_outbox(subject_id,recipient_id,version,kind)
    select subject,s.user_id,1,'requested' from public.staff_members s join auth.users u on u.id=s.user_id
    where s.role='developer' and s.revoked_at is null and u.email_confirmed_at is not null;
  return public.defectrag_auth_status();
end; $$;

create function public.defectrag_access_directory() returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
  if not public.defectrag_can_manage_access() then raise insufficient_privilege using message='Developer AAL2 required'; end if;
  return coalesce((select jsonb_agg(to_jsonb(t) order by t.created_at desc nulls last) from (
    select coalesce(r.user_id,s.user_id) user_id,coalesce(r.display_name,s.display_name) display_name,
      u.email,s.role,case when s.revoked_at is not null then 'revoked' when s.user_id is not null
        then 'approved' else r.status end status,coalesce(r.version,0) version,r.created_at
    from public.staff_access_requests r full join public.staff_members s on s.user_id=r.user_id
      join auth.users u on u.id=coalesce(r.user_id,s.user_id)
  ) t),'[]'::jsonb);
end; $$;

create function public.defectrag_decide_access(p_user_id uuid,p_action text,p_version integer) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r public.staff_access_requests; s public.staff_members; next_status text; next_version integer;
begin
  -- Serialize developer decisions globally to make last-developer checks safe.
  perform pg_catalog.pg_advisory_xact_lock(731902461);
  if not public.defectrag_can_manage_access() then raise insufficient_privilege using message='Developer AAL2 required'; end if;
  if p_user_id is null or p_user_id=auth.uid() or p_action is null or p_action not in ('approve','reject','revoke')
    then raise insufficient_privilege using message='A valid other account and action are required'; end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_user_id::text,0));
  select * into r from public.staff_access_requests where user_id=p_user_id for update;
  select * into s from public.staff_members where user_id=p_user_id for update;
  if p_version is null or p_version<>coalesce(r.version,0) then raise exception 'Request changed; refresh before deciding'; end if;
  if not exists(select 1 from auth.users where id=p_user_id and email_confirmed_at is not null)
    then raise exception 'Verified account required'; end if;
  if p_action in ('approve','reject') then
    if r.status is distinct from 'pending' or s.user_id is not null then raise exception 'Only pending requests can be decided'; end if;
    next_status:=case when p_action='approve' then 'approved' else 'rejected' end;
  else
    if s.user_id is null or s.revoked_at is not null then raise exception 'Active staff account required'; end if;
    if s.role='developer' and (select count(*) from public.staff_members where role='developer' and revoked_at is null)<=1
      then raise exception 'The last developer cannot be revoked'; end if;
    next_status:='revoked';
  end if;
  next_version:=coalesce(r.version,0)+1;
  insert into public.staff_access_requests(user_id,display_name,status,version,decided_at,decided_by)
    values(p_user_id,coalesce(r.display_name,s.display_name),next_status,next_version,now(),auth.uid())
    on conflict(user_id) do update set status=excluded.status,version=excluded.version,
      decided_at=excluded.decided_at,decided_by=excluded.decided_by;
  if p_action='approve' then
    insert into public.staff_members(user_id,display_name,role) values(p_user_id,r.display_name,'staff');
  elsif p_action='revoke' then
    update public.staff_members set revoked_at=now(),revoked_by=auth.uid() where user_id=p_user_id;
  end if;
  insert into public.staff_access_audit(subject_id,actor_id,action,version) values(p_user_id,auth.uid(),next_status,next_version);
  update public.staff_notification_outbox set status='superseded',lease_token=null,lease_until=null
    where subject_id=p_user_id and status in ('queued','sending','dead');
  insert into public.staff_notification_outbox(subject_id,recipient_id,version,kind)
    values(p_user_id,p_user_id,next_version,next_status);
  return jsonb_build_object('status',next_status,'version',next_version);
end; $$;

-- Additional restrictive guards intersect with existing owner/scope policies.
do $$ declare target text; begin
  foreach target in array array['staff_members','shared_inspections','staff_notes','team_audit',
    'personal_inspections','personal_notes','personal_audit'] loop
    execute format('create policy staff_auth_guard on public.%I as restrictive for all to authenticated using(public.defectrag_is_staff()) with check(public.defectrag_is_staff())',target);
  end loop;
end; $$;
create policy private_artifact_auth_guard on storage.objects as restrictive for all to authenticated
  using(bucket_id not in ('team-inspections','personal-inspections') or public.defectrag_is_staff())
  with check(bucket_id not in ('team-inspections','personal-inspections') or public.defectrag_is_staff());
create policy access_request_own on public.staff_access_requests for select to authenticated
  using(user_id=auth.uid() or public.defectrag_can_manage_access());
create policy access_audit_developer on public.staff_access_audit for select to authenticated using(public.defectrag_can_manage_access());
grant select on public.staff_access_requests,public.staff_access_audit to authenticated;

-- Administrative switch: deliberately NOT granted to browser or service roles.
-- Run only after separately approved bootstrap/activation, not in this migration.
create function public.defectrag_configure_auth(p_registration boolean,p_mfa boolean) returns void
language plpgsql security definer set search_path='' as $$
begin
  if p_registration is null or p_mfa is null then raise exception 'Explicit switches required'; end if;
  if p_mfa and not exists(select 1 from public.staff_members s join auth.mfa_factors f on f.user_id=s.user_id
    where s.role='developer' and s.revoked_at is null and f.factor_type='totp' and f.status='verified')
    then raise exception 'Enroll and verify an active developer TOTP factor before enforcement'; end if;
  update public.defectrag_auth_settings set registration_enabled=p_registration,mfa_required=p_mfa where singleton;
end; $$;

-- Only the trusted worker role can claim/ack/retry mail. Never grant to users.
create function public.defectrag_claim_notifications(p_limit integer default 5) returns jsonb
language plpgsql security definer set search_path='' as $$
declare result jsonb;
begin
  if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
  update public.staff_notification_outbox o set status='superseded',lease_token=null,lease_until=null
    where o.status in ('queued','sending','dead') and (not exists(select 1 from public.staff_access_requests r
      where r.user_id=o.subject_id and r.version=o.version) or (o.kind='requested' and not exists(
        select 1 from public.staff_members where user_id=o.recipient_id and role='developer' and revoked_at is null)));
  update public.staff_notification_outbox set status='dead',lease_token=null,lease_until=null
    where attempts>=8 and (status='queued' or (status='sending' and lease_until<now()));
  with selected as (select o.id from public.staff_notification_outbox o
    where o.attempts<8 and (o.status='queued' and o.next_attempt_at<=now() or o.status='sending' and o.lease_until<now())
    order by o.created_at limit least(greatest(coalesce(p_limit,5),1),10) for update skip locked), claimed as (
      update public.staff_notification_outbox o set status='sending',attempts=attempts+1,
        lease_token=gen_random_uuid(),lease_until=now()+interval '5 minutes'
      from selected where o.id=selected.id returning o.*)
  select coalesce(jsonb_agg(jsonb_build_object('event_id',c.id,'lease_token',c.lease_token,
    'request_id',c.subject_id,'version',c.version,'kind',c.kind,'recipient_email',u.email,
    'display_name',r.display_name,'applicant_email',case when c.kind='requested' then a.email else null end)),'[]'::jsonb)
    into result from claimed c join public.staff_access_requests r on r.user_id=c.subject_id
      join auth.users u on u.id=c.recipient_id and u.email_confirmed_at is not null
      join auth.users a on a.id=c.subject_id;
  return result;
end; $$;
create function public.defectrag_finish_notification(p_id uuid,p_lease uuid,p_delivered boolean,p_error text default '') returns boolean
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
  update public.staff_notification_outbox set
    status=case when p_delivered then 'sent' when attempts>=8 then 'dead' else 'queued' end,
    delivered_at=case when p_delivered then now() else null end,
    next_attempt_at=now()+make_interval(secs=>least(3600,30*power(2,greatest(attempts-1,0)))::integer),
    last_error=case when p_delivered then null else left(coalesce(p_error,'delivery_failed'),80) end,
    lease_token=null,lease_until=null
    where id=p_id and status='sending' and lease_token=p_lease and lease_until>now();
  get diagnostics changed=row_count; return changed=1;
end; $$;
create function public.defectrag_retry_notification(p_id uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_can_manage_access() then raise insufficient_privilege using message='Developer AAL2 required'; end if;
  update public.staff_notification_outbox o set status='queued',attempts=0,next_attempt_at=now(),last_error=null
    where id=p_id and status='dead' and exists(select 1 from public.staff_access_requests r where r.user_id=o.subject_id and r.version=o.version);
  get diagnostics changed=row_count; return changed=1;
end; $$;
create function public.defectrag_notification_status() returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
  if not public.defectrag_can_manage_access() then raise insufficient_privilege using message='Developer AAL2 required'; end if;
  return coalesce((select jsonb_agg(to_jsonb(t)) from (select id,kind,status,attempts,last_error,created_at
    from public.staff_notification_outbox order by created_at desc limit 50) t),'[]'::jsonb);
end; $$;

revoke all on function public.defectrag_has_aal2(),public.defectrag_can_manage_access(),public.defectrag_auth_status(),
  public.defectrag_request_access(text),public.defectrag_access_directory(),public.defectrag_decide_access(uuid,text,integer),
  public.defectrag_configure_auth(boolean,boolean),public.defectrag_claim_notifications(integer),
  public.defectrag_finish_notification(uuid,uuid,boolean,text),public.defectrag_retry_notification(uuid),
  public.defectrag_notification_status() from public,anon,authenticated,service_role;
grant execute on function public.defectrag_has_aal2(),public.defectrag_can_manage_access(),public.defectrag_auth_status(),
  public.defectrag_request_access(text),public.defectrag_access_directory(),public.defectrag_decide_access(uuid,text,integer),
  public.defectrag_retry_notification(uuid),public.defectrag_notification_status() to authenticated;
grant execute on function public.defectrag_claim_notifications(integer),public.defectrag_finish_notification(uuid,uuid,boolean,text) to service_role;
commit;
