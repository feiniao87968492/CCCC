param([ValidateSet(3,4)][int]$Problem=3, [string]$Team='202611102016', [int]$Port=2026)
$ErrorActionPreference='Stop'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'ui.ps1') -Action Login -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Login failed.' }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'ui.ps1') -Action StartPractice -Problem $Problem -Team $Team
if ($LASTEXITCODE -ne 0) { throw 'Practice did not become ready.' }
& python (Join-Path $PSScriptRoot 'smoke.py') --problem $Problem --team $Team --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Smoke test failed. Inspect the simulator before starting another test.' }
