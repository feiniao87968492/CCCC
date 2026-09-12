param(
    [int]$Rounds = 10
)
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
$log = Join-Path $here '..\experiments\q3_simulator\batch30.log'
"batch start $(Get-Date -Format o)" | Set-Content -LiteralPath $log -Encoding utf8
$strats = @('GREEDY', 'GREEDY_FAST', 'GREEDY_ABORT')
foreach ($s in $strats) {
    for ($i = 1; $i -le $Rounds; $i++) {
        $msg = "=== $s $i/$Rounds $(Get-Date -Format HH:mm:ss) ==="
        $msg | Tee-Object -FilePath $log -Append
        Start-Sleep -Seconds 10
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'run_q3_practice.ps1') -Strategy $s
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            "FAIL $s $i exit=$code; retry after 12s" | Tee-Object -FilePath $log -Append
            Start-Sleep -Seconds 12
            & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'run_q3_practice.ps1') -Strategy $s
            $code = $LASTEXITCODE
        }
        "done $s $i exit=$code" | Tee-Object -FilePath $log -Append
    }
}
"batch end $(Get-Date -Format o)" | Tee-Object -FilePath $log -Append
if ($code -ne 0) { exit $code }
exit 0
