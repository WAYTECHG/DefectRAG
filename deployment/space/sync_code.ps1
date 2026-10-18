$ErrorActionPreference='Stop'
$spaceSource=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$spaceDesktop='C:\Users\User\Desktop\DefectRAG-v2'
$spacePreserve=@('frontend/public/config.js','deployment/RUN_AND_DEPLOY.md')
$spaceHashes=@{}
foreach($relative in $spacePreserve){$spaceHashes[$relative]=(Get-FileHash -LiteralPath (Join-Path $spaceDesktop $relative)).Hash}
git -C $spaceDesktop fetch $spaceSource main
if($LASTEXITCODE -ne 0){throw 'Fetch failed'}
git -C $spaceDesktop merge --ff-only FETCH_HEAD
if($LASTEXITCODE -ne 0){throw 'Merge refused; inspect and preserve current work'}
foreach($relative in $spacePreserve){if((Get-FileHash -LiteralPath (Join-Path $spaceDesktop $relative)).Hash -ne $spaceHashes[$relative]){throw "Preservation check failed: $relative"}}
$spaceDestination=Join-Path $spaceDesktop 'development-support/space'
New-Item -ItemType Directory -Force -Path $spaceDestination | Out-Null
foreach($file in Get-ChildItem -LiteralPath (Join-Path $spaceSource 'development-support/space') -File){
    if($file.Extension -in @('.json','.xml','.log','.png')){Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $spaceDestination $file.Name)}
}
$spaceReceipt=@{status='passed';head=(git -C $spaceDesktop rev-parse HEAD);preserved_hashes=$spaceHashes;no_models_or_datasets_copied=$true}
$spaceReceipt | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $spaceDestination 'desktop-checkpoint.json') -Encoding utf8
git -C $spaceDesktop status --short
Write-Output 'Code and small evidence checkpoint synchronized; existing configuration and guide hashes unchanged.'
