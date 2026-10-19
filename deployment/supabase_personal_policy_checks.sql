-- OPTIONAL OWNER-EXECUTED POLICY TEST. Review first; run AFTER the migration.
-- Synthetic SOFTWARE TEST rows only, inside a transaction that is rolled back.
-- Does not change the allowlist, real inspections, gallery or storage objects.
-- SQL role/claim impersonation tests RLS, not actual login/JWT verification.
begin;
do $$
declare owner_uuid uuid;
begin
  select user_id into owner_uuid from public.staff_members order by user_id limit 1;
  if owner_uuid is null then raise exception 'One existing approved staff account is required'; end if;
  perform set_config('defectrag.test_owner',owner_uuid::text,true);
  perform set_config('defectrag.test_id',md5(gen_random_uuid()::text),true);
  perform set_config('request.jwt.claims',jsonb_build_object('sub',owner_uuid,'role','authenticated')::text,true);
end; $$;
set local role authenticated;
do $$
declare identifier text:=current_setting('defectrag.test_id'); changed integer;
begin
  insert into public.personal_inspections(id,owner_id,payload,image_path,heatmap_path)
    values(identifier,auth.uid(),jsonb_build_object('id',identifier,'category','pcb1','verdict','Anomalous',
      'score',0.2,'threshold',0.1,'scope','Synthetic SQL SOFTWARE TEST, not inference'),
      auth.uid()::text||'/'||identifier||'/image.jpg',auth.uid()::text||'/'||identifier||'/heatmap.jpg');
  insert into public.personal_notes(inspection_id,author_id,body) values(identifier,auth.uid(),'Synthetic rollback-only policy test');
  perform public.defectrag_personal_action(identifier,'conversation','Explain the software test','{"answer":"Software fixture only"}'::jsonb);
  perform public.defectrag_personal_action(identifier,'acknowledge');
  perform public.defectrag_personal_action(identifier,'acknowledge');
  if not exists(select 1 from public.personal_inspections where id=identifier and payload->>'alert_acknowledged_by'=auth.uid()::text) then
    raise exception 'Owner acknowledgement or actor tracking failed'; end if;
  if (select count(*) from public.personal_audit where inspection_id=identifier and action='acknowledge')<>1 then
    raise exception 'Duplicate acknowledgement created inconsistent audit'; end if;
  changed:=public.defectrag_personal_archive(array[identifier],false);
  if changed<>1 then raise exception 'Owner archive failed'; end if;
  changed:=public.defectrag_personal_archive(array[identifier],false);
  if changed<>0 then raise exception 'Archive idempotency failed'; end if;
  if public.defectrag_personal_archive(array[identifier],true)<>1 then raise exception 'Owner restore failed'; end if;
  perform public.defectrag_workspace_stats('personal');
  raise notice 'PASS: owner persistence fields, notes, conversation, acknowledgement, audit idempotency, archive/restore, statistics';
end; $$;
select set_config('request.jwt.claims','{"sub":"00000000-0000-0000-0000-000000000042","role":"authenticated"}',true);
do $$
declare identifier text:=current_setting('defectrag.test_id');
begin
  if public.defectrag_is_staff() then raise exception 'Fixture UUID unexpectedly belongs to approved staff; choose another unused UUID'; end if;
  if exists(select 1 from public.personal_inspections where id=identifier) or
     exists(select 1 from public.personal_notes where inspection_id=identifier) or
     exists(select 1 from public.personal_audit where inspection_id=identifier) then
    raise exception 'Non-staff RLS leaked owner-only data'; end if;
  begin
    perform public.defectrag_personal_action(identifier,'acknowledge');
    raise exception 'Non-staff mutation incorrectly succeeded';
  exception when insufficient_privilege then null; end;
  begin
    perform public.defectrag_workspace_stats('team');
    raise exception 'Non-staff team statistics incorrectly succeeded';
  exception when insufficient_privilege then null; end;
  raise notice 'PASS: non-staff private reads and privileged mutations denied';
end; $$;
set local role anon;
do $$
begin
  begin
    perform 1 from public.personal_inspections limit 1;
    raise exception 'Anonymous personal table read incorrectly succeeded';
  exception when insufficient_privilege then null; end;
  begin
    perform public.defectrag_personal_archive(array[current_setting('defectrag.test_id')],false);
    raise exception 'Anonymous archive incorrectly succeeded';
  exception when insufficient_privilege then null; end;
  raise notice 'PASS: anonymous table and RPC privileges denied';
end; $$;
rollback;
-- All synthetic rows and audit events above have now been rolled back.
