-- REVIEW ONLY: disable the QA Edge gate first; restore only reviewed original effect gate.
-- Retains all QA audit/event/effect rows. No deletion, no original role grant changes.
begin;
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
commit;
