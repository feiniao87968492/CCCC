param(
    [ValidateSet('SAFE','FAST','HYBRID','ROBUST','GREEDY','GREEDY_FAST','GREEDY_ABORT')][string]$Strategy = 'SAFE',
    [string]$Team = '202611102016',
    [int]$Port = 2026,
    [ValidateRange(0,360000)][double]$SourceBudgetS = 0
)
$ErrorActionPreference = 'Stop'
if ($SourceBudgetS -gt 0 -and $Strategy -ne 'GREEDY_FAST') { throw 'SourceBudgetS requires GREEDY_FAST.' }
$here = $PSScriptRoot
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'ui.ps1') -Action Login -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Login failed.' }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'ui.ps1') -Action StartPractice -Problem 3 -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Practice did not become ready. Refusing to send API.' }
& python (Join-Path $here 'q3_practice.py') --strategy $Strategy --source-budget-s $SourceBudgetS --team $Team --port $Port --skip-ui-start
if ($LASTEXITCODE -ne 0) { throw 'Q3 practice runner failed.' }
