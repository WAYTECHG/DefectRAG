-- REVIEW ONLY: additive and inactive. Never executes from the application.
-- Requires existing team workspace + native auth/MFA migrations.
begin;
create table public.corrective_action_settings (
 singleton boolean primary key default true check(singleton), automation_enabled boolean not null default false
);
insert into public.corrective_action_settings(singleton) values(true);
create table public.corrective_actions (
 id uuid primary key default gen_random_uuid(), inspection_id text not null references public.shared_inspections(id),
 review_id uuid not null unique references public.staff_notes(id), reviewer_id uuid not null references auth.users(id),
 review_snapshot text not null, confirmed_by uuid not null references auth.users(id),
 owner_id uuid not null references public.staff_members(user_id), supervisor_id uuid not null references public.staff_members(user_id),
 priority text not null check(priority in ('Low','Normal','High','Critical')),
 description text not null check(char_length(btrim(description)) between 10 and 2000),
 due_at timestamptz not null, state text not null default 'Open' check(state in ('Open','Assigned','In Progress','Resolved','Closed','Cancelled')),
 version integer not null default 1, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 resolved_at timestamptz, resolution text, closed_at timestamptz
);
create table public.corrective_action_history (
 id uuid primary key default gen_random_uuid(), case_id uuid not null references public.corrective_actions(id),
 version integer not null, actor_id uuid not null references auth.users(id), state text not null,
 note text not null, snapshot jsonb not null, created_at timestamptz not null default now(), unique(case_id,version)
);
create table public.corrective_action_events (
 id uuid primary key default gen_random_uuid(), case_id uuid not null references public.corrective_actions(id),
 version integer not null, kind text not null check(kind in ('created','updated','reminder','overdue')),
 status text not null default 'queued' check(status in ('queued','sending','sent','dead','superseded')),
 attempts integer not null default 0, next_attempt_at timestamptz not null default now(),
 lease_token uuid, lease_until timestamptz, last_error text, created_at timestamptz not null default now(),
 unique(case_id,version,kind)
);
create table public.corrective_action_effects (
 event_id uuid not null references public.corrective_action_events(id),
 effect text not null check(effect in ('notification','ticket')),
 state text not null check(state in ('processing','done','uncertain')),
 receipt text, started_at timestamptz not null default now(), finished_at timestamptz,
 primary key(event_id,effect)
);
alter table public.corrective_action_settings enable row level security;
alter table public.corrective_actions enable row level security;
alter table public.corrective_action_history enable row level security;
alter table public.corrective_action_events enable row level security;
alter table public.corrective_action_effects enable row level security;
revoke all on public.corrective_action_settings,public.corrective_actions,public.corrective_action_history,public.corrective_action_events,public.corrective_action_effects from public,anon,authenticated,service_role;

create function public.defectrag_ca_staff() returns boolean
language sql stable security definer set search_path='' as $$
 select public.defectrag_is_staff() and public.defectrag_has_aal2();
