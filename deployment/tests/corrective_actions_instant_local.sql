-- OFFLINE ONLY. Synthetic JWT/factor fixtures and recording stand-ins for Vault/pg_net.
-- Doorbell contracts for supabase_corrective_actions_instant.sql.
begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','supervisor@example.invalid',now()),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','owner@example.invalid',now());
insert into public.staff_members(user_id,display_name,role) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','Ring Developer','developer'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','Ring owner','staff');
insert into auth.mfa_factors(id,user_id,factor_type,status) select gen_random_uuid(),user_id,'totp','verified' from public.staff_members;
insert into public.shared_inspections(id,owner_id,payload,image_path,heatmap_path)
 select repeat(n::text,32),'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','{}','fixture/image.jpg','fixture/heatmap.jpg' from generate_series(1,3) n;
insert into public.staff_notes(id,inspection_id,author_id,body)
 select ('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,repeat(n::text,32),'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2',
 'DEFECTRAG_REVIEW_V1:{"status":"Reviewed","decision":"Reject"}' from generate_series(1,3) n;
update public.corrective_action_settings set automation_enabled=true;
create function pg_temp.create_case(n integer) returns uuid language sql as $$
 select public.defectrag_create_corrective_action(repeat(n::text,32),('bbbbbbbb-bbbb-4bbb-8bbb-'||lpad(n::text,12,'0'))::uuid,true,
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','Normal','Ring offline test case',now()+interval '3 days') $$;
select set_config('request.jwt.claims','{"role":"authenticated","sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1","aal":"aal2"}',true);

-- 1. No Vault secret yet: saving works, nothing rings.
set local role authenticated;
select set_config('test.case1',pg_temp.create_case(1)::text,true);
reset role;
do $$ begin if (select count(*) from net.calls)<>0 then raise exception 'Rang without a Vault secret'; end if;
 if (select count(*) from public.corrective_action_events where case_id=current_setting('test.case1')::uuid and kind='created')<>1 then raise exception 'Event missing'; end if; end $$;

-- 2. With the secret: a created case rings once with the exact request.
insert into vault.secrets_t(name,decrypted_secret) values('defectrag_ca_worker_bearer',repeat('k',48));
set local role authenticated;
select set_config('test.case2',pg_temp.create_case(2)::text,true);
reset role;
do $$ declare c net.calls; begin
 if (select count(*) from net.calls)<>1 then raise exception 'Created case must ring exactly once'; end if;
 select * into c from net.calls;
 if c.url<>'https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/corrective-actions' or c.body<>'{}'::jsonb
 or c.headers->>'Authorization'<>'Bearer '||repeat('k',48) or c.timeout_milliseconds<>110000 then raise exception 'Unexpected request %',c; end if;
end $$;

-- 3. A saved update rings once more.
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.case2')::uuid,1,'Assigned','Assigned for offline ring test');
reset role;
do $$ begin if (select count(*) from net.calls)<>2 then raise exception 'Update must ring'; end if; end $$;

-- 4. Timer-driven kinds never ring; the timer itself sends them.
insert into public.corrective_action_events(case_id,version,kind) values(current_setting('test.case2')::uuid,2,'reminder'),(current_setting('test.case2')::uuid,2,'overdue');
do $$ begin if (select count(*) from net.calls)<>2 then raise exception 'Reminder/overdue must not ring'; end if; end $$;

-- 5. Automation OFF: updates still save and queue, but nothing rings.
update public.corrective_action_settings set automation_enabled=false;
set local role authenticated;
select public.defectrag_update_corrective_action(current_setting('test.case2')::uuid,2,'In Progress','Work started offline');
reset role;
do $$ begin if (select count(*) from net.calls)<>2 then raise exception 'Rang while automation OFF'; end if;
 if not exists(select 1 from public.corrective_action_events where case_id=current_setting('test.case2')::uuid and version=3 and status='queued') then raise exception 'Update not queued'; end if; end $$;
update public.corrective_action_settings set automation_enabled=true;

-- 6. A failing network call never blocks saving; the event waits for the timer.
select set_config('test.net_fail','1',true);
set local role authenticated;
select set_config('test.case3',pg_temp.create_case(3)::text,true);
select public.defectrag_update_corrective_action(current_setting('test.case2')::uuid,3,'Resolved','Fixed while network failed');
reset role;
select set_config('test.net_fail','0',true);
do $$ begin if (select count(*) from net.calls)<>2 then raise exception 'Failed calls must not be recorded'; end if;
 if (select count(*) from public.corrective_action_events where status='queued' and (case_id=current_setting('test.case3')::uuid or version=4))<>2 then raise exception 'Saves lost on network failure'; end if; end $$;

-- 7. Nobody can call the doorbell directly.
do $$ begin
 if has_function_privilege('anon','public.defectrag_ca_ring()','EXECUTE') or has_function_privilege('authenticated','public.defectrag_ca_ring()','EXECUTE')
 or has_function_privilege('service_role','public.defectrag_ca_ring()','EXECUTE') then raise exception 'Doorbell ACL too wide'; end if;
end $$;
rollback;
select 'INSTANT_CONTRACTS_PASS';
