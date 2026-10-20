-- LOCAL ISOLATED SUPABASE ONLY. NOT RUN by this implementation.
-- Requires base/workspace/auth + new corrective-actions migrations in a LOCAL DB.
-- Run with psql ON_ERROR_STOP=1. All synthetic fixtures roll back.
-- Claims/factors are fixtures: this tests DB authorization, NOT real TOTP login.
begin;
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
do $$ begin if public.defectrag_ca_staff() then raise exception 'AAL1 qualified'; end if; end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
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
update public.corrective_action_settings set automation_enabled=true;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select set_config('test.ca_event',public.defectrag_ca_claim()::text,true);
do $$ declare e jsonb:=current_setting('test.ca_event')::jsonb; r jsonb; begin
 if (e->>'version')::integer<>2 then raise exception 'Obsolete event not superseded'; end if;
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
update public.staff_members set revoked_at=now() where user_id='caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
select set_config('request.jwt.claims','{"role":"authenticated","sub":"caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
do $$ begin
 if public.defectrag_ca_staff() then raise exception 'Revoked user retained privilege'; end if;
 if exists(select 1 from public.corrective_actions) then raise exception 'Revoked user can read cases'; end if;
end $$;
reset role;
rollback;
