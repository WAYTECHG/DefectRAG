-- Corrective Action notifications: send immediately after a person creates or
-- updates a case ("doorbell"), instead of waiting for the next timer check.
-- REVIEW BEFORE RUNNING. Run once, after supabase_corrective_actions_owner_cc.sql.
--
-- Adds one trigger function and one row trigger on corrective_action_events.
-- No table, policy, grant, setting or data change. The trigger only asks the
-- existing corrective-actions Edge Function to dispatch; the existing queue,
-- lease and one-effect ledger still decide what is sent, exactly once.
-- Reminders/overdue stay with the timer, which also retries anything missed.
-- Never blocks saving a case: every failure is swallowed and left to the timer.
-- Requires Vault secret 'defectrag_ca_worker_bearer' = DEFECTRAG_CA_WORKER_SECRET
-- (without "Bearer"); until it exists the trigger does nothing.
-- Rollback: corrective_actions_instant_rollback_REVIEW_ONLY.sql
begin;
set local lock_timeout='5s';
do $$ begin
 if to_regclass('vault.decrypted_secrets') is null
 or to_regprocedure('net.http_post(text,jsonb,jsonb,jsonb,integer)') is null
 or to_regclass('public.corrective_action_events') is null
 then raise exception 'STOP: Vault, pg_net or Corrective Actions missing'; end if;
 if to_regprocedure('public.defectrag_ca_ring()') is not null
 or exists(select 1 from pg_trigger where tgname='defectrag_ca_ring_on_event' and not tgisinternal)
 then raise exception 'STOP: doorbell already installed; inspect instead of replacing'; end if;
end $$;

create function public.defectrag_ca_ring() returns trigger
language plpgsql security definer set search_path='' as $$
declare bearer text;
begin
 if new.kind not in ('created','updated') or new.status<>'queued'
 or not exists(select 1 from public.corrective_action_settings where automation_enabled) then return null; end if;
 begin
  -- The value is used internally only; never output or log it.
  select decrypted_secret into bearer from vault.decrypted_secrets where name='defectrag_ca_worker_bearer';
  if bearer is null or length(bearer)<32 then return null; end if;
  -- pg_net sends only after this transaction commits, so the event is visible.
  perform net.http_post(
   url:='https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/corrective-actions',
   body:='{}'::jsonb,
   params:='{}'::jsonb,
   headers:=jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||bearer),
   timeout_milliseconds:=110000);
 exception when others then
  -- Saving the case matters more than speed; the timer delivers it instead.
  return null;
 end;
 return null;
end; $$;
revoke all on function public.defectrag_ca_ring() from public,anon,authenticated,service_role;

create trigger defectrag_ca_ring_on_event after insert on public.corrective_action_events
 for each row execute function public.defectrag_ca_ring();
commit;