$$;
create function public.defectrag_ca_visible(p_case uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select public.defectrag_ca_staff() and exists(select 1 from public.corrective_actions c
 join public.shared_inspections i on i.id=c.inspection_id where c.id=p_case
 and (i.archived_at is null or public.defectrag_is_developer()));
$$;
create policy ca_read on public.corrective_actions for select to authenticated using(public.defectrag_ca_visible(id));
create policy ca_history_read on public.corrective_action_history for select to authenticated using(public.defectrag_ca_visible(case_id));
create policy ca_events_read on public.corrective_action_events for select to authenticated using(public.defectrag_ca_visible(case_id));
create policy ca_effects_read on public.corrective_action_effects for select to authenticated using(exists(
 select 1 from public.corrective_action_events e where e.id=event_id and public.defectrag_ca_visible(e.case_id)));
grant select on public.corrective_actions,public.corrective_action_history to authenticated;
-- Payload-free delivery status; never expose lease capabilities in browser queries.
grant select(id,case_id,version,kind,status,attempts,last_error,created_at) on public.corrective_action_events to authenticated;
grant select(event_id,effect,state,started_at,finished_at) on public.corrective_action_effects to authenticated;

create function public.defectrag_create_corrective_action(p_inspection text,p_review uuid,p_confirmed boolean,
 p_owner uuid,p_supervisor uuid,p_priority text,p_description text,p_due timestamptz) returns uuid
language plpgsql security definer set search_path='' as $$
declare n public.staff_notes; review jsonb; result uuid;
begin
 if not public.defectrag_ca_staff() then raise insufficient_privilege using message='Approved staff and native TOTP AAL2 required'; end if;
 if p_confirmed is distinct from true then raise exception 'Explicit human defect confirmation required'; end if;
 perform 1 from public.shared_inspections where id=p_inspection and archived_at is null for update;
 if not found then raise exception 'Active team inspection required'; end if;
 select * into n from public.staff_notes where id=p_review and inspection_id=p_inspection;
 if not found or n.body not like 'DEFECTRAG_REVIEW_V1:%' then raise exception 'Recorded human review required'; end if;
 review:=substring(n.body from length('DEFECTRAG_REVIEW_V1:')+1)::jsonb;
 if review->>'status' is distinct from 'Reviewed' or review->>'decision' is distinct from 'Reject'
 or not exists(select 1 from public.staff_members where user_id=n.author_id and revoked_at is null)
 or exists(select 1 from public.staff_notes x where x.inspection_id=p_inspection
  and x.body like 'DEFECTRAG_REVIEW_V1:%' and (x.created_at,x.id)>(n.created_at,n.id)) then
  raise exception 'Latest reviewed Reject disposition by active staff required'; end if;
 -- Reject alone is a disposition, NOT a diagnosis. p_confirmed is a separate
 -- explicit human attestation, recorded with actor + immutable review snapshot.
 if p_due is null or p_due<=now() or p_due>now()+interval '365 days' then raise exception 'Due date must be within the next year'; end if;
 if not exists(select 1 from public.staff_members where user_id=p_owner and revoked_at is null)
 or not exists(select 1 from public.staff_members where user_id=p_supervisor and revoked_at is null) then raise exception 'Active owner and supervisor required'; end if;
 insert into public.corrective_actions(inspection_id,review_id,reviewer_id,review_snapshot,confirmed_by,owner_id,supervisor_id,priority,description,due_at)
 values(p_inspection,p_review,n.author_id,n.body,auth.uid(),p_owner,p_supervisor,p_priority,btrim(p_description),p_due) returning id into result;
 insert into public.corrective_action_history(case_id,version,actor_id,state,note,snapshot)
 select result,1,auth.uid(),'Open','Human-confirmed defect; case created',jsonb_build_object('owner_id',owner_id,'supervisor_id',supervisor_id,'due_at',due_at,'priority',priority)
 from public.corrective_actions where id=result;
 insert into public.corrective_action_events(case_id,version,kind) values(result,1,'created');
 return result;
end; $$;

create function public.defectrag_update_corrective_action(p_id uuid,p_version integer,p_state text,p_note text,
 p_owner uuid default null,p_supervisor uuid default null,p_due timestamptz default null) returns integer
language plpgsql security definer set search_path='' as $$
declare c public.corrective_actions; allowed boolean;
begin
 if not public.defectrag_ca_staff() then raise insufficient_privilege; end if;
 select * into c from public.corrective_actions where id=p_id for update;
 if not found or not public.defectrag_ca_visible(p_id) or exists(select 1 from public.shared_inspections where id=c.inspection_id and archived_at is not null) then raise insufficient_privilege; end if;
 if p_version is distinct from c.version then raise exception 'Case changed; refresh before updating'; end if;
 if p_note is null or char_length(btrim(p_note)) not between 3 and 2000 then raise exception 'An audit note is required'; end if;
 allowed:=c.state not in ('Closed','Cancelled') and (p_state=c.state or
  (c.state='Open' and p_state='Assigned') or (c.state='Assigned' and p_state='In Progress') or
  (c.state='In Progress' and p_state='Resolved') or (c.state='Resolved' and p_state in ('Closed','In Progress')) or p_state='Cancelled');
 if allowed is distinct from true then raise exception 'Invalid case transition'; end if;
 if p_due is not null and (p_due<=now() or p_due>now()+interval '365 days') then raise exception 'Invalid due date'; end if;
 if not exists(select 1 from public.staff_members where user_id=coalesce(p_owner,c.owner_id) and revoked_at is null)
 or not exists(select 1 from public.staff_members where user_id=coalesce(p_supervisor,c.supervisor_id) and revoked_at is null) then raise exception 'Reassign revoked owner/supervisor before proceeding'; end if;
 update public.corrective_actions set state=p_state,version=version+1,updated_at=now(),
  owner_id=coalesce(p_owner,owner_id),supervisor_id=coalesce(p_supervisor,supervisor_id),due_at=coalesce(p_due,due_at),
  resolved_at=case when p_state='Resolved' then coalesce(resolved_at,now()) when p_state='In Progress' then null else resolved_at end,
  resolution=case when p_state='Resolved' then btrim(p_note) when p_state='In Progress' then null else resolution end,
  closed_at=case when p_state='Closed' then now() else null end where id=p_id;
 insert into public.corrective_action_history(case_id,version,actor_id,state,note,snapshot)
 select p_id,c.version+1,auth.uid(),p_state,btrim(p_note),jsonb_build_object('owner_id',owner_id,'supervisor_id',supervisor_id,'due_at',due_at,'priority',priority,'resolution',resolution)
 from public.corrective_actions where id=p_id;
 insert into public.corrective_action_events(case_id,version,kind) values(p_id,c.version+1,'updated');
 return c.version+1;
end; $$;

-- Service-only scheduled maintenance: reminders are versioned and deduplicated.
create function public.defectrag_ca_schedule() returns integer
language plpgsql security definer set search_path='' as $$
declare total integer;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 if not exists(select 1 from public.corrective_action_settings where automation_enabled) then return 0; end if;
 insert into public.corrective_action_events(case_id,version,kind)
 select c.id,c.version,case when c.due_at<=now() then 'overdue' else 'reminder' end
 from public.corrective_actions c join public.shared_inspections i on i.id=c.inspection_id
 where c.state in ('Open','Assigned','In Progress') and i.archived_at is null and c.due_at<=now()+interval '24 hours'
 on conflict(case_id,version,kind) do nothing;
 get diagnostics total=row_count; return total;
end; $$;

create function public.defectrag_ca_claim() returns jsonb
language plpgsql security definer set search_path='' as $$
declare e public.corrective_action_events; c public.corrective_actions;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 if not exists(select 1 from public.corrective_action_settings where automation_enabled) then return null; end if;
 update public.corrective_action_events x set status='superseded',lease_token=null,lease_until=null
 where x.status in ('queued','sending','dead') and exists(select 1 from public.corrective_actions a
 join public.shared_inspections i on i.id=a.inspection_id where a.id=x.case_id and (a.version<>x.version or i.archived_at is not null));
 update public.corrective_action_events set status='dead',lease_token=null,lease_until=null,last_error='retry_limit'
 where attempts>=8 and (status='queued' or status='sending' and lease_until<now());
 select * into e from public.corrective_action_events where attempts<8 and
 (status='queued' and next_attempt_at<=now() or status='sending' and lease_until<now())
 order by created_at,id limit 1 for update skip locked;
 if not found then return null; end if;
 select * into c from public.corrective_actions where id=e.case_id;
 update public.corrective_action_events set status='sending',attempts=attempts+1,lease_token=gen_random_uuid(),lease_until=now()+interval '5 minutes'
 where id=e.id returning * into e;
 -- Capability is short-lived and event-scoped; no image, JWT or DB key.
 return jsonb_build_object('event_id',e.id,'lease_token',e.lease_token,'case_id',c.id,'kind',e.kind,'version',c.version,
 'state',c.state,'priority',c.priority,'due_at',c.due_at);
end; $$;

create function public.defectrag_ca_effect(p_event uuid,p_lease uuid,p_effect text,p_finish boolean default false,p_receipt text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare e public.corrective_action_events; c public.corrective_actions; effect_row public.corrective_action_effects; recipient text;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 -- Ticket capability intentionally unavailable until a reviewed connector exists.
 if p_effect is distinct from 'notification' then raise exception 'Unsupported effect'; end if;
 select * into e from public.corrective_action_events where id=p_event for update;
 if not found or e.status<>'sending' or e.lease_token is distinct from p_lease or e.lease_until<=now() then raise insufficient_privilege; end if;
 select * into c from public.corrective_actions where id=e.case_id;
 if c.version<>e.version or exists(select 1 from public.shared_inspections where id=c.inspection_id and archived_at is not null)
 or not exists(select 1 from public.corrective_action_settings where automation_enabled) then raise insufficient_privilege; end if;
 select * into effect_row from public.corrective_action_effects where event_id=p_event and effect=p_effect;
 if p_finish then
  if effect_row.state='done' then return jsonb_build_object('done',true); end if;
  if effect_row.state is distinct from 'processing' or p_receipt is null or char_length(p_receipt) not between 1 and 200 then raise exception 'Invalid provider receipt'; end if;
  update public.corrective_action_effects set state='done',receipt=p_receipt,finished_at=now() where event_id=p_event and effect=p_effect;
  return jsonb_build_object('done',true);
 end if;
 if effect_row.state='done' then return jsonb_build_object('done',true,'execute',false); end if;
 if effect_row.state is not null then
  update public.corrective_action_effects set state='uncertain' where event_id=p_event and effect=p_effect;
  return jsonb_build_object('done',false,'execute',false,'manual_review',true);
 end if;
 select u.email into recipient from public.staff_members s join auth.users u on u.id=s.user_id
 where s.user_id=c.supervisor_id and s.revoked_at is null and u.email_confirmed_at is not null;
 if recipient is null then raise exception 'Active verified supervisor required'; end if;
 insert into public.corrective_action_effects(event_id,effect,state) values(p_event,p_effect,'processing');
 return jsonb_build_object('execute',true,'done',false,'recipient_email',recipient,'case_id',c.id,'kind',e.kind,'state',c.state,'priority',c.priority,'due_at',c.due_at);
end; $$;

create function public.defectrag_ca_finish(p_event uuid,p_lease uuid,p_success boolean) returns boolean
language plpgsql security definer set search_path='' as $$
declare e public.corrective_action_events; done boolean; ambiguous boolean;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 select * into e from public.corrective_action_events where id=p_event for update;
 if not found or e.status<>'sending' or e.lease_token is distinct from p_lease or e.lease_until<=now() then return false; end if;
 select exists(select 1 from public.corrective_action_effects where event_id=p_event and effect='notification' and state='done') into done;
 select exists(select 1 from public.corrective_action_effects where event_id=p_event and state in ('processing','uncertain')) into ambiguous;
 update public.corrective_action_events set status=case when p_success and done then 'sent' when ambiguous or attempts>=8 then 'dead' else 'queued' end,
 last_error=case when p_success and done then null when ambiguous then 'effect_ambiguous_manual_review' else 'workflow_unavailable' end,
 next_attempt_at=now()+make_interval(secs=>least(3600,30*power(2,greatest(attempts-1,0)))::integer),lease_token=null,lease_until=null where id=p_event;
 return true;
end; $$;

revoke all on function public.defectrag_ca_staff(),public.defectrag_ca_visible(uuid),public.defectrag_create_corrective_action(text,uuid,boolean,uuid,uuid,text,text,timestamptz),public.defectrag_update_corrective_action(uuid,integer,text,text,uuid,uuid,timestamptz),public.defectrag_ca_schedule(),public.defectrag_ca_claim(),public.defectrag_ca_effect(uuid,uuid,text,boolean,text),public.defectrag_ca_finish(uuid,uuid,boolean) from public,anon,authenticated,service_role;
grant execute on function public.defectrag_ca_staff(),public.defectrag_ca_visible(uuid),public.defectrag_create_corrective_action(text,uuid,boolean,uuid,uuid,text,text,timestamptz),public.defectrag_update_corrective_action(uuid,integer,text,text,uuid,uuid,timestamptz) to authenticated;
grant execute on function public.defectrag_ca_schedule(),public.defectrag_ca_claim(),public.defectrag_ca_effect(uuid,uuid,text,boolean,text),public.defectrag_ca_finish(uuid,uuid,boolean) to service_role;
commit;
