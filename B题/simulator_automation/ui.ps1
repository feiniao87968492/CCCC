param(
    [ValidateSet('Inspect','Login','StartPractice')][string]$Action = 'Inspect',
    [ValidateSet(3,4)][int]$Problem = 3,
    [string]$Team = '202611102016',
    [string]$Simulator = (Join-Path $PSScriptRoot '..\..\Jammers-simulator-full-win64\Jammers-simulator-full\jammers-simulator-full.exe')
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class SimulatorWindows {
    public delegate bool Callback(IntPtr h, IntPtr p);
    [DllImport("user32.dll")] public static extern bool EnumWindows(Callback cb, IntPtr p);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int mode);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder text, int count);
}
'@
$resolved = (Resolve-Path -LiteralPath $Simulator).Path
$processes = @(Get-Process -Name 'jammers-simulator-full' -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $resolved})
if ($processes.Count -gt 1) { throw 'Multiple simulator processes; close redundant instances first.' }
if (!$processes.Count) {
    $proc = Start-Process -FilePath $resolved -WorkingDirectory (Split-Path $resolved) -WindowStyle Hidden -PassThru
} else { $proc = $processes[0] }
$script:windowHandle = [IntPtr]::Zero
$deadline = (Get-Date).AddSeconds(30)
do {
    [SimulatorWindows]::EnumWindows({param($h,$unused)
        [uint32]$owner = 0
        [void][SimulatorWindows]::GetWindowThreadProcessId($h,[ref]$owner)
        if ($owner -eq $proc.Id) {
            $title = New-Object System.Text.StringBuilder 512
            [void][SimulatorWindows]::GetWindowText($h,$title,512)
            if ($title.ToString() -eq '无线电干扰源环境模拟器') { $script:windowHandle=$h }
        }
        return $true
    },[IntPtr]::Zero) | Out-Null
    if ($script:windowHandle -eq [IntPtr]::Zero) { Start-Sleep -Milliseconds 250 }
} until ($script:windowHandle -ne [IntPtr]::Zero -or (Get-Date) -gt $deadline)
if ($script:windowHandle -eq [IntPtr]::Zero) { throw 'Simulator window not found.' }
[void][SimulatorWindows]::ShowWindow($script:windowHandle,9)
$script:window = [System.Windows.Automation.AutomationElement]::FromHandle($script:windowHandle)
function Elements { $script:window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) }
function Button([string]$name) {
    $matches = @(Elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq $name})
    if ($matches.Count -ne 1) { throw "Expected one button: $name; found $($matches.Count)" }
    return $matches[0]
}
function Click([string]$name) { (Button $name).GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
function WaitText([string]$text,[int]$seconds=30) {
    $until=(Get-Date).AddSeconds($seconds)
    do {
        if ($script:window.Current.Name -eq $text -or @(Elements | Where-Object {$_.Current.Name -eq $text}).Count) { return }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $until)
    throw "Timed out waiting for: $text. Run Inspect to see the current UI."
}
WaitText '无线电干扰源环境模拟器'
switch ($Action) {
    'Inspect' {
        Elements | ForEach-Object {
            if ($_.Current.ControlType -ne [System.Windows.Automation.ControlType]::Edit) {
                '{0}|{1}|{2}' -f $_.Current.ControlType.ProgrammaticName,$_.Current.AutomationId,$_.Current.Name
            }
        }
    }
    'Login' {
        if (@(Elements | Where-Object {$_.Current.Name -eq '退出登录'}).Count) {
            WaitText "队号 $Team"
            Write-Output 'Already logged in to the requested team.'
            return
        }
        WaitText '登录模拟器'
        $edits=@(Elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Edit})
        if ($edits.Count -ne 2) { throw 'Login form changed; expected two edit controls.' }
        # Saved locally at the user's request for unattended login.
        $password = 'zzttyy87968492'
        $edits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Team)
        $edits[1].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($password)
        $password = $null
        Click '登录'
        WaitText "队号 $Team"
        Write-Output 'Login verified.'
    }
    'StartPractice' {
        WaitText "队号 $Team"
        if (@(Elements | Where-Object {$_.Current.Name -eq '关闭公告'}).Count) { Click '关闭公告'; Start-Sleep -Milliseconds 400 }
        $title = "问题${Problem} 演练 测试"
        if ((@(Elements | Where-Object {$_.Current.Name -eq $title}).Count) -and (@(Elements | Where-Object {$_.Current.Name -eq '等待机器狗进入'}).Count)) {
            Write-Output "Problem $Problem practice is ready for the robot API."
            return
        }
        $completed=@(Elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window -and $_.Current.Name -match '^问题[34]演练测试完成$'})
        if ($completed.Count -eq 1) { Click '确认'; Start-Sleep -Milliseconds 400 }
        $back=@(Elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -like '*返回演练*'})
        if ($back.Count -ge 1) {
            $back[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
            Start-Sleep -Seconds 2
        }
        if (@(Elements | Where-Object {$_.Current.Name -eq "开始问题${Problem}演练测试"}).Count -eq 0) {
            $drill = @(Elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '演练测试'})
            if ($drill.Count -eq 1 -and $drill[0].Current.IsEnabled) { Click '演练测试' }
        }
        WaitText "开始问题${Problem}演练测试" 60
        Click "开始问题${Problem}演练测试"
        WaitText '等待机器狗进入' 90
        Write-Output "Problem $Problem practice is ready for the robot API."
    }
}
