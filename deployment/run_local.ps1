$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$listeners=@(Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue)
if($listeners.Count){
    $health=$null
    try{$health=Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 3}catch{}
    if($health.data.status -eq 'ok' -and $health.data.mode -eq 'local_single_user' -and $health.data.local_sync_enabled -eq $true){
        Write-Host 'DefectRAG is already running. Open http://127.0.0.1:8765 (no second server was started).'
        Write-Host 'To restart after an update, press Ctrl+C in the original server terminal, then run this launcher again.'
        return
    }
    $listenerIds=($listeners.OwningProcess | Sort-Object -Unique) -join ', '
    throw "Port 8765 is already occupied (process $listenerIds). Stop the existing service in its own terminal before starting DefectRAG. No process was stopped automatically."
}
$python=Join-Path $projectRoot '.venv/Scripts/python.exe'
if(-not (Test-Path -LiteralPath $python)){throw 'The project Python environment is missing. Restore the existing environment before starting.'}
& $python -m backend.local_frontend
if($LASTEXITCODE -ne 0){
    $dist=Join-Path $projectRoot 'frontend/dist'
    if(Test-Path -LiteralPath $dist){
        $backup=Join-Path $projectRoot ('runtime/frontend-backups/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
        New-Item -ItemType Directory -Path $backup | Out-Null
        Copy-Item -LiteralPath $dist -Destination (Join-Path $backup 'dist') -Recurse
        Write-Host "Existing dashboard backed up to $backup"
    }
    & npm.cmd --prefix frontend run build
    if($LASTEXITCODE -ne 0){throw 'Dashboard build failed. Existing history and the previous build backup are retained.'}
    & $python -m backend.local_frontend
    if($LASTEXITCODE -ne 0){throw 'Dashboard verification failed; server was not started.'}
}
$env:DEFECTRAG_LOCAL_SYNC='1'
Write-Host 'Open http://127.0.0.1:8765 and complete Staff sign-in/MFA for private synchronization.'
& $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --workers 1
