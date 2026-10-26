-- OFFLINE ONLY. Synthetic JWT/factor fixtures, NOT native Supabase login.
begin;
create function public.qa_expect_denied(sql text) returns void language plpgsql as $$
begin execute sql; raise exception 'Unexpected authorization success'; exception when insufficient_privilege then null; end; $$;
insert into auth.users(id,email,email_confirmed_at) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','dev@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','staff@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','pending@example.invalid',now());
insert into public.staff_members(user_id,display_name,role) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','QA Developer','developer'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','QA Staff','staff');
insert into auth.mfa_factors(id,user_id,factor_type,status) select gen_random_uuid(),user_id,'totp','verified' from public.staff_members;
insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path) values
 ('dddddddddddddddddddddddddddddddd','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','{}','fixture/image.jpg','fixture/heatmap.jpg');
insert into public.staff_notes(id,inspection_id,author_id,body)
 select ('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,'dddddddddddddddddddddddddddddddd',
 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject"}' from generate_series(1,5) n;
insert into public.corrective_actions(id,inspection_id,review_id,reviewer_id,review_snapshot,confirmed_by,owner_id,supervisor_id,priority,description,due_at)
 select ('cccccccc-cccc-4ccc-8ccc-'||lpad(n::text,12,'0'))::uuid,'dddddddddddddddddddddddddddddddd',
 ('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','QA human review',
 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2',
 'High','QA disposable offline case',now()+interval '2 hours' from generate_series(1,5) n;
insert into public.corrective_action_events(id,case_id,version,kind)
 select ('eeeeeeee-eeee-4eee-8eee-'||lpad(n::text,12,'0'))::uuid,('cccccccc-cccc-4ccc-8ccc-'||lpad(n::text,12,'0'))::uuid,1,'created' from generate_series(1,5) n;
select set_config('test.qa_event','eeeeeeee-eeee-4eee-8eee-000000000001',true);
select set_config('test.other_before',(select md5(jsonb_agg(to_jsonb(e) order by id)::text) from public.corrective_action_events e where id<>current_setting('test.qa_event')::uuid),true);

do $$ begin
 if has_function_privilege('authenticated','public.defectrag_ca_qa_claim(uuid)','EXECUTE')
 or has_function_privilege('anon','public.defectrag_ca_qa_approve(uuid,boolean)','EXECUTE')
 or has_table_privilege('service_role','public.corrective_action_qa_runs','SELECT')
 or has_table_privilege('authenticated','public.corrective_action_qa_runs','UPDATE') then raise exception 'QA ACL mismatch'; end if;
end $$;
set local role anon;
select public.qa_expect_denied('select public.defectrag_ca_qa_approve(''eeeeeeee-eeee-4eee-8eee-000000000001'',true)');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
select public.qa_expect_denied('select public.defectrag_ca_qa_readiness()');
select public.qa_expect_denied('select public.defectrag_ca_qa_approve(''eeeeeeee-eeee-4eee-8eee-000000000001'',true)');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal1"}',true);
set local role authenticated;
select public.qa_expect_denied('select public.defectrag_ca_qa_approve(''eeeeeeee-eeee-4eee-8eee-000000000001'',true)');
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
do $$ begin if not public.defectrag_ca_qa_readiness() then raise exception 'Developer readiness must see global gate OFF'; end if; end $$;
select public.defectrag_ca_qa_approve(current_setting('test.qa_event')::uuid,true);
reset role;

-- Revoked Developer and missing current verified factor invalidate the grant.
update public.staff_members set revoked_at=now() where role='developer';
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000001'')');
reset role;
update public.staff_members set revoked_at=null where role='developer';
update auth.mfa_factors set status='unverified' where user_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';
set local role service_role;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000001'')');
reset role;
update auth.mfa_factors set status='verified' where user_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';
update public.corrective_action_qa_runs set expires_at=now()-interval '1 second';
set local role service_role;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000001'')');
reset role;
update public.corrective_action_qa_runs set expires_at=now()+interval '15 minutes';
set local role service_role;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000002'')');
select set_config('test.qa_lease',public.defectrag_ca_qa_claim(current_setting('test.qa_event')::uuid)->>'lease_token',true);
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000001'')');
select public.qa_expect_denied('select public.defectrag_ca_qa_effect(''eeeeeeee-eeee-4eee-8eee-000000000001'',''ffffffff-ffff-4fff-8fff-ffffffffffff'',false,null)');
do $$ declare r jsonb; begin
 if public.defectrag_ca_claim() is not null or public.defectrag_ca_schedule()<>0 then raise exception 'Global gate changed'; end if;
 r:=public.defectrag_ca_qa_effect(current_setting('test.qa_event')::uuid,current_setting('test.qa_lease')::uuid,false,null);
 if r->>'recipient_email'<>'supervisor@example.invalid' or r->>'execute'<>'true' then raise exception 'Sink projection mismatch'; end if;
 perform public.defectrag_ca_qa_effect(current_setting('test.qa_event')::uuid,current_setting('test.qa_lease')::uuid,true,'<qa-local-sink@example.invalid>');
 r:=public.defectrag_ca_qa_effect(current_setting('test.qa_event')::uuid,current_setting('test.qa_lease')::uuid,false,null);
 if r->>'execute'<>'false' or r->>'done'<>'true' then raise exception 'Duplicate suppression failed'; end if;
 if not public.defectrag_ca_qa_finish(current_setting('test.qa_event')::uuid,current_setting('test.qa_lease')::uuid,true) then raise exception 'Authoritative finish failed'; end if;
