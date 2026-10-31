-- OFFLINE ONLY. Synthetic JWT/factor fixtures, NOT native Supabase login.
-- Owner-CC contracts for supabase_corrective_actions_owner_cc.sql.
begin;
create function public.cc_expect_denied(sql text) returns void language plpgsql as $$
begin execute sql; raise exception 'Unexpected authorization success'; exception when insufficient_privilege then null; end; $$;
insert into auth.users(id,email,email_confirmed_at) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','supervisor@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','owner@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','revoked@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4','unverified@example.invalid',null);
insert into public.staff_members(user_id,display_name,role) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','CC Developer supervisor','developer'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','CC owner','staff'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','CC revoked owner','staff'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4','CC unverified owner','staff');
insert into auth.mfa_factors(id,user_id,factor_type,status) select gen_random_uuid(),user_id,'totp','verified' from public.staff_members;
insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path) values
 ('dddddddddddddddddddddddddddddddd','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','{}','fixture/image.jpg','fixture/heatmap.jpg');
insert into public.staff_notes(id,inspection_id,author_id,body)
 select ('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,'dddddddddddddddddddddddddddddddd',
 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject"}' from generate_series(1,5) n;
-- Case n: 1 distinct owner, 2 owner is supervisor, 3 revoked owner, 4 unverified owner, 5 QA (distinct owner).
insert into public.corrective_actions(id,inspection_id,review_id,reviewer_id,review_snapshot,confirmed_by,owner_id,supervisor_id,priority,description,due_at)
 select ('cccccccc-cccc-4ccc-8ccc-'||lpad(n::text,12,'0'))::uuid,'dddddddddddddddddddddddddddddddd',
 ('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','CC human review',
 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
 (array['aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2'])[n]::uuid,
 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','High',case when n=5 then 'QA disposable offline case' else 'CC disposable offline case' end,now()+interval '2 hours' from generate_series(1,5) n;
-- Revoke after assignment, as a later access change would.
update public.staff_members set revoked_at=now() where user_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3';
insert into public.corrective_action_events(id,case_id,version,kind)
 select ('eeeeeeee-eeee-4eee-8eee-'||lpad(n::text,12,'0'))::uuid,('cccccccc-cccc-4ccc-8ccc-'||lpad(n::text,12,'0'))::uuid,1,'created' from generate_series(1,5) n;

-- Production path: global gate ON only inside this disposable database.
update public.corrective_action_settings set automation_enabled=true;
update public.corrective_action_events set status='sending',attempts=1,lease_token='ffffffff-ffff-4fff-8fff-000000000001',lease_until=now()+interval '5 minutes'
 where id::text like 'eeeeeeee-eeee-4eee-8eee-00000000000_' and id<>'eeeeeeee-eeee-4eee-8eee-000000000005';
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
select public.cc_expect_denied('select public.defectrag_ca_effect(''eeeeeeee-eeee-4eee-8eee-000000000001'',''ffffffff-ffff-4fff-8fff-000000000001'',''notification'')');
reset role;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
do $$ declare r jsonb; lease uuid:='ffffffff-ffff-4fff-8fff-000000000001'; begin
 r:=public.defectrag_ca_effect('eeeeeeee-eeee-4eee-8eee-000000000001',lease,'notification');
 if r->>'execute'<>'true' or r->>'recipient_email'<>'supervisor@example.invalid' or r->>'cc_email' is distinct from 'owner@example.invalid' then raise exception 'Distinct owner must be copied: %',r; end if;
 for n in 2..4 loop
  r:=public.defectrag_ca_effect(('eeeeeeee-eeee-4eee-8eee-'||lpad(n::text,12,'0'))::uuid,lease,'notification');
  if r->>'execute'<>'true' or r->>'recipient_email'<>'supervisor@example.invalid' or r->>'cc_email' is not null then raise exception 'Case % must notify supervisor without copy: %',n,r; end if;
 end loop;
 -- One effect and one receipt remain the exactly-once boundary.
 r:=public.defectrag_ca_effect('eeeeeeee-eeee-4eee-8eee-000000000001',lease,'notification',true,'<cc-local-sink@example.invalid>');
 if r->>'done'<>'true' then raise exception 'Receipt not recorded'; end if;
 r:=public.defectrag_ca_effect('eeeeeeee-eeee-4eee-8eee-000000000001',lease,'notification');
 if r->>'execute'<>'false' or r->>'done'<>'true' or r ? 'cc_email' then raise exception 'Duplicate suppression failed: %',r; end if;
 r:=public.defectrag_ca_effect('eeeeeeee-eeee-4eee-8eee-000000000002',lease,'notification');
 if r->>'manual_review'<>'true' or r->>'execute'<>'false' then raise exception 'Interrupted effect must need manual review: %',r; end if;
end $$;
reset role;
update public.corrective_action_settings set automation_enabled=false;

-- QA path: approved one-shot QA event keeps the fixed sink envelope with no copy.
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);
set local role authenticated;
select public.defectrag_ca_qa_approve('eeeeeeee-eeee-4eee-8eee-000000000005',true);
reset role;
select set_config('request.jwt.claims','{"role":"service_role"}',true);
set local role service_role;
select set_config('test.qa_lease',public.defectrag_ca_qa_claim('eeeeeeee-eeee-4eee-8eee-000000000005')->>'lease_token',true);
do $$ declare r jsonb; begin
 r:=public.defectrag_ca_qa_effect('eeeeeeee-eeee-4eee-8eee-000000000005',current_setting('test.qa_lease')::uuid,false,null);
 if r->>'execute'<>'true' or r->>'recipient_email'<>'supervisor@example.invalid' or r ? 'cc_email' then raise exception 'QA must keep the fixed sink envelope: %',r; end if;
end $$;
reset role;
do $$ begin if (select automation_enabled from public.corrective_action_settings) then raise exception 'Global automation unexpectedly ON'; end if; end $$;
commit;
select 'OWNER_CC_CONTRACTS_PASS';
