# Public CA downloaded over HTTPS from this project's Database Settings link.
# No credentials, network calls or setting changes occur when dot-sourcing.
$supabaseCertificatePath=Join-Path $PSScriptRoot 'certificates\supabase-prod-ca-2021.crt'
$supabaseExpectedCaHash='700723581420DD1AC98FD7E9AC529F0EF210EADCAF87FC868A3AD7D114C2F3B7'
if((Get-FileHash -LiteralPath $supabaseCertificatePath -Algorithm SHA256).Hash -ne $supabaseExpectedCaHash){throw 'Supabase public CA fingerprint changed; stop for review'}
if($supabaseCertificatePath.Contains(',')){throw 'Unsupported comma in certificate mount path'}
$supabaseTlsMount="type=bind,source=$supabaseCertificatePath,target=/certs/supabase-ca.crt,readonly"
. (Join-Path $PSScriptRoot 'project_python.ps1')
function Test-SupabaseTls([switch]$Offline){
    $supabaseTlsPython=Get-ProjectPython  # throws if no project Python exists; nothing is installed
    $tlsProbeArgs=@((Join-Path $PSScriptRoot 'check_supabase_tls.py'))
    if($Offline){$tlsProbeArgs+='--offline'}
    & $supabaseTlsPython @tlsProbeArgs
    if($LASTEXITCODE -ne 0){throw 'Certificate verification failed BEFORE login. Do not reset the password or weaken TLS.'}
}
