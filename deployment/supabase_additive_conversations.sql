-- REVIEW REQUIRED before execution. Additive functions only.
-- Existing staff policies, grants on tables, accounts and measurements remain.
-- No DELETE, DROP, table UPDATE grant, signup policy or service-role credential.
-- Reuse existing shared_inspections.conversation JSONB and payload JSONB fields.
begin;

create or replace function public.defectrag_append_conversation(
  p_id text, p_question text, p_answer jsonb
) returns integer
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_is_staff() then
    raise exception 'Approved staff access required';
  end if;
  if p_id is null or p_question is null or p_answer is null
     or p_id !~ '^[a-f0-9]{32}$' or char_length(p_question) not between 3 and 1200
     or jsonb_typeof(p_answer) <> 'object' or octet_length(p_answer::text) > 40000 then
    raise exception 'Invalid bounded conversation payload';
  end if;
  -- Atomic append avoids losing another staff member's simultaneous conversation.
  update public.shared_inspections
    set conversation=conversation || jsonb_build_array(
      jsonb_build_object('role','user','question',p_question,'created_at',now(),'actor_id',auth.uid()),
      p_answer || jsonb_build_object('role','assistant','created_at',now(),'actor_id',auth.uid()))
    where id=p_id and archived_at is null;
  get diagnostics changed=row_count;
  if changed=0 then raise exception 'Active staff inspection not found'; end if;
  return changed;
end;
$$;

create or replace function public.defectrag_acknowledge_review(p_id text)
returns integer
language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
  if not public.defectrag_is_staff() or p_id is null or p_id !~ '^[a-f0-9]{32}$' then
    raise exception 'Approved staff access and a valid inspection required';
  end if;
  update public.shared_inspections
    set payload=jsonb_set(payload,'{alert_acknowledged}','true'::jsonb,true)
    where id=p_id and archived_at is null;
  get diagnostics changed=row_count;
  return changed;
end;
$$;

revoke all on function public.defectrag_append_conversation(text,text,jsonb) from public,anon;
revoke all on function public.defectrag_acknowledge_review(text) from public,anon;
grant execute on function public.defectrag_append_conversation(text,text,jsonb) to authenticated;
grant execute on function public.defectrag_acknowledge_review(text) to authenticated;
commit;
