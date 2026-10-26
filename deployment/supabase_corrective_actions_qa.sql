-- REVIEW ONLY. Never run automatically. Global CA automation must remain OFF.
-- Adds a Developer-AAL2-approved, one-event, 15-minute sink-only QA capability.
-- The sole existing function replacement is generated below from the exact
-- reviewed base effect function, extending ONLY its automation gate.
begin;
create table public.corrective_action_qa_runs (
 event_id uuid primary key references public.corrective_action_events(id),
 approved_by uuid not null references auth.users(id), approved_at timestamptz not null default now(),
 expires_at timestamptz not null default now()+interval '15 minutes',
 claimed_at timestamptz, finished_at timestamptz, revoked_at timestamptz, revoked_by uuid references auth.users(id)
);
alter table public.corrective_action_qa_runs enable row level security;
revoke all on public.corrective_action_qa_runs from public,anon,authenticated,service_role;
grant select on public.corrective_action_qa_runs to authenticated;
create policy ca_qa_developer_read on public.corrective_action_qa_runs for select to authenticated
 using(public.defectrag_is_developer() and public.defectrag_has_aal2());

create function public.defectrag_ca_qa_readiness() returns boolean
language plpgsql stable security definer set search_path='' as $$
begin
 if not (public.defectrag_is_developer() and public.defectrag_has_aal2()) then raise insufficient_privilege; end if;
 return not exists(select 1 from public.corrective_action_settings where automation_enabled);
end; $$;

create function public.defectrag_ca_qa_approve(p_event uuid,p_confirm_disposable boolean) returns void
language plpgsql security definer set search_path='' as $$
declare e public.corrective_action_events; c public.corrective_actions;
begin
 if not (public.defectrag_is_developer() and public.defectrag_has_aal2()) then raise insufficient_privilege; end if;
 if p_confirm_disposable is distinct from true then raise exception 'Confirm a disposable QA case explicitly'; end if;
 if exists(select 1 from public.corrective_action_qa_runs where event_id=p_event) then raise exception 'QA event authorization cannot be reset'; end if;
 if exists(select 1 from public.corrective_action_settings where automation_enabled) then raise exception 'Global automation must be OFF'; end if;
 select * into e from public.corrective_action_events where id=p_event for update;
 if not found or e.status<>'queued' or e.attempts<>0 or e.kind not in ('created','updated') then raise exception 'Unused QA event required'; end if;
 select * into c from public.corrective_actions where id=e.case_id for update;
 if c.confirmed_by is distinct from auth.uid() or c.description not like 'QA %' or c.version<>e.version
 or c.state not in ('Open','Assigned','In Progress') or not exists(select 1 from public.shared_inspections where id=c.inspection_id and archived_at is null)
 or exists(select 1 from public.corrective_action_effects where event_id=p_event) then raise exception 'Current active disposable QA case confirmed by this Developer required'; end if;
 insert into public.corrective_action_qa_runs(event_id,approved_by) values(p_event,auth.uid());
 -- Unique event key deliberately prevents resetting/reapproving a consumed run.
end; $$;

create function public.defectrag_ca_qa_revoke(p_event uuid) returns void
language plpgsql security definer set search_path='' as $$
begin
 if not (public.defectrag_is_developer() and public.defectrag_has_aal2()) then raise insufficient_privilege; end if;
 update public.corrective_action_qa_runs set revoked_at=coalesce(revoked_at,now()),revoked_by=coalesce(revoked_by,auth.uid()) where event_id=p_event;
 update public.corrective_action_events set status='dead',lease_token=null,lease_until=null,last_error='qa_revoked_manual_review'
 where id=p_event and status in ('queued','sending') and exists(select 1 from public.corrective_action_qa_runs where event_id=p_event);
end; $$;

create function public.defectrag_ca_qa_authorized(p_event uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.corrective_action_qa_runs q
 join public.staff_members s on s.user_id=q.approved_by
 join auth.users u on u.id=s.user_id
 where q.event_id=p_event and q.expires_at>now() and q.revoked_at is null and q.finished_at is null
 and q.claimed_at is not null and s.role='developer' and s.revoked_at is null and u.email_confirmed_at is not null
 and exists(select 1 from auth.mfa_factors f where f.user_id=s.user_id and f.factor_type='totp' and f.status='verified')
 and not exists(select 1 from public.corrective_action_settings where automation_enabled));
$$;

