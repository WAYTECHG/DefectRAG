param(
    [string]$RepositoryPath,
    [switch]$PrepareOnly
)
$ErrorActionPreference='Stop'
$updateSource=Split-Path $PSScriptRoot -Parent
if(-not $RepositoryPath){$RepositoryPath=Join-Path $updateSource 'development-support/github-ready/DefectRAG'}
$updateRepository=[IO.Path]::GetFullPath($RepositoryPath)
if(-not (Test-Path -LiteralPath (Join-Path $updateRepository '.git'))){throw 'Choose the existing GitHub checkout with -RepositoryPath. No repository was created.'}
$actualRoot=& git -C $updateRepository rev-parse --show-toplevel
if($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($actualRoot).TrimEnd('\','/') -ne $updateRepository.TrimEnd('\','/')){throw 'RepositoryPath must be the repository root.'}
$updateRemote=& git -C $updateRepository remote get-url origin
if($LASTEXITCODE -ne 0 -or $updateRemote -notmatch '(?i)github\.com[:/]WAYTECHG/DefectRAG(?:\.git)?/?$'){throw 'Expected origin WAYTECHG/DefectRAG. No remote was changed.'}
$alreadyStaged=& git -C $updateRepository diff --cached --name-only
if($LASTEXITCODE -ne 0 -or $alreadyStaged){throw 'Commit or unstage the existing staged changes before running this update. They were preserved.'}
$updateFiles=@(Get-Content -LiteralPath (Join-Path $updateSource 'docs/WORKFLOW_UPDATE_FILES.txt') | Where-Object {$_ -and -not $_.StartsWith('#')})
function Test-UpdateContent([string]$source,[string]$target){
    if((Get-FileHash -LiteralPath $source).Hash -eq (Get-FileHash -LiteralPath $target).Hash){return $true}
    if([IO.Path]::GetExtension($source) -eq '.png'){return $false}
    # Git may check out CRLF on Windows; an EOL-only difference is not a user edit.
    return ([IO.File]::ReadAllText($source).Replace("`r`n","`n") -ceq [IO.File]::ReadAllText($target).Replace("`r`n","`n"))
}
# Validate every path and local edit before copying any file.
foreach($relative in $updateFiles){
    if([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)' -or $relative -match '(?i)(^|/)(\.env|models|runtime|experiments|node_modules|\.venv)(/|$)'){throw "Unexpected update path: $relative"}
    $source=Join-Path $updateSource $relative
    $target=[IO.Path]::GetFullPath((Join-Path $updateRepository $relative))
    if(-not $target.StartsWith($updateRepository.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Target escaped the checkout.'}
    if(-not (Test-Path -LiteralPath $source -PathType Leaf)){throw "Missing source file: $relative"}
    if((Get-Item -LiteralPath $source).Length -gt 2097152){throw "Unexpected large source file: $relative"}
    $changes=& git -C $updateRepository status --porcelain -- $relative
    if($LASTEXITCODE -ne 0){throw 'Could not inspect existing edits.'}
    if($changes -and (Test-Path -LiteralPath $target) -and -not (Test-UpdateContent $source $target)){throw "Existing edits preserved: $relative. Reconcile that file before updating."}
}
foreach($relative in $updateFiles){
    $source=Join-Path $updateSource $relative;$target=Join-Path $updateRepository $relative
    if([IO.Path]::GetFullPath($source) -eq [IO.Path]::GetFullPath($target)){continue}
    New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
}
if(-not $PrepareOnly){
    & git -C $updateRepository add -- @updateFiles
    if($LASTEXITCODE -ne 0){throw 'Git staging failed. No commit or push was attempted.'}
    & git -C $updateRepository diff --cached --stat
}
Write-Output "Prepared $($updateFiles.Count) source/documentation files in $updateRepository"
Write-Output 'Models, datasets, environments, public configuration, private history and existing Git history were preserved.'
Write-Output 'No GitHub push was performed. Review the changes, then commit and push using the guide.'
