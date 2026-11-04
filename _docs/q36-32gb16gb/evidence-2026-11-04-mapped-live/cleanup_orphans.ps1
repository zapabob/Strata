$ErrorActionPreference = 'Continue'
$targets = @(4024, 28188, 22204)
$killed = @()

foreach ($procId in $targets) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue
    if (-not $p) {
        Write-Host "PID $procId already gone"
        $killed += [pscustomobject]@{ Pid = $procId; Status = 'already_gone' }
        continue
    }

    $cmd = if ($p.CommandLine) { $p.CommandLine } else { '' }
    $snip = if ($cmd.Length -gt 180) { $cmd.Substring(0, 180) } else { $cmd }
    Write-Host "KILLING PID=$procId Name=$($p.Name)"
    Write-Host "CMD=$cmd"

    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800
    $still = Get-Process -Id $procId -ErrorAction SilentlyContinue
    $status = 'killed'
    if ($still) {
        & taskkill.exe /F /PID $procId 2>&1 | Out-Host
        Start-Sleep -Milliseconds 800
        $still2 = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($still2) { $status = 'FAILED' } else { $status = 'killed_via_taskkill' }
    }

    $killed += [pscustomobject]@{
        Pid = $procId
        Name = $p.Name
        Status = $status
        CmdSnippet = $snip
    }
}

Write-Host '===KILLED==='
$killed | ConvertTo-Json -Depth 3
$killed | ConvertTo-Json -Depth 3 | Set-Content -Encoding utf8 -Path (Join-Path $PSScriptRoot 'cleanup-killed-pids.json')

Start-Sleep -Seconds 4

Write-Host '===POST strata==='
$s = Get-CimInstance Win32_Process -Filter "Name = 'strata.exe'"
if ($s) {
    $s | Select-Object ProcessId, CommandLine | Format-List
} else {
    Write-Host 'no strata.exe'
}

Write-Host '===POST babysitters==='
$b = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -match 't03_launch2|launch_mapped_live|q36-expert-store mapped-pack|qwen36-UD-Q4'
    )
}
if ($b) {
    $b | Select-Object ProcessId, Name, CommandLine | Format-List
} else {
    Write-Host 'no orphan babysitters'
}

Write-Host '===NVIDIA==='
nvidia-smi --query-gpu=memory.used,memory.free,memory.total,utilization.gpu --format=csv
