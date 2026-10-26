-- SELECT ONLY. Dedicated disposable case; no row payloads, recipients or leases.
-- Run after the native live QA lifecycle; never claims events or activates delivery.
with qa as (
 select * from public.corrective_actions
 where id='7ce36833-4300-4c7f-a3df-b9b8356a0d1d'::uuid
)
select jsonb_build_object(
 'case_count',(select count(*) from qa),
 'automation_enabled',(select automation_enabled from public.corrective_action_settings where singleton),
 'case',(select jsonb_build_object('id',id,'state',state,'version',version,
   'resolved',resolved_at is not null,'closed',closed_at is not null,
   'owner_matches_supervisor',owner_id=supervisor_id) from qa),
 'audit',(select jsonb_build_object('rows',count(*),'distinct_versions',count(distinct h.version),
   'first_version',min(h.version),'last_version',max(h.version),
   'actors',count(distinct h.actor_id))
   from public.corrective_action_history h join qa q on q.id=h.case_id),
 'events',(select jsonb_build_object('rows',count(*),'attempts',coalesce(sum(e.attempts),0),
   'all_queued',coalesce(bool_and(e.status='queued'),false))
   from public.corrective_action_events e join qa q on q.id=e.case_id),
 'effects',(select count(*) from public.corrective_action_effects f
   join public.corrective_action_events e on e.id=f.event_id join qa q on q.id=e.case_id),
 'qa_records',jsonb_build_object(
   'personal',(select count(*) from public.personal_inspections i join qa q on q.inspection_id=i.id),
   'team',(select count(*) from public.shared_inspections i join qa q on q.inspection_id=i.id),
   'personal_notes',(select count(*) from public.personal_notes n join qa q on q.inspection_id=n.inspection_id),
   'team_notes',(select count(*) from public.staff_notes n join qa q on q.inspection_id=n.inspection_id),
   'private_objects',(select count(*) from storage.objects o join qa q on split_part(o.name,'/',2)=q.inspection_id where o.bucket_id='personal-inspections'),
   'team_objects',(select count(*) from storage.objects o join qa q on split_part(o.name,'/',2)=q.inspection_id where o.bucket_id='team-inspections')),
 'non_qa_counts',jsonb_build_object(
   'personal',(select count(*) from public.personal_inspections i where not exists(select 1 from qa q where q.inspection_id=i.id)),
   'team',(select count(*) from public.shared_inspections i where not exists(select 1 from qa q where q.inspection_id=i.id)),
   'personal_notes',(select count(*) from public.personal_notes n where not exists(select 1 from qa q where q.inspection_id=n.inspection_id)),
   'team_notes',(select count(*) from public.staff_notes n where not exists(select 1 from qa q where q.inspection_id=n.inspection_id)),
   'gallery',(select count(*) from public.defectrag_gallery_entries),
   'staff',(select count(*) from public.staff_members),
   'pending_requests',(select count(*) from public.staff_access_requests where status='pending'))
) as corrective_live_qa_check;
