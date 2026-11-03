# Finds the Python interpreter for this project. No side effects when dot-sourced.
# Order: DEFECTRAG_PYTHON, the project .venv, the active conda env named
# "defectrag", then the default Anaconda location of that env.
function Get-ProjectPython{
    $root=Split-Path $PSScriptRoot -Parent
    $candidates=@()
    if($env:DEFECTRAG_PYTHON){$candidates+=$env:DEFECTRAG_PYTHON}
    $candidates+=(Join-Path $root '.venv\Scripts\python.exe')
    if($env:CONDA_PREFIX -and (Split-Path $env:CONDA_PREFIX -Leaf) -eq 'defectrag'){$candidates+=(Join-Path $env:CONDA_PREFIX 'python.exe')}
    foreach($base in @('anaconda3','miniconda3')){$candidates+=(Join-Path $env:USERPROFILE "$base\envs\defectrag\python.exe")}
    foreach($candidate in $candidates){if($candidate -and (Test-Path -LiteralPath $candidate)){return $candidate}}
    throw 'No project Python found. Run: conda activate defectrag (see README, "Development machine (conda)"), or set DEFECTRAG_PYTHON to a python.exe.'
}
