# Owner-run private backup supplement. READ requests only; no key/role/settings
# changes, emails or uploads. PAT is entered hidden and never saved. Root key,
# bucket definitions, paths/metadata and object bytes are DPAPI-encrypted.
param([string]$BackupDirectory,[switch]$ValidateOnly)
$ErrorActionPreference='Stop'
try{Add-Type -AssemblyName System.Security.Cryptography.ProtectedData -ErrorAction Stop}
catch{Add-Type -AssemblyName System.Security -ErrorAction Stop}
Add-Type -AssemblyName System.Net.Http
$projectRef='zrzqpbcomlorfzszolrs'
$managementBase='https://api.supabase.com/v1/projects/'+$projectRef
$storageBase='https://'+$projectRef+'.supabase.co/storage/v1'
$maximumTotalBytes=256MB
$totalBytes=[int64]0
$http=$null;$handler=$null;$token=$null;$serviceKey=$null;$requestCount=0

function New-OwnerOnlyFolder([string]$Path){
    if(Test-Path -LiteralPath $Path){throw 'Refusing to overwrite an existing recovery folder'}
    New-Item -ItemType Directory -Path $Path | Out-Null
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl=[Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner($sid);$acl.SetAccessRuleProtection($true,$false)
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
    Set-Acl -LiteralPath $Path -AclObject $acl
}

function Protect-PrivateBytes([string]$Name,[byte[]]$Bytes){
    if($Name -notmatch '^[a-z0-9.-]+\.dpapi$'){throw 'Invalid local encrypted filename'}
    $path=Join-Path $recoveryFolder $Name
    if(Test-Path -LiteralPath $path){throw 'Refusing to overwrite existing recovery data'}
    $cipher=[Security.Cryptography.ProtectedData]::Protect($Bytes,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    [IO.File]::WriteAllBytes($path,$cipher)
    $roundtrip=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($path),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    $sha=[Security.Cryptography.SHA256]::Create()
    try{
        if([Convert]::ToBase64String($sha.ComputeHash($Bytes)) -ne [Convert]::ToBase64String($sha.ComputeHash($roundtrip))){throw 'Encrypted recovery-material readback mismatch'}
    }finally{$sha.Dispose();[Array]::Clear($roundtrip,0,$roundtrip.Length)}
    return @{file=$Name;bytes=$cipher.Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
}

function Read-RecoveryResource([string]$Method,[string]$Uri,[string]$Body=''){
    $managementRead=$Method -eq 'GET' -and ($Uri -ceq ($managementBase+'/pgsodium') -or $Uri -ceq ($managementBase+'/api-keys?reveal=true'))
    $storageRead=($Method -eq 'GET' -and ($Uri -ceq ($storageBase+'/bucket') -or $Uri.StartsWith($storageBase+'/object/',[StringComparison]::Ordinal))) -or ($Method -eq 'POST' -and $Uri.StartsWith($storageBase+'/object/list/',[StringComparison]::Ordinal))
    if(-not($managementRead -or $storageRead)){throw 'Refused an unexpected destination or non-backup API operation'}
    if($script:requestCount -ge 1000){throw 'Read request safety limit reached'}
    $script:requestCount++
    if($ValidateOnly){
        if($Uri -ceq ($managementBase+'/pgsodium')){$fixture=@{root_key=('a'*64)} | ConvertTo-Json -Compress}
        elseif($Uri -ceq ($managementBase+'/api-keys?reveal=true')){$fixture='[{"name":"service_role","api_key":"OFFLINE-FIXTURE-ONLY"}]'}
        elseif($Uri -ceq ($storageBase+'/bucket')){$fixture='[{"id":"fixture-bucket","name":"fixture-bucket","public":false}]'}
        elseif($Method -eq 'POST'){
            $listing=$Body | ConvertFrom-Json
            if($listing.prefix -eq ''){$fixture='[{"name":"folder","id":null}]'}
            elseif($listing.prefix -eq 'folder/'){$fixture='[{"name":"image.bin","id":"fixture-id","metadata":{"size":4}}]'}
            else{throw 'Unexpected fixture prefix'}
        }else{return ,([byte[]]@(0,1,2,3))}
        return ,([Text.Encoding]::UTF8.GetBytes($fixture))
    }
    $request=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::new($Method),$Uri)
    $response=$null
    try{
        $authValue=if($managementRead){$token}else{$serviceKey}
        $request.Headers.Authorization=[Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$authValue)
        if($storageRead){$request.Headers.Add('apikey',$serviceKey)}
        if($Method -eq 'POST'){$request.Content=[Net.Http.StringContent]::new($Body,[Text.Encoding]::UTF8,'application/json')}
        $response=$http.SendAsync($request,[Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        if(-not $response.IsSuccessStatusCode){throw ('Read-only recovery request failed (HTTP '+[int]$response.StatusCode+'). No settings were changed; do not disclose the token.')}
        if($response.Content.Headers.ContentLength -and $response.Content.Headers.ContentLength -gt $maximumTotalBytes){throw 'Object exceeds the private-backup byte safety limit'}
        $buffer=$response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
        return ,$buffer
    }catch{
        # Do not forward HTTP exception data, headers, URI paths or bodies.
        if($_.Exception.Message.StartsWith('Read-only recovery request failed (HTTP ')){throw $_.Exception.Message}
        throw 'Private backup read failed; no response body, credential or private path was displayed. No production settings were changed.'
    }finally{if($response){$response.Dispose()};$request.Dispose()}
}

function Read-PrivateJson([string]$Method,[string]$Uri,[string]$Body=''){
    $bytes=Read-RecoveryResource $Method $Uri $Body
    try{return (ConvertFrom-Json -InputObject ([Text.Encoding]::UTF8.GetString($bytes)))}
    catch{throw 'Unexpected private JSON response; no response body displayed'}
    finally{[Array]::Clear($bytes,0,$bytes.Length)}
}

if($ValidateOnly){
    $base=Join-Path (Split-Path $PSScriptRoot -Parent) 'runtime\recovery-export-validation'
}else{
    if(-not $BackupDirectory){throw 'Supply the existing completed backup DIRECTORY, never a password or token'}
    $base=(Resolve-Path -LiteralPath $BackupDirectory).Path
    $original=Get-Content -LiteralPath (Join-Path $base 'manifest.json') -Raw | ConvertFrom-Json
    if($original.project -ne $projectRef -or $original.status -ne 'exported_not_restore_verified'){throw 'Expected the completed backup for this project'}
    if(-not (Get-Acl -LiteralPath $base).AreAccessRulesProtected){throw 'Expected the private owner-protected backup folder'}
}
$recoveryFolder=Join-Path $base ('recovery-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
New-OwnerOnlyFolder $recoveryFolder
$summary=[ordered]@{project=$projectRef;status='incomplete';offline_fixture=[bool]$ValidateOnly;started_utc=[DateTime]::UtcNow.ToString('o');pat_saved=$false;service_key_saved=$false;root_key_changed=$false;storage_objects=0;plaintext_object_bytes=0;encrypted_files=@();same_windows_profile_required=$true;source_snapshot_atomic=$false;native_mfa_recovery_verified=$false;complete_recovery_verified=$false}
try{
    if(-not $ValidateOnly){
        Write-Host 'Enter your saved Supabase PERSONAL ACCESS TOKEN privately. It will not echo or be saved.'
        Write-Host 'This reads existing recovery material and Storage files only. It never resets keys or changes settings.'
        $secureToken=Read-Host 'Supabase account token' -AsSecureString
        $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
        try{$token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)}
        finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer);$secureToken.Dispose()}
        if([string]::IsNullOrWhiteSpace($token)){throw 'No token entered; nothing requested'}
        $handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false
        $http=[Net.Http.HttpClient]::new($handler);$http.Timeout=[TimeSpan]::FromSeconds(45)
        $http.MaxResponseContentBufferSize=$maximumTotalBytes
    }
    $root=Read-PrivateJson 'GET' ($managementBase+'/pgsodium')
    if($root.root_key -notmatch '^[0-9a-fA-F]{64}$'){throw 'Unexpected recovery-key response; stop without displaying it'}
    $keyBytes=[Text.Encoding]::UTF8.GetBytes($root.root_key)
    try{$summary.encrypted_files+=Protect-PrivateBytes 'root-key.dpapi' $keyBytes}
    finally{[Array]::Clear($keyBytes,0,$keyBytes.Length);$root=$null}
    $keys=@(Read-PrivateJson 'GET' ($managementBase+'/api-keys?reveal=true'))
    $legacy=@($keys | Where-Object {($_.name -eq 'service_role' -or $_.id -eq 'service_role') -and $_.api_key})
    if($legacy.Count -ne 1){throw 'Existing service-role key unavailable to this token; no API key will be created or changed'}
    $serviceKey=[string]$legacy[0].api_key;$keys=$null;$legacy=$null
    $buckets=@(Read-PrivateJson 'GET' ($storageBase+'/bucket'))
    $objects=@();$seen=@{};$bucketCounts=[ordered]@{}
    foreach($bucket in $buckets){
        $bucketId=[string]$bucket.id
        if(-not $bucketId){throw 'Missing bucket identifier'}
        $encodedBucket=[Uri]::EscapeDataString($bucketId)
        $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue('')
        $seenFolders=@{};$bucketCounts[$bucketId]=0
        while($queue.Count){
            $prefix=$queue.Dequeue()
            if($seenFolders.ContainsKey($prefix)){throw 'Repeated Storage folder; stop rather than loop'}
            $seenFolders[$prefix]=$true;$offset=0
            do{
                $body=@{prefix=$prefix;limit=100;offset=$offset;sortBy=@{column='name';order='asc'}} | ConvertTo-Json -Compress
                $page=@(Read-PrivateJson 'POST' ($storageBase+'/object/list/'+$encodedBucket) $body)
                foreach($object in $page){
                    if(-not $object.name -or $object.name -match '(^|/)\.\.?(/|$)'){throw 'Unsafe or missing object name'}
                    $objectPath=$prefix+[string]$object.name
                    if(-not $object.id){$queue.Enqueue($objectPath+'/');continue}
                    $identity=$bucketId+':'+$objectPath
                    if($seen.ContainsKey($identity)){throw 'Duplicate Storage listing; no duplicate file will be saved'}
                    $seen[$identity]=$true
                    if($object.metadata.size -and ($totalBytes+[int64]$object.metadata.size) -gt $maximumTotalBytes){throw 'Storage backup exceeds 256MiB safety cap; stop for review without changing the project'}
                    $encodedPath=(($objectPath -split '/') | ForEach-Object {[Uri]::EscapeDataString($_)}) -join '/'
                    $bytes=Read-RecoveryResource 'GET' ($storageBase+'/object/'+$encodedBucket+'/'+$encodedPath)
                    try{
                        $totalBytes+=$bytes.Length
                        if($totalBytes -gt $maximumTotalBytes){throw 'Storage backup exceeds 256MiB safety cap'}
                        if($null -ne $object.metadata.size -and [int64]$object.metadata.size -ne $bytes.Length){throw 'Storage metadata/byte-length mismatch; no complete recovery claim'}
                        $fileName=('object-{0:D6}.dpapi' -f ($objects.Count+1))
                        $entry=Protect-PrivateBytes $fileName $bytes
                        $summary.encrypted_files+=$entry
                        $sha=[Security.Cryptography.SHA256]::Create()
                        try{$plainHash=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
                        $objects+=@{bucket=$bucketId;path=$objectPath;metadata=$object;file=$fileName;plaintext_bytes=$bytes.Length;plaintext_sha256=$plainHash}
                        $bucketCounts[$bucketId]++
                    }finally{[Array]::Clear($bytes,0,$bytes.Length)}
                }
                $offset+=100
            }while($page.Count -eq 100)
        }
    }
    $privateInventory=@{project=$projectRef;buckets=$buckets;objects=$objects;bucket_counts=$bucketCounts} | ConvertTo-Json -Depth 20 -Compress
    $inventoryBytes=[Text.Encoding]::UTF8.GetBytes($privateInventory)
    try{$summary.encrypted_files+=Protect-PrivateBytes 'storage-inventory.dpapi' $inventoryBytes}
    finally{[Array]::Clear($inventoryBytes,0,$inventoryBytes.Length);$privateInventory=$null}
    if($ValidateOnly){
        foreach($denied in @(@('PUT',($managementBase+'/pgsodium')),@('DELETE',($storageBase+'/object/fixture-bucket/image.bin')),@('GET','https://example.invalid/private'))){
            $blocked=$false;$before=$script:requestCount
            try{$null=Read-RecoveryResource $denied[0] $denied[1]}catch{$blocked=$true}
            if(-not $blocked -or $script:requestCount -ne $before){throw 'Offline read-only destination/method guard failed'}
        }
        $blocked=$false
        try{$null=Protect-PrivateBytes 'root-key.dpapi' ([byte[]]@(0))}catch{$blocked=$true}
        if(-not $blocked -or $http){throw 'Offline overwrite/no-network guard failed'}
        $summary.offline_safety_guards_passed=$true
    }
    $summary.storage_objects=$objects.Count;$summary.plaintext_object_bytes=$totalBytes
    $summary.status='encrypted_recovery_material_exported_not_full_restore_verified'
    Write-Host ('Recovery key and '+$objects.Count+' Storage files encrypted and read back successfully.')
    Write-Host 'Do not migrate yet. Cross-check against the database snapshot and native recovery remains necessary.'
}catch{
    $summary.status='failed_or_incomplete'
    throw
}finally{
    $token=$null;$serviceKey=$null;$keys=$null;$root=$null
    if($http){$http.Dispose()};if($handler){$handler.Dispose()}
    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $recoveryFolder 'recovery_manifest.json') -Encoding utf8
    Write-Host ('Private recovery directory: '+$recoveryFolder)
}
