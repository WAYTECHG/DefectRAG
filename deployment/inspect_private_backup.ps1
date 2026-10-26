# Read/decrypt the owner's completed export in memory only. No SQL execution,
# remote connection, password, plaintext file, or inspection payload output.
param([Parameter(Mandatory=$true)][string]$BackupDirectory)
$ErrorActionPreference='Stop'
try{Add-Type -AssemblyName System.Security.Cryptography.ProtectedData -ErrorAction Stop}
catch{Add-Type -AssemblyName System.Security -ErrorAction Stop}
$resolvedBackup=(Resolve-Path -LiteralPath $BackupDirectory).Path
$manifest=Get-Content -LiteralPath (Join-Path $resolvedBackup 'manifest.json') -Raw | ConvertFrom-Json
if($manifest.project -ne 'zrzqpbcomlorfzszolrs' -or $manifest.status -ne 'exported_not_restore_verified'){throw 'Expected completed export manifest for the intended project'}
if(@($manifest.files).Count -ne 2){throw 'Expected exactly two completed encrypted exports'}
$recoveredArchive=$null
try{
    foreach($expectedName in @('database.dump.dpapi','roles.sql.dpapi')){
        $entry=@($manifest.files | Where-Object {$_.name -ceq $expectedName})
        if($entry.Count -ne 1){throw 'Export manifest has missing/duplicate file entries'}
        $file=Join-Path $resolvedBackup $expectedName
        if((Get-Item -LiteralPath $file).Length -ne $entry[0].bytes -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry[0].sha256){throw 'Encrypted export size/checksum mismatch'}
        $recovered=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($file),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        if($recovered.Length -eq 0){throw 'Decrypted export is empty'}
        if($expectedName -eq 'database.dump.dpapi'){
            if([Text.Encoding]::ASCII.GetString($recovered,0,5) -ne 'PGDMP'){throw 'Expected PostgreSQL custom archive header'}
            $recoveredArchive=$recovered
        }else{[Array]::Clear($recovered,0,$recovered.Length)}
    }
    & docker image inspect postgres:17-alpine --format '{{.Id}}' | Out-Null
    if($LASTEXITCODE -ne 0){throw 'Cached PostgreSQL17 image required; no automatic download'}
    $start=[Diagnostics.ProcessStartInfo]::new()
    $start.FileName='docker'
    $start.Arguments='run --rm --pull never --network none --interactive postgres:17-alpine pg_restore --list'
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process=[Diagnostics.Process]::new();$process.StartInfo=$start
    try{
        if(-not $process.Start()){throw 'Could not start offline archive reader'}
        $outputTask=$process.StandardOutput.ReadToEndAsync()
        $errorTask=$process.StandardError.ReadToEndAsync()
        $process.StandardInput.BaseStream.Write($recoveredArchive,0,$recoveredArchive.Length)
        $process.StandardInput.Close()
        if(-not $process.WaitForExit(30000)){$process.Kill();throw 'Offline archive reader timed out'}
        $toc=$outputTask.GetAwaiter().GetResult()
        $null=$errorTask.GetAwaiter().GetResult()
        if($process.ExitCode -ne 0){throw 'Offline archive reader failed; no private output displayed'}
    }finally{$process.Dispose()}
    $entries=@($toc -split '\r?\n' | Where-Object {$_ -match '^\d+; '})
    $extensions=@($entries | ForEach-Object {if($_ -match '^\d+; \d+ \d+ EXTENSION - ([^ ]+) '){$Matches[1]}} | Sort-Object -Unique)
    $schemas=@($entries | ForEach-Object {if($_ -match '^\d+; \d+ \d+ SCHEMA - ([^ ]+) '){$Matches[1]}} | Sort-Object -Unique)
    $requiredData=[ordered]@{}
    foreach($table in @('public.shared_inspections','public.personal_inspections','public.staff_members','public.staff_access_requests','public.defectrag_gallery_entries','auth.users','auth.mfa_factors','storage.buckets','storage.objects')){
        $parts=$table.Split('.')
        $pattern='^\d+; \d+ \d+ TABLE DATA '+[regex]::Escape($parts[0])+' '+[regex]::Escape($parts[1])+' '
        $requiredData[$table]=@($entries | Where-Object {$_ -match $pattern}).Count -eq 1
    }
    [ordered]@{
        status='encrypted_export_readable_not_restore_verified';project=$manifest.project;
        encrypted_file_checksums_ok=$true;both_exports_decrypted_in_current_profile=$true;
        custom_archive_readable=$true;archive_entries=$entries.Count;
        table_data_entries=@($entries | Where-Object {$_ -match ' TABLE DATA '}).Count;
        policy_entries=@($entries | Where-Object {$_ -match ' POLICY '}).Count;
        extensions=$extensions;schemas=$schemas;table_data_present=$requiredData;
        network='none';sql_executed=$false;plaintext_files_created=$false;
        storage_object_bytes_verified=$false;native_mfa_recovery_verified=$false;
        isolated_restore_verified=$false
    } | ConvertTo-Json -Depth 5
}finally{
    if($recoveredArchive){[Array]::Clear($recoveredArchive,0,$recoveredArchive.Length)}
}
