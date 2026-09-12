param(
    [int]$Rounds = 20,
    [int]$StartFrom = 1
)
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
$outDir = Join-Path $here '..\experiments\q3_simulator'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$log = Join-Path $outDir 'batch_jso20.log'
"batch JSO practice start $(Get-Date -Format o) rounds=$Rounds start=$StartFrom" | Tee-Object -FilePath $log -Append
$fail = 0
for ($i = $StartFrom; $i -le $Rounds; $i++) {
    $msg = "=== JSO $i/$Rounds $(Get-Date -Format HH:mm:ss) ==="
    $msg | Tee-Object -FilePath $log -Append
    if ($i -gt $StartFrom) { Start-Sleep -Seconds 15 }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'run_q3_practice.ps1') -Strategy JSO
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        "FAIL JSO $i exit=$code; retry after 12s" | Tee-Object -FilePath $log -Append
        Start-Sleep -Seconds 12
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'run_q3_practice.ps1') -Strategy JSO
        $code = $LASTEXITCODE
    }
    if ($code -ne 0) { $fail++ }
    "done JSO $i exit=$code" | Tee-Object -FilePath $log -Append
}
"batch JSO practice end $(Get-Date -Format o) fail=$fail" | Tee-Object -FilePath $log -Append
if ($fail -gt 0) { exit 1 }
exit 0