create function public.defectrag_ca_qa_claim(p_event uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare q public.corrective_action_qa_runs; e public.corrective_action_events; c public.corrective_actions;
begin
 if auth.role() is distinct from 'service_role' then raise insufficient_privilege; end if;
 select * into q from public.corrective_action_qa_runs where event_id=p_event for update;
 if not found or q.claimed_at is not null then raise insufficient_privilege; end if;
 update public.corrective_action_qa_runs set claimed_at=now() where event_id=p_event;
 if not public.defectrag_ca_qa_authorized(p_event) then raise insufficient_privilege; end if;
 select * into e from public.corrective_action_events where id=p_event for update;
 if not found or e.status<>'queued' or e.attempts<>0 or e.next_attempt_at>now()
 or exists(select 1 from public.corrective_action_effects where event_id=p_event) then raise insufficient_privilege; end if;
 select * into c from public.corrective_actions where id=e.case_id for update;
 if c.confirmed_by<>q.approved_by or c.version<>e.version or c.state not in ('Open','Assigned','In Progress')
 or not exists(select 1 from public.shared_inspections where id=c.inspection_id and archived_at is null) then raise insufficient_privilege; end if;
 update public.corrective_action_events set status='sending',attempts=attempts+1,
 lease_token=gen_random_uuid(),lease_until=least(now()+interval '5 minutes',q.expires_at) where id=p_event returning * into e;
 return jsonb_build_object('event_id',e.id,'lease_token',e.lease_token,'case_id',c.id,'kind',e.kind,'version',e.version);
end; $$;

-- QA calls the actual installed production ledger, not a parallel mock ledger.
-- QA notification recipient is permanently redirected to the reserved sink name.
create function public.defectrag_ca_qa_effect(p_event uuid,p_lease uuid,p_finish boolean default false,p_receipt text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r jsonb;
begin
 if auth.role() is distinct from 'service_role' or not public.defectrag_ca_qa_authorized(p_event) then raise insufficient_privilege; end if;
 r:=public.defectrag_ca_effect(p_event,p_lease,'notification',p_finish,p_receipt);
 if r->>'execute'='true' then r:=jsonb_set(r,'{recipient_email}','"supervisor@example.invalid"'::jsonb); end if;
 return r;
end; $$;

create function public.defectrag_ca_qa_finish(p_event uuid,p_lease uuid,p_success boolean) returns boolean
language plpgsql security definer set search_path='' as $$
declare result boolean;
begin
 if auth.role() is distinct from 'service_role' or not public.defectrag_ca_qa_authorized(p_event) then raise insufficient_privilege; end if;
 result:=public.defectrag_ca_finish(p_event,p_lease,p_success);
 if result then
  -- A consumed one-shot QA run must never re-enter the ordinary retry queue.
  update public.corrective_action_events set status='dead',last_error='qa_consumed_no_automatic_replay'
   where id=p_event and status='queued';
  update public.corrective_action_qa_runs set finished_at=now() where event_id=p_event;
 end if;
 return result;
end; $$;

revoke all on function public.defectrag_ca_qa_readiness(),public.defectrag_ca_qa_approve(uuid,boolean),public.defectrag_ca_qa_revoke(uuid),
 public.defectrag_ca_qa_authorized(uuid),public.defectrag_ca_qa_claim(uuid),
 public.defectrag_ca_qa_effect(uuid,uuid,boolean,text),public.defectrag_ca_qa_finish(uuid,uuid,boolean)
 from public,anon,authenticated,service_role;
grant execute on function public.defectrag_ca_qa_readiness(),public.defectrag_ca_qa_approve(uuid,boolean),public.defectrag_ca_qa_revoke(uuid) to authenticated;
grant execute on function public.defectrag_ca_qa_claim(uuid),public.defectrag_ca_qa_effect(uuid,uuid,boolean,text),
 public.defectrag_ca_qa_finish(uuid,uuid,boolean) to service_role;

do $$ begin
 if md5(replace((select prosrc from pg_proc where oid='public.defectrag_ca_effect(uuid,uuid,text,boolean,text)'::regprocedure),E'\r\n',E'\n')) <> '127ba8841692b7f272854a7e9ff67b53' then
 raise exception 'Installed effect function differs from reviewed baseline; stop without replacement'; end if;
end $$;
create or replace function public.defectrag_ca_effect(p_event uuid,p_lease uuid,p_effect text,p_finish boolean default false,p_receipt text default null) returns jsonb
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
 or (not exists(select 1 from public.corrective_action_settings where automation_enabled)
 and not public.defectrag_ca_qa_authorized(p_event)) then raise insufficient_privilege; end if;
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
commit;
