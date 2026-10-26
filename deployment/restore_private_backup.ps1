# Isolated local rehearsal only. No production connection, password or SQL.
# Decrypted data moves through a binary pipe; no host plaintext dump is written.
param([Parameter(Mandatory=$true)][string]$BackupDirectory,[string]$RecoveryDirectory,[switch]$NativeAuth)
$ErrorActionPreference='Stop'
try{Add-Type -AssemblyName System.Security.Cryptography.ProtectedData -ErrorAction Stop}
catch{Add-Type -AssemblyName System.Security -ErrorAction Stop}
$backupFolder=(Resolve-Path -LiteralPath $BackupDirectory).Path
$manifest=Get-Content -LiteralPath (Join-Path $backupFolder 'manifest.json') -Raw | ConvertFrom-Json
if($manifest.project -ne 'zrzqpbcomlorfzszolrs' -or $manifest.status -ne 'exported_not_restore_verified'){throw 'Expected the completed project export'}
$python=Join-Path (Split-Path $PSScriptRoot -Parent) '.venv\Scripts\python.exe'
$rehearsal=Join-Path $PSScriptRoot 'rehearse_supabase_restore.py'
$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName=$python;$start.Arguments='"'+$rehearsal+'"'
if($RecoveryDirectory){$start.Arguments+=' --with-recovery'}
if($NativeAuth){if(-not $RecoveryDirectory){throw 'Native Auth rehearsal requires the verified recovery supplement'};$start.Arguments+=' --native-auth'}
$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
$process=[Diagnostics.Process]::new();$process.StartInfo=$start
$started=$false;$recoveryRoot=$null;$recoveryInventoryBytes=$null
try{
    if($RecoveryDirectory){
        $recoveryFolder=(Resolve-Path -LiteralPath $RecoveryDirectory).Path
        if(-not $recoveryFolder.StartsWith($backupFolder+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Recovery material must belong to this backup directory'}
        $supplement=Get-Content -LiteralPath (Join-Path $recoveryFolder 'recovery_manifest.json') -Raw | ConvertFrom-Json
        if($supplement.project -ne $manifest.project -or $supplement.status -ne 'encrypted_recovery_material_exported_not_full_restore_verified' -or $supplement.offline_fixture){throw 'Expected completed LIVE recovery supplement for this project'}
        if(-not (Get-Acl -LiteralPath $recoveryFolder).AreAccessRulesProtected){throw 'Expected private recovery-directory ACL'}
        function Read-CheckedRecoveryFile([string]$Name){
            if($Name -notmatch '^(root-key|storage-inventory|object-[0-9]{6})\.dpapi$'){throw 'Unexpected recovery filename'}
            $entry=@($supplement.encrypted_files | Where-Object {$_.file -ceq $Name})
            if($entry.Count -ne 1){throw 'Missing or duplicate encrypted recovery file'}
            $path=Join-Path $recoveryFolder $Name
            if((Get-Item -LiteralPath $path).Length -ne $entry[0].bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry[0].sha256){throw 'Recovery-file checksum mismatch'}
            return ,([Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($path),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser))
        }
        $recoveryRoot=Read-CheckedRecoveryFile 'root-key.dpapi'
        if([Text.Encoding]::UTF8.GetString($recoveryRoot) -notmatch '^[0-9a-fA-F]{64}$'){throw 'Invalid private recovery key format; no value displayed'}
        $recoveryInventoryBytes=Read-CheckedRecoveryFile 'storage-inventory.dpapi'
        try{$inventory=[Text.Encoding]::UTF8.GetString($recoveryInventoryBytes) | ConvertFrom-Json}
        catch{throw 'Invalid encrypted inventory; no contents displayed'}
        if($inventory.project -ne $manifest.project -or @($inventory.objects).Count -ne $supplement.storage_objects -or @($supplement.encrypted_files).Count -ne (2+$supplement.storage_objects)){throw 'Recovery inventory/manifest count mismatch'}
        $objectFiles=@{};$objectKeys=@{};$verifiedBytes=[int64]0
        foreach($object in $inventory.objects){
            $identity=[string]$object.bucket+"`0"+[string]$object.path
            if($objectFiles.ContainsKey($object.file) -or $objectKeys.ContainsKey($identity)){throw 'Duplicate recovery object/file'}
            $objectFiles[$object.file]=$true;$objectKeys[$identity]=$true
            $bytes=Read-CheckedRecoveryFile $object.file
            $sha=[Security.Cryptography.SHA256]::Create()
            try{
                $hash=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
                if($bytes.Length -ne $object.plaintext_bytes -or $hash -cne $object.plaintext_sha256){throw 'Decrypted object byte-length/hash mismatch'}
                $verifiedBytes+=$bytes.Length
            }finally{$sha.Dispose();[Array]::Clear($bytes,0,$bytes.Length)}
        }
        if($verifiedBytes -ne $supplement.plaintext_object_bytes){throw 'Recovery byte-total mismatch'}
        Write-Host ('Verified all '+$supplement.storage_objects+' decrypted object files and their SHA256 hashes; private contents were not displayed.')
    }
    if(-not $process.Start()){throw 'Cannot start isolated rehearsal'}
    $started=$true
    $outputTask=$process.StandardOutput.ReadToEndAsync();$errorTask=$process.StandardError.ReadToEndAsync()
    foreach($name in @('database.dump.dpapi','roles.sql.dpapi')){
        $entry=@($manifest.files | Where-Object {$_.name -ceq $name})
        if($entry.Count -ne 1){throw 'Missing/duplicate archive entry'}
        $file=Join-Path $backupFolder $name
        if((Get-Item -LiteralPath $file).Length -ne $entry[0].bytes -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry[0].sha256){throw 'Export checksum mismatch'}
        $plain=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($file),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try{
            $header=[BitConverter]::GetBytes([uint64]$plain.Length)
            $process.StandardInput.BaseStream.Write($header,0,$header.Length)
            $process.StandardInput.BaseStream.Write($plain,0,$plain.Length)
        }finally{[Array]::Clear($plain,0,$plain.Length)}
    }
    if($RecoveryDirectory){
        foreach($payload in @($recoveryRoot,$recoveryInventoryBytes)){
            $header=[BitConverter]::GetBytes([uint64]$payload.Length)
            $process.StandardInput.BaseStream.Write($header,0,$header.Length)
            $process.StandardInput.BaseStream.Write($payload,0,$payload.Length)
        }
    }
    $process.StandardInput.Close()
    if(-not $process.WaitForExit(240000)){$process.Kill();throw 'Isolated restore timeout; inspect only the unique rehearsal container'}
    $result=$outputTask.GetAwaiter().GetResult()
    $null=$errorTask.GetAwaiter().GetResult()
    Write-Output $result
    if($process.ExitCode -ne 0){throw 'Isolated restore did not pass; migration remains blocked. Private error payloads were not displayed.'}
}finally{
    if($recoveryRoot){[Array]::Clear($recoveryRoot,0,$recoveryRoot.Length)}
    if($recoveryInventoryBytes){[Array]::Clear($recoveryInventoryBytes,0,$recoveryInventoryBytes.Length)}
    if($started -and -not $process.HasExited){$process.Kill()}
    $process.Dispose()
}
