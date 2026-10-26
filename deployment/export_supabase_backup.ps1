# Private Windows export using cached official PostgreSQL17. No production writes.
# User enters the existing password at TWO hidden pg_dump/pg_dumpall prompts.
# Native DPAPI protects exports for this Windows account; do not upload to Git.
param([switch]$ValidateOnly)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'supabase_tls.ps1')
try{Add-Type -AssemblyName System.Security.Cryptography.ProtectedData -ErrorAction Stop}
catch{Add-Type -AssemblyName System.Security -ErrorAction Stop} # Windows PowerShell5.1
$backupImage='postgres:17-alpine'
& docker image inspect $backupImage --format '{{.Id}}' | Out-Null
if($LASTEXITCODE -ne 0){throw 'Cached PostgreSQL17 image unavailable; no image download or remote connection attempted'}

function New-PrivateExportDirectory([string]$Path){
    if(Test-Path -LiteralPath $Path){throw 'Refusing to overwrite an existing backup directory'}
    New-Item -ItemType Directory -Path $Path | Out-Null
    $resolved=(Resolve-Path -LiteralPath $Path).Path
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $permissions=[Security.AccessControl.DirectorySecurity]::new()
    $permissions.SetOwner($sid);$permissions.SetAccessRuleProtection($true,$false)
    $permissions.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
    Set-Acl -LiteralPath $resolved -AclObject $permissions
    return $resolved
}

function Protect-Export([string]$Path){
    $plain=[System.IO.File]::ReadAllBytes($Path)
    $encrypted=$null;$recovered=$null
    try{
        $encrypted=[Security.Cryptography.ProtectedData]::Protect($plain,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        $sealedPath=$Path+'.dpapi'
        if(Test-Path -LiteralPath $sealedPath){throw 'Refusing to overwrite an encrypted backup'}
        [System.IO.File]::WriteAllBytes($sealedPath,$encrypted)
        $recovered=[Security.Cryptography.ProtectedData]::Unprotect([System.IO.File]::ReadAllBytes($sealedPath),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        $sha=[Security.Cryptography.SHA256]::Create()
        try{
            if([Convert]::ToBase64String($sha.ComputeHash($plain)) -ne [Convert]::ToBase64String($sha.ComputeHash($recovered))){throw 'Encrypted-export recovery check failed'}
        }finally{$sha.Dispose()}
        # Only this newly generated plaintext export is removed AFTER successful
        # encrypted readback. No recursive deletion or existing data is touched.
        Remove-Item -LiteralPath $Path
        return $sealedPath
    }finally{
        if($plain){[Array]::Clear($plain,0,$plain.Length)}
        if($recovered){[Array]::Clear($recovered,0,$recovered.Length)}
    }
}

if($ValidateOnly){
    $sample=[Text.Encoding]::UTF8.GetBytes('NONSECRET_BACKUP_VALIDATION')
    $sealed=[Security.Cryptography.ProtectedData]::Protect($sample,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    $roundtrip=[Security.Cryptography.ProtectedData]::Unprotect($sealed,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    if([Convert]::ToBase64String($sample) -ne [Convert]::ToBase64String($roundtrip)){throw 'DPAPI validation failed'}
    $fixtureBase=Join-Path (Split-Path $PSScriptRoot -Parent) 'runtime\backup-export-validation'
    $fixtureDir=New-PrivateExportDirectory (Join-Path $fixtureBase ([Guid]::NewGuid().ToString('N')))
    $fixturePath=Join-Path $fixtureDir 'nonsecret-fixture.txt'
    & docker run --rm --pull never --network none --mount "type=bind,source=$fixtureDir,target=/backup" $backupImage sh -c 'printf NONSECRET_BACKUP_VALIDATION > /backup/nonsecret-fixture.txt'
    if($LASTEXITCODE -ne 0){throw 'Offline private bind-mount write validation failed'}
    $protectedFixture=Protect-Export $fixturePath
    if((Test-Path -LiteralPath $fixturePath) -or -not(Test-Path -LiteralPath $protectedFixture)){throw 'Encrypted-file lifecycle validation failed'}
    Test-SupabaseTls -Offline
    & docker run --rm --pull never --network none --mount $supabaseTlsMount $backupImage sh -c 'pg_dump --version; pg_dumpall --version; pg_restore --version; test -s /certs/supabase-ca.crt'
    if($LASTEXITCODE -ne 0){throw 'Offline tool/TLS validation failed'}
    Write-Host 'Offline tools and native encryption roundtrip passed. No Supabase connection, password prompt or backup created.'
    return
}

# Fail before creating an export directory or asking for any password.
Test-SupabaseTls
$backupBase=Join-Path $env:LOCALAPPDATA 'DefectRAG\PrivateBackups'
$backupLeaf='supabase-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$backupDir=Join-Path $backupBase $backupLeaf
$backupDir=New-PrivateExportDirectory $backupDir
if($backupDir.Contains(',')){throw 'Unsupported comma in private backup path; no remote connection attempted'}
$connection=@('--host','aws-0-ap-northeast-1.pooler.supabase.com','--port','5432','--username','postgres.zrzqpbcomlorfzszolrs','--password')
$container=@('run','--rm','--pull','never','--interactive','--tty','--env','PGSSLMODE=verify-full','--env','PGSSLROOTCERT=/certs/supabase-ca.crt','--env','PGCONNECT_TIMEOUT=15','--mount',$supabaseTlsMount,'--mount',"type=bind,source=$backupDir,target=/backup",$backupImage)
$manifest=[ordered]@{schema=1;project='zrzqpbcomlorfzszolrs';started_utc=[DateTime]::UtcNow.ToString('o');status='incomplete';password_stored=$false;encryption='Windows DPAPI CurrentUser';same_windows_profile_required=$true;storage_object_bytes_included=$false;native_encryption_key_recovery_verified=$false;isolated_restore_verified=$false;files=@()}
$manifestPath=Join-Path $backupDir 'manifest.json'
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host 'Enter the SAME working DATABASE password privately at each of the two hidden prompts.'
Write-Host 'No password is included in command arguments, environment variables or saved files.'
try{
    Write-Host '1/2: export all database schemas/data/ACLs into a custom archive.'
    & docker @container pg_dump @connection --dbname postgres --format custom --file /backup/database.dump
    if($LASTEXITCODE -ne 0){throw 'Database export failed; stop without guessing or resetting the password'}
    $manifest.files += Protect-Export (Join-Path $backupDir 'database.dump')
    Write-Host '2/2: export global role definitions; custom role passwords are deliberately excluded.'
    & docker @container pg_dumpall @connection --database postgres --roles-only --no-role-passwords --file /backup/roles.sql
    if($LASTEXITCODE -ne 0){throw 'Role export failed; this backup is incomplete'}
    $manifest.files += Protect-Export (Join-Path $backupDir 'roles.sql')
    $manifest.status='exported_not_restore_verified'
    $manifest.files=@($manifest.files | ForEach-Object { @{name=[IO.Path]::GetFileName($_);bytes=(Get-Item -LiteralPath $_).Length;sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash} })
}catch{
    $manifest.status='failed_or_incomplete'
    Write-Warning 'Export incomplete. Any partial plaintext remains in the owner-only folder; do not share it. No migration is authorized.'
    throw
}finally{
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Write-Host "Private backup directory: $backupDir"
}
Write-Host 'Exports encrypted and read back successfully. This is NOT an isolated database restore test.'
Write-Host 'Keep the migration blocked. Storage bytes, native key recovery and compatible restoration still require verification.'
