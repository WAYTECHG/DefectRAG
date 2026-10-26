-- SELECT ONLY. One result row; no lease/recipient/payload output, no claims.
select
 not exists(select 1 from public.corrective_action_settings where automation_enabled) as global_automation_off,
 (select mfa_required from public.defectrag_auth_settings where singleton) as mfa_required,
 to_regclass('public.corrective_action_qa_runs') is null as qa_extension_not_installed,
 md5(replace((select prosrc from pg_proc where oid='public.defectrag_ca_effect(uuid,uuid,text,boolean,text)'::regprocedure),E'\r\n',E'\n'))='127ba8841692b7f272854a7e9ff67b53' as reviewed_effect_baseline_matches,
 not has_function_privilege('anon','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE')
 and not has_function_privilege('authenticated','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE')
 and has_function_privilege('service_role','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE') as existing_effect_grants_ok,
 (select count(*) from public.corrective_actions) as case_count,
 (select count(*) from public.corrective_action_events) as event_count,
 (select count(*) from public.corrective_action_effects) as effect_count;
