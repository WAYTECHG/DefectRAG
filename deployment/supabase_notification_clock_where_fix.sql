-- REVIEW ONLY: NOT EXECUTED. Separate production approval REQUIRED.
-- Fixes the confirmed clock UPDATE failure; no claims, sends or data updates.
-- Existing installations: run this correction ONCE, NOT the original migration.
-- Keep delivery0. Leaves safeupdate, owner, grants, RLS, auth flags and data intact.
begin;
set local lock_timeout='5s';
set local statement_timeout='20s';
do $clock_where_fix$
declare
 target regprocedure := to_regprocedure('public.defectrag_claim_direct_notifications(integer,uuid)');
 before_definition text;
 before_attributes record;
 unsafe_statement constant text := 'update public.notification_dispatch_clock set next_claim_at=now()+interval ''30 seconds'';';
 safe_statement constant text := 'update public.notification_dispatch_clock set next_claim_at=now()+interval ''30 seconds'' where singleton;';
begin
 if target is null then raise exception 'STOP: direct claim function is missing'; end if;
 select proowner,proacl,prosecdef,proconfig into strict before_attributes
 from pg_proc where oid=target;
 if not before_attributes.prosecdef then raise exception 'STOP: function security differs; review first'; end if;
 before_definition := pg_get_functiondef(target);
 if length(before_definition)-length(replace(before_definition,unsafe_statement,''))<>length(unsafe_statement) then
  raise exception 'STOP: expected exactly one known unsafe clock statement; function changed or fix already applied';
 end if;
 -- Recreate ONLY this live function, with precisely one statement substitution.
 execute replace(before_definition,unsafe_statement,safe_statement);
 if exists(select 1 from pg_proc p where p.oid=target and (
  p.proowner is distinct from before_attributes.proowner or
  p.proacl is distinct from before_attributes.proacl or
  p.prosecdef is distinct from before_attributes.prosecdef or
  p.proconfig is distinct from before_attributes.proconfig)) then
  raise exception 'STOP: function metadata changed; transaction rolled back';
 end if;
 if position(safe_statement in pg_get_functiondef(target))=0 then
  raise exception 'STOP: corrected statement was not retained';
 end if;
end;
$clock_where_fix$;
commit;
