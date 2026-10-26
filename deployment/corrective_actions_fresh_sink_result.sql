-- SELECT ONLY for the approved disposable test. Never returns a lease/receipt/key.
select jsonb_build_object(
 'global_automation_off',not exists(select 1 from public.corrective_action_settings where automation_enabled),
 'mfa_required',(select mfa_required from public.defectrag_auth_settings where singleton),
 'case',(select jsonb_build_object('id',id,'state',state,'version',version,
   'resolved_timestamp',resolved_at is not null,'closed_timestamp',closed_at is not null,
   'owner_supervisor_match',owner_id=supervisor_id)
   from public.corrective_actions where id='fb462978-af2b-4b4f-a280-2c9803dc4bb1'::uuid),
 'planned_event',(select jsonb_build_object('id',id,'status',status,'attempts',attempts,
   'lease_cleared',lease_token is null and lease_until is null,'last_error',last_error)
   from public.corrective_action_events where id='b857cc19-6e07-4772-8651-b91b52c9bb4b'::uuid
   and case_id='fb462978-af2b-4b4f-a280-2c9803dc4bb1'::uuid),
 'effect',(select jsonb_build_object('state',state,'receipt_present',receipt is not null,
   'finished',finished_at is not null) from public.corrective_action_effects
   where event_id='b857cc19-6e07-4772-8651-b91b52c9bb4b'::uuid and effect='notification'),
 'qa_grant',(select jsonb_build_object('claimed',claimed_at is not null,
   'finished',finished_at is not null,'revoked',revoked_at is not null,
   'expired',expires_at<=now(),'remaining_seconds',greatest(0,extract(epoch from expires_at-now()))::integer) from public.corrective_action_qa_runs
   where event_id='b857cc19-6e07-4772-8651-b91b52c9bb4b'::uuid),
 'history',(select jsonb_agg(jsonb_build_object('version',version,'state',state) order by version)
   from public.corrective_action_history where case_id='fb462978-af2b-4b4f-a280-2c9803dc4bb1'::uuid),
 'case_events',(select jsonb_agg(jsonb_build_object('id',id,'version',version,'kind',kind,
   'status',status,'attempts',attempts) order by version,kind) from public.corrective_action_events
   where case_id='fb462978-af2b-4b4f-a280-2c9803dc4bb1'::uuid)
) as single_sink_result;
