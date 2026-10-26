-- SELECT ONLY. Counts and fingerprints, never payloads, emails, keys or leases.
-- Baseline: leave excluded_qa_case NULL. After the one-event test: substitute
-- ONLY its known case UUID to compare the remaining original rows unchanged.
with scope as (select null::uuid as excluded_qa_case)
select jsonb_build_object(
 'global_automation_off',not exists(select 1 from public.corrective_action_settings where automation_enabled),
 'mfa_required',(select mfa_required from public.defectrag_auth_settings where singleton),
 'qa_runs',(select count(*) from public.corrective_action_qa_runs),
 'synthetic_fixture_id',(select i.id from public.shared_inspections i
   join public.corrective_actions c on c.inspection_id=i.id
   where c.id='7ce36833-4300-4c7f-a3df-b9b8356a0d1d'::uuid
   and i.payload->>'model_id'='QA-SYNTHETIC-NO-INFERENCE' and i.archived_at is null),
 'original_cases',(select jsonb_build_object('count',count(*),
   'fingerprint',md5(coalesce(string_agg(to_jsonb(c)::text,'|' order by c.id),'')))
   from public.corrective_actions c cross join scope s where c.id is distinct from s.excluded_qa_case),
 'original_history',(select jsonb_build_object('count',count(*),
   'fingerprint',md5(coalesce(string_agg(to_jsonb(h)::text,'|' order by h.id),'')))
   from public.corrective_action_history h cross join scope s where h.case_id is distinct from s.excluded_qa_case),
 'original_events',(select jsonb_build_object('count',count(*),
   'fingerprint',md5(coalesce(string_agg(to_jsonb(e)::text,'|' order by e.id),'')))
   from public.corrective_action_events e cross join scope s where e.case_id is distinct from s.excluded_qa_case),
 'original_effects',(select jsonb_build_object('count',count(*),
   'fingerprint',md5(coalesce(string_agg(to_jsonb(f)::text,'|' order by f.event_id,f.effect),'')))
   from public.corrective_action_effects f join public.corrective_action_events e on e.id=f.event_id
   cross join scope s where e.case_id is distinct from s.excluded_qa_case),
 'staff_memberships',(select jsonb_build_object('count',count(*),
   'fingerprint',md5(coalesce(string_agg(to_jsonb(m)::text,'|' order by m.user_id),''))) from public.staff_members m),
 'personal_inspections',(select count(*) from public.personal_inspections),
 'team_inspections',(select count(*) from public.shared_inspections),
 'gallery_entries',(select count(*) from public.defectrag_gallery_entries)
) as single_sink_metadata;
