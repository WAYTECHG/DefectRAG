# Public CA downloaded over HTTPS from this project's Database Settings link.
# No credentials, network calls or setting changes occur when dot-sourcing.
$supabaseCertificatePath=Join-Path $PSScriptRoot 'certificates\supabase-prod-ca-2021.crt'
$supabaseExpectedCaHash='700723581420DD1AC98FD7E9AC529F0EF210EADCAF87FC868A3AD7D114C2F3B7'
if((Get-FileHash -LiteralPath $supabaseCertificatePath -Algorithm SHA256).Hash -ne $supabaseExpectedCaHash){throw 'Supabase public CA fingerprint changed; stop for review'}
if($supabaseCertificatePath.Contains(',')){throw 'Unsupported comma in certificate mount path'}
$supabaseTlsMount="type=bind,source=$supabaseCertificatePath,target=/certs/supabase-ca.crt,readonly"
$supabaseTlsPython=Join-Path (Split-Path $PSScriptRoot -Parent) '.venv\Scripts\python.exe'
function Test-SupabaseTls([switch]$Offline){
    if(-not(Test-Path -LiteralPath $supabaseTlsPython)){throw 'Existing project Python environment is required for the credential-free TLS preflight; no dependency install attempted'}
    $tlsProbeArgs=@((Join-Path $PSScriptRoot 'check_supabase_tls.py'))
    if($Offline){$tlsProbeArgs+='--offline'}
    & $supabaseTlsPython @tlsProbeArgs
    if($LASTEXITCODE -ne 0){throw 'Certificate verification failed BEFORE login. Do not reset the password or weaken TLS.'}
}
