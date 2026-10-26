-- OFFLINE DISPOSABLE DATABASE ONLY. Synthetic claims, no native login or mail.
-- Run after corrective_actions_local.sql; every fixture/helper rolls back.
begin;
create function public.qa_ca_update_denied(p_id uuid,p_version integer,p_state text,
 p_owner uuid default null,p_supervisor uuid default null) returns void
language plpgsql as $$ begin
 begin
  perform public.defectrag_update_corrective_action(p_id,p_version,p_state,
   'Unauthorized fixture edit',p_owner,p_supervisor);
 exception when insufficient_privilege then return; end;
 raise exception 'Unauthorized case update unexpectedly allowed';
end $$;

insert into auth.users(id,aud,role,email,email_confirmed_at,raw_app_meta_data,raw_user_meta_data)
select ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa'||n)::uuid,'authenticated','authenticated',
 'ca-editor-'||n||'@example.invalid',now(),'{}','{}' from generate_series(1,5) n;
insert into public.staff_members(user_id,display_name,role) values
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','Developer','developer'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','Owner','staff'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4','Supervisor','staff'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5','Other staff / creator','staff');
insert into auth.mfa_factors(id,user_id,factor_type,status,secret)
select gen_random_uuid(),user_id,'totp','verified','OFFLINE_FIXTURE_ONLY' from public.staff_members;
insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path) values
 ('cccccccccccccccccccccccccccccccc','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','{"id":"cccccccccccccccccccccccccccccccc"}',
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2/cccccccccccccccccccccccccccccccc/image.jpg',
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2/cccccccccccccccccccccccccccccccc/heatmap.jpg');
insert into public.staff_notes(id,inspection_id,author_id,body) values
 ('cddddddd-dddd-4ddd-8ddd-ddddddddddd1','cccccccccccccccccccccccccccccccc','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2',
 'DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject","note":"Human review fixture"}');

-- An unassigned creator may create/read a Team case, but cannot edit or self-assign it.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5","aal":"aal2"}',true);
set local role authenticated;
select set_config('test.edit_case',public.defectrag_create_corrective_action(
 'cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',true,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4',
 'High','Editor authorization fixture',now()+interval '2 hours')::text,true);
do $$ begin
 if not exists(select 1 from public.corrective_actions where id=current_setting('test.edit_case')::uuid) then raise exception 'Team read unexpectedly restricted'; end if;
 perform public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,1,'Open');
 perform public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,1,'Open',auth.uid(),auth.uid());
 if (select version from public.corrective_actions where id=current_setting('test.edit_case')::uuid)<>1 then raise exception 'Denied updates changed case'; end if;
end $$;
reset role;

-- Owner, non-Developer supervisor and an unassigned Developer all have positive tests.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,1,'Assigned','Owner assigned work');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,2,'In Progress','Supervisor started work');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,3,'In Progress','Unassigned Developer oversight');
reset role;

-- A valid supervisor can transfer responsibility. Persisted new assignments apply immediately.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,4,'In Progress','Transfer case responsibility',
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1');
select public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,5,'In Progress',null,auth.uid());
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
select public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,5,'In Progress',auth.uid());
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,5,'Resolved','New owner verified correction');
reset role;

-- Revocation overrides assignment; Developer status never bypasses native MFA.
update public.staff_members set revoked_at=now() where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5';
set local role authenticated;
select public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,6,'Closed');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal1"}',true);
set local role authenticated;
select public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,6,'Closed');
reset role;
update auth.mfa_factors set status='unverified' where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
select public.qa_ca_update_denied(current_setting('test.edit_case')::uuid,6,'Closed');
reset role;
update auth.mfa_factors set status='verified' where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.edit_case')::uuid,6,'Closed','Developer reassigned revoked owner and closed',
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2');
do $$ begin
 if (select count(*) from public.corrective_action_history where case_id=current_setting('test.edit_case')::uuid)<>7
 or (select count(*) from public.corrective_action_events where case_id=current_setting('test.edit_case')::uuid)<>7
 then raise exception 'Unauthorized attempt changed audit/event count'; end if;
 if (select actor_id from public.corrective_action_history where case_id=current_setting('test.edit_case')::uuid and version=3)<>'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4'::uuid
 or (select actor_id from public.corrective_action_history where case_id=current_setting('test.edit_case')::uuid and version=4)<>'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'::uuid
 then raise exception 'Supervisor/Developer audit actor mismatch'; end if;
end $$;
reset role;
rollback;
select 'owner/supervisor/Developer editor, self-assignment, transfer, revocation and MFA contracts passed' as result;
