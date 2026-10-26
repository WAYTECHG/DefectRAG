-- SELECT ONLY after manual approved migration. One result; no payloads/leases.
select jsonb_build_object(
 'global_automation_off',not exists(select 1 from public.corrective_action_settings where automation_enabled),
 'mfa_required',(select mfa_required from public.defectrag_auth_settings where singleton),
 'qa_rls_enabled',(select relrowsecurity from pg_class where oid='public.corrective_action_qa_runs'::regclass),
 'qa_direct_writes_denied',not has_table_privilege('authenticated','public.corrective_action_qa_runs','INSERT,UPDATE,DELETE')
   and not has_table_privilege('service_role','public.corrective_action_qa_runs','SELECT,INSERT,UPDATE,DELETE'),
 'native_rpcs_guarded_grants',(select count(*)=3 and bool_and(has_function_privilege('authenticated',p.oid,'EXECUTE')
   and not has_function_privilege('anon',p.oid,'EXECUTE') and not has_function_privilege('service_role',p.oid,'EXECUTE')) from pg_proc p
   where p.oid in ('public.defectrag_ca_qa_readiness()'::regprocedure,'public.defectrag_ca_qa_approve(uuid,boolean)'::regprocedure,'public.defectrag_ca_qa_revoke(uuid)'::regprocedure)),
 'worker_rpcs_service_only',(select count(*)=3 and bool_and(has_function_privilege('service_role',p.oid,'EXECUTE')
   and not has_function_privilege('anon',p.oid,'EXECUTE') and not has_function_privilege('authenticated',p.oid,'EXECUTE')) from pg_proc p
   where p.oid in ('public.defectrag_ca_qa_claim(uuid)'::regprocedure,'public.defectrag_ca_qa_effect(uuid,uuid,boolean,text)'::regprocedure,'public.defectrag_ca_qa_finish(uuid,uuid,boolean)'::regprocedure)),
 'internal_helper_not_directly_callable',not has_function_privilege('authenticated','public.defectrag_ca_qa_authorized(uuid)','EXECUTE')
   and not has_function_privilege('service_role','public.defectrag_ca_qa_authorized(uuid)','EXECUTE')
   and not has_function_privilege('anon','public.defectrag_ca_qa_authorized(uuid)','EXECUTE'),
 'existing_effect_service_only',has_function_privilege('service_role','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE')
   and not has_function_privilege('authenticated','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE')
   and not has_function_privilege('anon','public.defectrag_ca_effect(uuid,uuid,text,boolean,text)','EXECUTE'),
 'reviewed_effect_gate_matches',md5(replace((select prosrc from pg_proc where oid='public.defectrag_ca_effect(uuid,uuid,text,boolean,text)'::regprocedure),E'\r\n',E'\n'))='3db8dc902488441eb3a7b946a21e1289'
) as qa_postflight;
