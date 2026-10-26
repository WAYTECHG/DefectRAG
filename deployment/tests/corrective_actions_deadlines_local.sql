-- ISOLATED PostgreSQL fixture ONLY. No production connection or external effects.
begin;
insert into auth.users(id,email,email_confirmed_at) values('daaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','deadline@example.invalid',now());
insert into public.staff_members(user_id,display_name,role) values('daaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','Offline deadline QA','developer');
insert into auth.mfa_factors(id,user_id,factor_type,status,secret) values(gen_random_uuid(),'daaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','totp','verified','FAKE_LOCAL_ONLY');
create temporary table deadline_cases(name text primary key,id uuid);
select set_config('request.jwt.claims','{"role":"authenticated","sub":"daaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
do $$ declare label text; inspection text; review uuid; case_id uuid; due timestamptz;
begin
 foreach label in array array['far','window','near','overdue','resolved','closed','cancelled','archived'] loop
  inspection:=md5('DEADLINE_FIXTURE_'||label);review:=gen_random_uuid();
  insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path)
   values(inspection,auth.uid(),'{}','fixture/image.jpg','fixture/heatmap.jpg');
  insert into public.staff_notes(id,inspection_id,author_id,body) values(review,inspection,auth.uid(),
   'DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject","note":"Offline synthetic deadline check"}');
  due:=now()+case label when 'far' then interval '25 hours' when 'window' then interval '24 hours' else interval '1 hour' end;
  case_id:=public.defectrag_create_corrective_action(inspection,review,true,auth.uid(),auth.uid(),'Normal','QA offline deadline fixture',due);
  insert into deadline_cases values(label,case_id);
  if label in ('resolved','closed') then
   perform public.defectrag_update_corrective_action(case_id,1,'Assigned','QA assigned');
   perform public.defectrag_update_corrective_action(case_id,2,'In Progress','QA started');
   perform public.defectrag_update_corrective_action(case_id,3,'Resolved','QA verified resolution');
   if label='closed' then perform public.defectrag_update_corrective_action(case_id,4,'Closed','QA closed');end if;
  elsif label='cancelled' then perform public.defectrag_update_corrective_action(case_id,1,'Cancelled','QA cancelled');
  elsif label='overdue' then update public.corrective_actions set due_at=now()-interval '1 second' where id=case_id;
  elsif label='archived' then update public.shared_inspections set archived_at=now() where id=inspection;
  end if;
 end loop;
end $$;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
do $$ begin if public.defectrag_ca_schedule()<>0 then raise exception 'Disabled scheduler wrote events';end if;end $$;
reset role;
update public.corrective_action_settings set automation_enabled=true;
set local role service_role;
do $$ begin
 if public.defectrag_ca_schedule()<>3 then raise exception 'Deadline window/terminal filtering failed';end if;
 if public.defectrag_ca_schedule()<>0 then raise exception 'Same-version deadline duplicate';end if;
end $$;
reset role;
do $$ begin
 if (select count(*) from public.corrective_action_events where kind='reminder')<>2
 or (select count(*) from public.corrective_action_events where kind='overdue')<>1
 or exists(select 1 from public.corrective_action_events e join deadline_cases c on c.id=e.case_id
   where c.name in ('far','resolved','closed','cancelled','archived') and e.kind in ('reminder','overdue')) then
  raise exception 'Unexpected reminder or escalation recipient case';end if;
end $$;
-- Advance only fixture time to test exact due boundary without waiting an hour.
update public.corrective_actions set due_at=now() where id=(select id from deadline_cases where name='near');
set local role service_role;
do $$ begin
 if public.defectrag_ca_schedule()<>1 or public.defectrag_ca_schedule()<>0 then raise exception 'Overdue boundary/dedup failed';end if;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"daaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
select public.defectrag_update_corrective_action((select id from deadline_cases where name='near'),1,'Assigned','QA new version');
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
do $$ begin if public.defectrag_ca_schedule()<>1 or public.defectrag_ca_schedule()<>0 then raise exception 'New version/dedup failed';end if;end $$;
reset role;
update public.corrective_action_settings set automation_enabled=false;
set local role service_role;
do $$ begin if public.defectrag_ca_schedule()<>0 then raise exception 'Pause gate bypass';end if;end $$;
reset role;
rollback;
select 'deadline window, boundary, version dedup, resolved/closed/cancelled/archive exclusion and pause: PASS' as result;
