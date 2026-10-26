-- ONE read-only result. No records, secrets, claims, migration or flag changes.
select jsonb_build_object(
 'auth_settings',(select jsonb_build_object('registration_enabled',registration_enabled,'mfa_required',mfa_required) from public.defectrag_auth_settings where singleton),
 'personal_table',to_regclass('public.personal_inspections') is not null,
 'personal_notes',to_regclass('public.personal_notes') is not null,
 'staff_guard',to_regprocedure('public.defectrag_is_staff()') is not null,
 'owner_action_rpc',to_regprocedure('public.defectrag_personal_action(text,text,text,jsonb)') is not null,
 'owner_archive_rpc',to_regprocedure('public.defectrag_personal_archive(text[],boolean)') is not null,
 'personal_bucket_private',(select not public from storage.buckets where id='personal-inspections'),
 'sync_column_already_present',exists(select 1 from information_schema.columns where table_schema='public' and table_name='personal_inspections' and column_name='sync_version'),
 'sync_rpc_already_present',to_regprocedure('public.defectrag_personal_sync_apply(uuid,text,bigint,text,jsonb)') is not null,
 'receipt_table_already_present',to_regclass('public.personal_sync_receipts') is not null
) as personal_sync_preflight;
