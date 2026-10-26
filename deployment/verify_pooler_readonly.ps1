# Run interactively only when a read-only login check is needed and authorized.
# No password argument, environment variable, URI, file or transcript is created.
# -ValidateOnly checks the cached client offline; it never authenticates remotely.
param([switch]$ValidateOnly)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'supabase_tls.ps1')
$rotationImage='postgres:17-alpine'
& docker image inspect $rotationImage --format '{{.Id}}' | Out-Null
if($LASTEXITCODE -ne 0){throw 'The cached PostgreSQL17 image is unavailable. No download or connection attempted.'}
if($ValidateOnly){
    Test-SupabaseTls -Offline
    & docker run --rm --pull never --network none --mount $supabaseTlsMount $rotationImage sh -c 'psql --version; test -s /certs/supabase-ca.crt'
    if($LASTEXITCODE -ne 0){throw 'Offline client/TLS trust validation failed'}
    Write-Host 'Offline validation passed. No Supabase authentication was attempted.'
    return
}
Test-SupabaseTls
Write-Host 'Enter the working DATABASE password privately at the psql prompt. It will not echo.'
Write-Host 'Exactly one connection attempt will be made. Stop on failure; do not guess or reset again.'
$rotationQuery='BEGIN READ ONLY; SELECT current_user, current_database(), current_setting(''transaction_read_only'') AS read_only, (SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()) AS server_connection_tls; ROLLBACK;'
& docker run --rm --pull never --interactive --tty `
    --env PGSSLMODE=verify-full --env PGSSLROOTCERT=/certs/supabase-ca.crt `
    --mount $supabaseTlsMount `
    --env PGCONNECT_TIMEOUT=15 `
    $rotationImage psql --no-psqlrc --set ON_ERROR_STOP=1 --password `
    --host aws-0-ap-northeast-1.pooler.supabase.com --port 5432 `
    --username postgres.zrzqpbcomlorfzszolrs --dbname postgres --command $rotationQuery
if($LASTEXITCODE -ne 0){throw 'The one read-only connection failed. Retain the error text only; do not disclose the password or retry automatically.'}
Write-Host 'Read-only connection completed. Expected current_user=postgres, database=postgres, read_only=on.'
Write-Host 'Client-to-pooler TLS certificate/hostname verification was required. server_connection_tls describes the database-side connection.'
