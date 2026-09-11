param(
    [string]$Team = '202611102016',
    [int]$Port = 2026
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'ui.ps1') -Action Login -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Login failed.' }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'ui.ps1') -Action StartPractice -Problem 4 -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Problem 4 practice did not become ready. Refusing to send API.' }
& python (Join-Path $here 'q4_practice.py') --team $Team --port $Port --skip-ui-start
if ($LASTEXITCODE -ne 0) { throw 'Q4 practice runner failed.' }
