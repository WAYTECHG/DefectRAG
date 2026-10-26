-- SELECT ONLY: no claims, sends, schema or permission changes.
select jsonb_build_object(
 'auth_flags',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'event',(select jsonb_build_object('status',o.status,'attempts',o.attempts,'last_error',o.last_error,'request_status',r.status,'current_version',o.version=r.version,'has_membership',exists(select 1 from public.staff_members m where m.user_id=o.subject_id),'snapshot_present',o.email_payload is not null,'delivered_at',o.delivered_at) from public.staff_notification_outbox o join public.staff_access_requests r on r.user_id=o.subject_id where o.id='3d25e7b3-04c4-43c8-a49e-e473be3bcbdc'::uuid),
 'claim_rpc',(select jsonb_build_object('security_definer',p.prosecdef,'owner',pg_get_userbyid(p.proowner),'config',p.proconfig,'service_role_execute',has_function_privilege('service_role',p.oid,'EXECUTE'),'anonymous_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'signed_in_execute',has_function_privilege('authenticated',p.oid,'EXECUTE')) from pg_proc p where p.oid=to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)')),
 'clock_rows',(select count(*) from public.notification_dispatch_clock),
 'clock_ready',coalesce((select next_claim_at<=now() from public.notification_dispatch_clock where singleton),false)
) as no_send_audit;
