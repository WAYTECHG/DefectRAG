-- LOCAL ISOLATED DATABASE ONLY. Run using run_corrective_actions_sql.py.
-- Requires base/workspace/auth + new corrective-actions migrations in a LOCAL DB.
-- Run with psql ON_ERROR_STOP=1. All synthetic fixtures roll back.
-- Claims/factors are fixtures: this tests DB authorization, NOT real TOTP login.
begin;
do $$ begin
 if has_function_privilege('anon','public.defectrag_create_corrective_action(text,uuid,boolean,uuid,uuid,text,text,timestamptz)','EXECUTE')
 or has_function_privilege('authenticated','public.defectrag_ca_claim()','EXECUTE')
 or has_function_privilege('authenticated','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE')
 or not has_function_privilege('service_role','public.defectrag_ca_claim()','EXECUTE')
 or has_table_privilege('authenticated','public.corrective_actions','INSERT')
 or has_table_privilege('authenticated','public.corrective_actions','UPDATE')
 or has_table_privilege('authenticated','public.corrective_actions','DELETE') then raise exception 'Corrective-action ACL mismatch'; end if;
end $$;
insert into auth.users(id,aud,role,email,email_confirmed_at,raw_app_meta_data,raw_user_meta_data) values
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','authenticated','authenticated','ca-dev@example.invalid',now(),'{}','{}'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','authenticated','authenticated','ca-staff@example.invalid',now(),'{}','{}'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','authenticated','authenticated','ca-pending@example.invalid',now(),'{}','{}');
insert into public.staff_members(user_id,display_name,role) values
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','CA fixture developer','developer'),
 ('caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','CA fixture staff','staff');
insert into auth.mfa_factors(id,user_id,factor_type,status,secret) values
 ('cbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','totp','verified','LOCAL_FIXTURE_NOT_A_REAL_SECRET'),
 ('cbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','totp','verified','LOCAL_FIXTURE_NOT_A_REAL_SECRET');
insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path) values
 ('cccccccccccccccccccccccccccccccc','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','{"id":"cccccccccccccccccccccccccccccccc","verdict":"Anomalous"}',
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2/cccccccccccccccccccccccccccccccc/image.jpg','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2/cccccccccccccccccccccccccccccccc/heatmap.jpg');
insert into public.staff_notes(id,inspection_id,author_id,body) values
 ('cddddddd-dddd-4ddd-8ddd-ddddddddddd1','cccccccccccccccccccccccccccccccc','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2',
 'DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject","note":"Local human review fixture"}');

set local role anon;
do $$ begin
 begin perform 1 from public.corrective_actions; raise exception 'Anonymous read unexpectedly allowed';
 exception when insufficient_privilege then null; end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3","aal":"aal2"}',true);
set local role authenticated;
do $$ begin
 if public.defectrag_ca_staff() then raise exception 'Pending account qualified'; end if;
 begin perform public.defectrag_create_corrective_action('cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',true,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High','Local fixture defect',now()+interval '2 hours');
 raise exception 'Pending write unexpectedly allowed'; exception when insufficient_privilege then null; end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal1"}',true);
set local role authenticated;
do $$ begin
 if public.defectrag_ca_staff() then raise exception 'AAL1 qualified'; end if;
 begin perform public.defectrag_create_corrective_action('cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',true,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High','Local fixture defect',now()+interval '2 hours');
 raise exception 'AAL1 write allowed'; exception when insufficient_privilege then null; end;
end $$;
reset role;
-- A forged AAL2 fixture claim without a verified factor is still insufficient.
update auth.mfa_factors set status='unverified' where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
do $$ begin if public.defectrag_ca_staff() then raise exception 'Unverified factor qualified'; end if; end $$;
reset role;
update auth.mfa_factors set status='verified' where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
set local role authenticated;
do $$ begin
 begin perform public.defectrag_create_corrective_action('cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',false,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High','Local fixture defect',now()+interval '2 hours');
 raise exception 'Missing explicit confirmation allowed'; exception when others then if sqlerrm not like 'Explicit human%' then raise; end if; end;
end $$;
select set_config('test.ca_id',public.defectrag_create_corrective_action('cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',true,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High','Local fixture defect',now()+interval '2 hours')::text,true);
do $$ begin
 begin perform public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,1,'Closed','Invalid direct close');
 raise exception 'Invalid transition allowed'; exception when others then if sqlerrm not like 'Invalid case transition%' then raise; end if; end;
end $$;
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,1,'Assigned','Assign fixture case');
do $$ begin
 begin perform public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,1,'In Progress','Stale version update');
 raise exception 'Stale version allowed'; exception when others then if sqlerrm not like 'Case changed%' then raise; end if; end;
 if (select count(*) from public.corrective_action_history where case_id=current_setting('test.ca_id')::uuid)<>2 then raise exception 'History missing'; end if;
 begin perform lease_token from public.corrective_action_events; raise exception 'Browser can read delivery capability'; exception when insufficient_privilege then null; end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3","aal":"aal2"}',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.corrective_actions) or exists(select 1 from public.corrective_action_history) then raise exception 'Pending account sees existing cases'; end if;
 begin perform public.defectrag_ca_claim(); raise exception 'Browser acquired worker lease'; exception when insufficient_privilege then null; end;
end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal1"}',true);
set local role authenticated;
do $$ begin if exists(select 1 from public.corrective_actions) then raise exception 'AAL1 sees existing cases'; end if; end $$;
reset role;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
do $$ begin if public.defectrag_ca_claim() is not null or public.defectrag_ca_schedule()<>0 then raise exception 'Disabled automation gate bypass'; end if; end $$;
reset role;
update public.corrective_action_settings set automation_enabled=true;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select set_config('test.ca_event',public.defectrag_ca_claim()::text,true);
do $$ declare e jsonb:=current_setting('test.ca_event')::jsonb; r jsonb; begin
 if (e->>'version')::integer<>2 then raise exception 'Obsolete event not superseded'; end if;
 begin perform public.defectrag_ca_effect((e->>'event_id')::uuid,gen_random_uuid(),'notification');
 raise exception 'Wrong capability allowed'; exception when insufficient_privilege then null; end;
 begin perform public.defectrag_ca_effect((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'ticket');
 raise exception 'Unimplemented ticket allowed'; exception when others then if sqlerrm not like 'Unsupported effect%' then raise; end if; end;
 r:=public.defectrag_ca_effect((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'notification');
 if r->>'execute'<>'true' then raise exception 'First effect not reserved'; end if;
 perform public.defectrag_ca_effect((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'notification',true,'fixture-provider-id');
 r:=public.defectrag_ca_effect((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'notification');
 if r->>'done'<>'true' or r->>'execute'<>'false' then raise exception 'Completed effect replay'; end if;
 if not public.defectrag_ca_finish((e->>'event_id')::uuid,(e->>'lease_token')::uuid,true) then raise exception 'Acknowledgment lost'; end if;
 if public.defectrag_ca_claim() is not null then raise exception 'Acknowledged event claimed again'; end if;
 if public.defectrag_ca_schedule()<>1 or public.defectrag_ca_schedule()<>0 then raise exception 'Reminder dedup failed'; end if;
end $$;
reset role;
-- Expired capabilities cannot retrieve a recipient or record an effect receipt.
update public.corrective_action_events set status='sending',lease_token=gen_random_uuid(),lease_until=now()-interval '1 second'
where id=(select id from public.corrective_action_events where kind='reminder' limit 1);
select set_config('test.expired_event',(select jsonb_build_object('event_id',id,'lease_token',lease_token)::text from public.corrective_action_events where kind='reminder' limit 1),true);
set local role service_role;
do $$ declare e jsonb:=current_setting('test.expired_event')::jsonb; begin
 begin perform public.defectrag_ca_effect((e->>'event_id')::uuid,(e->>'lease_token')::uuid,'notification');
 raise exception 'Expired capability allowed'; exception when insufficient_privilege then null; end;
 if public.defectrag_ca_finish((e->>'event_id')::uuid,(e->>'lease_token')::uuid,true) then raise exception 'Expired acknowledgment allowed'; end if;
end $$;
reset role;
-- Audit progression, reopening and terminal-state rejection.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,2,'In Progress','Start corrective work');
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,3,'Resolved','Human verified fixture correction');
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,4,'In Progress','Reopen fixture correction');
do $$ begin
 if exists(select 1 from public.corrective_actions where id=current_setting('test.ca_id')::uuid and (resolved_at is not null or resolution is not null)) then raise exception 'Reopen retained resolution'; end if;
end $$;
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,5,'Resolved','Correction verified a second time');
select public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,6,'Closed','Close verified correction');
do $$ begin
 begin perform public.defectrag_update_corrective_action(current_setting('test.ca_id')::uuid,7,'Open','Attempt terminal replay');
 raise exception 'Terminal state reopened'; exception when others then if sqlerrm not like 'Invalid case transition%' then raise; end if; end;
 if (select count(*) from public.corrective_action_history where case_id=current_setting('test.ca_id')::uuid)<>7 then raise exception 'Immutable history incomplete'; end if;
 begin perform public.defectrag_create_corrective_action('cccccccccccccccccccccccccccccccc','cddddddd-dddd-4ddd-8ddd-ddddddddddd1',true,
 'caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High','Duplicate local fixture',now()+interval '2 hours');
 raise exception 'Duplicate case accepted'; exception when unique_violation then null; end;
end $$;
reset role;
update public.staff_members set revoked_at=now() where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
do $$ begin
 if public.defectrag_ca_staff() then raise exception 'Revoked user retained privilege'; end if;
 if exists(select 1 from public.corrective_actions) then raise exception 'Revoked user can read cases'; end if;
end $$;
reset role;
rollback;
select 'corrective-action ACL/MFA/review/CAS/lifecycle/audit/lease/effect/reminder contracts passed' as result;
