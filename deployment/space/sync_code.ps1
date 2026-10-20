param([string]$DesktopPath='C:\Users\User\Desktop\DefectRAG-v2',[string]$SourceRef='',[string]$SourcePath='',[switch]$SyncFrontend)
$ErrorActionPreference='Stop'
$spaceSource=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if($SourcePath){$spaceSource=(Resolve-Path -LiteralPath $SourcePath).Path}
if(git -C $spaceSource status --porcelain --untracked-files=no){throw 'Commit source changes before synchronizing'}
$spaceDesktop=(Resolve-Path -LiteralPath $DesktopPath).Path
if($SyncFrontend){throw 'Working builds are preserved. Build/verify/stage explicitly with frontend_release.mjs instead.'}
if(-not $SourceRef){$SourceRef=(git -C $spaceSource branch --show-current).Trim()}
$spaceCommit=(git -C $spaceSource rev-parse --verify $SourceRef).Trim()
if($LASTEXITCODE -ne 0){throw 'Source ref does not resolve'}
$spaceBranch=(git -C $spaceSource branch --show-current).Trim()
git check-ref-format --branch $spaceBranch | Out-Null
if($LASTEXITCODE -ne 0){throw 'Use a named source branch'}
$spaceHead=(git -C $spaceDesktop rev-parse HEAD).Trim()
$spaceDirty=@(git -C $spaceDesktop diff HEAD --name-only)
$spacePreserve=@($spaceDirty+@('frontend/public/config.js','deployment/RUN_AND_DEPLOY.md') | Sort-Object -Unique)
$spaceHashes=@{}
foreach($relative in $spacePreserve){
    $file=Join-Path $spaceDesktop $relative
    if(Test-Path -LiteralPath $file -PathType Leaf){$spaceHashes[$relative]=(Get-FileHash -LiteralPath $file).Hash}
}
git -C $spaceDesktop fetch $spaceSource $spaceCommit
if($LASTEXITCODE -ne 0){throw 'Local fetch failed'}
git -C $spaceDesktop merge-base --is-ancestor HEAD FETCH_HEAD
if($LASTEXITCODE -ne 0){throw 'Desktop history diverged. Resolve history without resetting files.'}
$spaceChanged=@(git -C $spaceDesktop diff --name-only HEAD FETCH_HEAD)
$spaceConflicts=@($spaceDirty | Where-Object {$_ -in $spaceChanged})
if($spaceConflicts.Count){throw ('Overlapping Desktop edits preserved; resolve before sync: '+($spaceConflicts -join ', '))}
$spaceCurrentBranch=(git -C $spaceDesktop branch --show-current).Trim()
if($spaceCurrentBranch -ne $spaceBranch){
    git -C $spaceDesktop show-ref --verify --quiet "refs/heads/$spaceBranch"
    if($LASTEXITCODE -eq 0){throw 'Desktop target branch already exists; inspect before switching'}
    git -C $spaceDesktop switch -c $spaceBranch
    if($LASTEXITCODE -ne 0){throw 'Branch switch refused; no forced checkout performed'}
}
git -C $spaceDesktop merge --ff-only FETCH_HEAD
if($LASTEXITCODE -ne 0){throw 'Fast-forward refused; local files remain preserved'}
foreach($relative in $spaceHashes.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $spaceDesktop $relative)).Hash -ne $spaceHashes[$relative]){throw "Preservation check failed: $relative"}
}
$spaceDestination=Join-Path $spaceDesktop 'development-support/space'
New-Item -ItemType Directory -Force -Path $spaceDestination | Out-Null
$spaceReceipt=@{status='passed';source=$spaceCommit;previous_desktop_head=$spaceHead;
    branch=$spaceBranch;head=(git -C $spaceDesktop rev-parse HEAD).Trim();
    synchronized_files=$spaceChanged;preserved_local_hashes=$spaceHashes;
    datasets_models_secrets_records_copied=$false;working_builds_replaced=$false}
$spaceStamp=[DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
$spaceShortCommit=$spaceCommit.Substring(0,12)
$spaceReceiptFile=Join-Path $spaceDestination "desktop-sync-$spaceShortCommit-$spaceStamp.json"
$spaceReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $spaceReceiptFile -Encoding utf8
git -C $spaceDesktop status --short
Write-Output ('Synchronized '+$spaceChanged.Count+' tracked code/document/result files; local edits and untracked files preserved.')
Write-Output ('Preservation receipt: '+$spaceReceiptFile)
