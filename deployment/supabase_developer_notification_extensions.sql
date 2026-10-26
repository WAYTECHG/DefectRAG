-- REVIEW ONLY. Explicit production approval required. No schedule or sends.
-- Verified preflight: both extensions absent, Vault already installed.
-- No drops/reinstalls: preserve any existing extension if state changes.
begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
create extension if not exists pg_cron with schema pg_catalog;
create extension if not exists pg_net with schema extensions;
commit;
