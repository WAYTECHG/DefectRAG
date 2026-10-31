-- Corrective Action notifications: copy (CC) the person responsible.
-- REVIEW BEFORE RUNNING. Run once, after supabase_corrective_actions.sql and
-- supabase_corrective_actions_qa.sql. Replaces two function bodies only:
-- no table, policy, grant, setting or data change, and it does not turn on
-- automation. CREATE OR REPLACE keeps the existing function privileges.
--
-- One notification effect, one SMTP message: To the verified supervisor, CC the
-- person responsible when that is a different, active, email-verified Staff
-- member. The existing one-effect/one-receipt exactly-once ledger is unchanged.
-- QA keeps its single fixed synthetic envelope: the QA wrapper removes cc_email.
-- Rollback: corrective_actions_owner_cc_rollback_REVIEW_ONLY.sql
begin;
do $$ begin
 if md5(replace((select prosrc from pg_proc where oid='public.defectrag_ca_effect(uuid,uuid,text,boolean,text)'::regprocedure),E'\r\n',E'\n')) <> '3db8dc902488441eb3a7b946a21e1289' then
  raise exception 'Installed effect function differs from the reviewed QA baseline; stop without replacement'; end if;
 if md5(replace((select prosrc from pg_proc where oid='public.defectrag_ca_qa_effect(uuid,uuid,boolean,text)'::regprocedure),E'\r\n',E'\n')) <> '4339748ee679b0409cbaca7398c91f0d' then
  raise exception 'Installed QA effect wrapper differs from the reviewed baseline; stop without replacement'; end if;
end $$;

create or replace function public.defectrag_ca_effect(p_event uuid,p_lease uuid,p_effect text,p_finish boolean default false,p_receipt text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare e public.corrective_action_events; c public.corrective_actions; effect_row public.corrective_action_effects; recipient text; copy_to text;
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
 -- Optional copy: never blocks the supervisor notification when unavailable.
 select u.email into copy_to from public.staff_members s join auth.users u on u.id=s.user_id
 where s.user_id=c.owner_id and c.owner_id is distinct from c.supervisor_id and s.revoked_at is null
 and u.email_confirmed_at is not null and lower(u.email)<>lower(recipient);
 insert into public.corrective_action_effects(event_id,effect,state) values(p_event,p_effect,'processing');
 return jsonb_build_object('execute',true,'done',false,'recipient_email',recipient,'cc_email',copy_to,'case_id',c.id,'kind',e.kind,'state',c.state,'priority',c.priority,'due_at',c.due_at);
end; $$;

-- QA notification recipient is permanently redirected to the reserved sink name,
-- and QA never carries a copy address.
create or replace function public.defectrag_ca_qa_effect(p_event uuid,p_lease uuid,p_finish boolean default false,p_receipt text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r jsonb;
begin
 if auth.role() is distinct from 'service_role' or not public.defectrag_ca_qa_authorized(p_event) then raise insufficient_privilege; end if;
 r:=public.defectrag_ca_effect(p_event,p_lease,'notification',p_finish,p_receipt);
 if r->>'execute'='true' then r:=jsonb_set(r,'{recipient_email}','"supervisor@example.invalid"'::jsonb); end if;
 return r-'cc_email';
end; $$;
commit;
