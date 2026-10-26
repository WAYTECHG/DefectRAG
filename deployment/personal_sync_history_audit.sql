-- READ ONLY; scoped to the owner of the one disposable synchronization QA record.
-- Metadata for import comparison only. Does NOT import or change any record.
with target as (
 select owner_id from public.personal_inspections where id='c82bf820f305459988c6e94494514edf'
), records as (
 select i.* from public.personal_inspections i join target t on t.owner_id=i.owner_id
)
select jsonb_build_object(
 'cloud_total',(select count(*) from records),
 'cloud_active',(select count(*) from records where archived_at is null),
 'cloud_archived',(select count(*) from records where archived_at is not null),
 'records',(select jsonb_agg(jsonb_build_object('id',id,'archived',archived_at is not null,
   'category',payload->>'category','verdict',payload->>'verdict','batch',payload->>'batch',
   'score',payload->'score','threshold',payload->'threshold','model_id',payload->>'model_id',
   'request_fingerprint',payload->>'request_fingerprint',
   'image_sha256',substring(image_path from 'image-([a-f0-9]{64})\.jpg$'),
   'heatmap_sha256',substring(heatmap_path from 'heatmap-([a-f0-9]{64})\.jpg$'),
   'sync_version',sync_version)) from records)
) as private_import_audit;
