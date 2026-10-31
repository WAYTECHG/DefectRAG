-- REVIEW ONLY: removes the Corrective Action "doorbell". Emails then go out on
-- the timer alone, as before. Leaves the Vault secret for a separate decision.
begin;
drop trigger if exists defectrag_ca_ring_on_event on public.corrective_action_events;
drop function if exists public.defectrag_ca_ring();
commit;