end $$;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000001'')');
reset role;
do $$ begin
 if (select md5(jsonb_agg(to_jsonb(e) order by id)::text) from public.corrective_action_events e where id<>current_setting('test.qa_event')::uuid)<>current_setting('test.other_before') then raise exception 'Unrelated queue changed'; end if;
 if (select status from public.corrective_action_events where id=current_setting('test.qa_event')::uuid)<>'sent' then raise exception 'Target not completed'; end if;
 if (select attempts from public.corrective_action_events where id=current_setting('test.qa_event')::uuid)<>1 then raise exception 'Unexpected retries'; end if;
 if (select automation_enabled from public.corrective_action_settings) then raise exception 'Global automation unexpectedly ON'; end if;
end $$;

-- Native pending/Staff visibility on the new approval audit table remains denied.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3","aal":"aal2"}',true);
set local role authenticated;
do $$ begin if exists(select 1 from public.corrective_action_qa_runs) then raise exception 'Pending sees QA audit'; end if; end $$;
reset role;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2","aal":"aal2"}',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.corrective_action_qa_runs) then raise exception 'Staff sees QA audit'; end if;
 if (select count(*) from public.corrective_actions)<>5 then raise exception 'Existing Team visibility changed'; end if;
end $$;
reset role;

-- Independent event: native ledger marks an ambiguous replay uncertain, not done.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_ca_qa_approve('eeeeeeee-eeee-4eee-8eee-000000000003',true);
select public.defectrag_ca_qa_approve('eeeeeeee-eeee-4eee-8eee-000000000004',true);
select public.defectrag_ca_qa_approve('eeeeeeee-eeee-4eee-8eee-000000000005',true);
select public.defectrag_ca_qa_revoke('eeeeeeee-eeee-4eee-8eee-000000000004');
reset role;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select public.qa_expect_denied('select public.defectrag_ca_qa_claim(''eeeeeeee-eeee-4eee-8eee-000000000004'')');
select set_config('test.no_effect_lease',public.defectrag_ca_qa_claim('eeeeeeee-eeee-4eee-8eee-000000000005')->>'lease_token',true);
select public.defectrag_ca_qa_finish('eeeeeeee-eeee-4eee-8eee-000000000005',current_setting('test.no_effect_lease')::uuid,false);
select set_config('test.ambiguous_lease',public.defectrag_ca_qa_claim('eeeeeeee-eeee-4eee-8eee-000000000003')->>'lease_token',true);
do $$ declare r jsonb; begin
 perform public.defectrag_ca_qa_effect('eeeeeeee-eeee-4eee-8eee-000000000003',current_setting('test.ambiguous_lease')::uuid,false,null);
 r:=public.defectrag_ca_qa_effect('eeeeeeee-eeee-4eee-8eee-000000000003',current_setting('test.ambiguous_lease')::uuid,false,null);
 if r->>'manual_review'<>'true' or r->>'execute'<>'false' then raise exception 'Ambiguity not quarantined'; end if;
 perform public.defectrag_ca_qa_finish('eeeeeeee-eeee-4eee-8eee-000000000003',current_setting('test.ambiguous_lease')::uuid,false);
end $$;
reset role;
do $$ begin
 if exists(select 1 from public.corrective_action_events where id in ('eeeeeeee-eeee-4eee-8eee-000000000004','eeeeeeee-eeee-4eee-8eee-000000000005') and status<>'dead') then raise exception 'Revoked/consumed QA event left replayable'; end if;
 if (select status from public.corrective_action_events where id='eeeeeeee-eeee-4eee-8eee-000000000003')<>'dead'
 or (select state from public.corrective_action_effects where event_id='eeeeeeee-eeee-4eee-8eee-000000000003')<>'uncertain' then raise exception 'Actual production ledger quarantine mismatch'; end if;
end $$;
rollback;
select 'QA scoped SQL contracts PASS; synthetic Auth fixtures only' as result;
