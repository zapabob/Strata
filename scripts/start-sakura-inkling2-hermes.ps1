param(
    [ValidateSet("131k", "98k", "65k", "98k-vramfix")]
    [string]$Context = "131k",
    [int]$Port = 8092,
    [string]$BindHost = "127.0.0.1",
    [double]$LoopExitTol = 0.0,
    [double]$CpuMissPrune = 0.0,
    [int]$PpStageMb = 64,
    [int]$VramReserveMb = 3328,
    [int]$Tier2Floor = 0
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = "C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}

$ConfigPath = Join-Path $RepoRoot "configs\strata-sakura-inkling2-$Context.json"
if (-not (Test-Path $ConfigPath)) {
    throw "Config file not found: $ConfigPath"
}

if ($LoopExitTol -gt 0.0 -or $CpuMissPrune -gt 0.0) {
    $cfg = Get-Content -Raw -Encoding UTF8 $ConfigPath | ConvertFrom-Json
    $argsList = [System.Collections.ArrayList]@($cfg.args)
    if ($LoopExitTol -gt 0.0) {
        [void]$argsList.Add("--loop-exit-tol")
        [void]$argsList.Add($LoopExitTol.ToString([System.Globalization.CultureInfo]::InvariantCulture))
    }
    if ($CpuMissPrune -gt 0.0) {
        [void]$argsList.Add("--cpu-miss-prune")
        [void]$argsList.Add($CpuMissPrune.ToString([System.Globalization.CultureInfo]::InvariantCulture))
    }
    $cfg.args = $argsList
    $TempCfg = Join-Path $env:TEMP "strata-sakura-inkling2-$Context-opt.json"
    $cfg | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $TempCfg
    $ConfigPath = $TempCfg
}

if (-not $env:STRATA_API_KEY) {
    throw "STRATA_API_KEY is not set. Hermes provider 'inkling2' authenticates with key_env: STRATA_API_KEY."
}

$env:PYTHONPATH = "$RepoRoot\terminal;$RepoRoot"
# GPU / pinned-RAM / CPU expert distribution (place_experts in inkling2_engine.cu):
#   GPU VRAM  = looped core layers 6-17 (3x/token) + Fate-zeta outer layers, capped by --expert-vram
#   pinned RAM = $PpStageMb x2 prefill staging buffers (STRATA_PP_STAGE_MB)
#   CPU        = remaining host-resident experts, computed by 5 pinning workers
#   VramReserveMb keeps WDDM shared-memory migration off on <=17 GiB cards.
$env:STRATA_PP_STAGE_MB = "$PpStageMb"
$env:STRATA_VRAM_RESERVE_MB = "$VramReserveMb"
$env:STRATA_TIER2_FLOOR = "$Tier2Floor"
Write-Host "[strata-hermes] Starting Sakura-Inkling-2-Mini ($Context) on http://${BindHost}:${Port}/v1 (API key: STRATA_API_KEY) ..."
Write-Host "[strata-hermes] expert distribution: GPU(<=--expert-vram) + pinned-RAM(${PpStageMb}MB x2) + CPU workers; VRAM reserve ${VramReserveMb}MB, tier2-floor $Tier2Floor"
& $PythonExe "$RepoRoot\terminal\serve\server.py" `
    --engine strata `
    --config $ConfigPath `
    --host $BindHost `
    --port $Port
