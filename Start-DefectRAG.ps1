param([switch]$Setup,[switch]$NoBrowser,[switch]$Verify,[int]$Port=8765,[string]$PythonPath='')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$env:USE_TF='0'
$localDeps=Join-Path $PSScriptRoot '.python-deps'
if (Test-Path -LiteralPath $localDeps) { $env:PYTHONPATH=$localDeps }
$pythonExe=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($PythonPath) { $pythonExe=$PythonPath }
if (-not (Test-Path -LiteralPath $pythonExe)) {
  if (-not $Setup) { throw 'First run: .\Start-DefectRAG.ps1 -Setup. This installs dependencies into a separate venv.' }
  & py -3.11 -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required for automatic setup. Install Python or pass -PythonPath to an existing compatible environment.' }
}
if ($Setup) {
  & $pythonExe -m pip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed. Check your network and Python version.' }
}
if (-not (Test-Path -LiteralPath 'models\encoder\model.safetensors') -and -not (Test-Path -LiteralPath 'models\encoder_dinov2\model.safetensors')) { throw 'Encoder asset missing. See README asset setup.' }
if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) {
  & npm.cmd ci --prefix frontend --no-audit --no-fund
  if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed' }
  & npm.cmd run build --prefix frontend
  if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
}
if ($Verify) {
  & $pythonExe -m scripts.verify_startup
  if ($LASTEXITCODE -ne 0) { throw 'Startup validation failed' }
  exit 0
}
Write-Host "DefectRAG: http://127.0.0.1:$Port"
Write-Host 'For generated answers, run Ollama with qwen2.5:3b. Retrieval fallback remains available.'
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$Port" }
& $pythonExe -m uvicorn backend.main:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
