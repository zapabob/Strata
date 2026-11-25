param(
    [Parameter(Mandatory)][string]$ModelRoot,
    [Parameter(Mandatory)][string]$NativeBin,
    [Parameter(Mandatory)][string]$Python,
    [Parameter(Mandatory)][string]$HermesRepo,
    [Parameter(Mandatory)][string]$VerifierPath,
    [Parameter(Mandatory)][string]$ReferencePythonPath,
    [Parameter(Mandatory)][string]$LlamaRepo,
    [string]$StrataEngine,
    [int]$WaitForOwnedPid = 0,
    [ValidateSet('pilot','strata','aime','open-context','answer-context','full','cards','vision')][string[]]$Stages =
        @('pilot','strata','aime','open-context','answer-context','vision','full','cards')
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='2'
$protectionReasons=@('device_memory_pressure','disk_space_pressure','physical_memory_pressure','commit_pressure')
$evidence=Join-Path $ModelRoot 'evaluation'
$math=Join-Path $evidence 'generative-maths'
$long=Join-Path $evidence 'hermes-long-context'
$server=Join-Path $NativeBin 'llama-server.exe'
$hermesPython=Join-Path $HermesRepo '.venv/Scripts/python.exe'
$originalPath=$env:PYTHONPATH
function Invoke-Script([string]$Name,[string[]]$Inputs) {
    & $Python -B (Join-Path $PSScriptRoot $Name) @Inputs
    if ($LASTEXITCODE -ne 0) { throw "$Name exited with $LASTEXITCODE" }
}
function Invoke-Measured([string]$Name,[string[]]$Inputs,[string]$RunDir) {
    while ($true) {
        $started=[DateTime]::UtcNow
        try {
            Invoke-Script $Name $Inputs
            return
        } catch {
            $record=Get-ChildItem -LiteralPath $RunDir -Directory -Filter 'server-*' -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
            $retry=$false
            if ($record) {
                $receipt=Get-Item -LiteralPath (Join-Path $record.FullName 'measurement.json') -ErrorAction SilentlyContinue
                if ($receipt -and $receipt.LastWriteTimeUtc -ge $started) {
                    $m=Get-Content -Raw -LiteralPath $receipt.FullName | ConvertFrom-Json
                    $retry=@($m.protection_events | Where-Object {$protectionReasons -contains $_}).Count -gt 0
                }
            }
            if (!$retry) { throw }
            Write-Output "Waiting for local resources after a measured interruption."
            Start-Sleep -Seconds 15
        }
    }
}
try {
    if ($WaitForOwnedPid) {
        $owned=Get-CimInstance Win32_Process -Filter "ProcessId=$WaitForOwnedPid"
        if ($owned -and $owned.CommandLine -notmatch 'benchmark_hermes_context\.py.*run') {
            throw 'The supplied PID is not the preceding Hermes context measurement'
        }
        if ($owned) { Wait-Process -Id $WaitForOwnedPid -ErrorAction SilentlyContinue }
    }
    foreach ($stage in $Stages) {
        Write-Output ("{0:o} {1}" -f [DateTimeOffset]::Now,$stage)
        $env:PYTHONPATH=$ReferencePythonPath
        if ($stage -eq 'cards') {
            Invoke-Script 'prepare_hf_bundle.py' @('--root',$ModelRoot,'--llama',$LlamaRepo)
            continue
        }
        foreach ($variant in @('ablated','official')) {
            $folder=Join-Path $ModelRoot "$variant-models"
            $filename=if ($variant -eq 'official') {'Inkling-2-Mini-PQ2_0-Baseline.gguf'} else {'Inkling-2-Mini-PQ2_0-Balanced.gguf'}
            $model=Join-Path $folder $filename
            if ($stage -eq 'pilot' -or $stage -eq 'full') {
                $inputs=@('generate','--root',$math,'--stage',$stage,'--variant',$variant,'--bin',$server,
                    '--model',$model,'--manifest',(Join-Path $folder 'Inkling-2-Mini-PQ2_0-Balanced.manifest.json'))
                Invoke-Measured 'benchmark_generation.py' $inputs (Join-Path $math $variant)
            } elseif ($stage -eq 'aime') {
                $aime=Join-Path $evidence 'aime2025'
                $inputs=@('generate','--root',$aime,'--stage','full','--variant',$variant,'--bin',$server,
                    '--model',$model,'--manifest',(Join-Path $folder 'Inkling-2-Mini-PQ2_0-Balanced.manifest.json'))
                Invoke-Measured 'benchmark_generation.py' $inputs (Join-Path $aime $variant)
            } elseif ($stage -eq 'strata') {
                if (!$StrataEngine -or !(Test-Path -LiteralPath $StrataEngine -PathType Leaf)) {
                    throw 'Supply -StrataEngine with the source-built strata-inkling executable for the native stage.'
                }
                $publishedName=if ($variant -eq 'official') {'Inkling-2-Mini-PQ2_0-GGUF/Inkling-2-Mini-PQ2_0-Baseline.gguf'} else {'Inkling-2-Mini-Heretic-PQ2_0-GGUF/Inkling-2-Mini-Heretic-PQ2_0-Balanced.gguf'}
                $model=Join-Path $ModelRoot "huggingface/$publishedName"
                $inputs=@('--root',$ModelRoot,'--bin',$StrataEngine,'--model',$model,'--hermes',$HermesRepo,'--variant',$variant)
                Invoke-Measured 'benchmark_strata.py' $inputs (Join-Path $evidence "sm120-$variant/strata-native")
            } elseif ($stage -eq 'vision') {
                Invoke-Script 'benchmark_vision.py' @('--root',$ModelRoot,'--bin',$NativeBin,'--model',$model,'--variant',$variant)
            } else {
                $protocol=if ($stage -eq 'open-context') {'open-chat'} else {'answer-channel'}
                $inputs=@('run','--root',$long,'--repo',$HermesRepo,'--hermes-python',$hermesPython,
                    '--model',$model,'--bin',$server,'--variant',$variant,'--protocol',$protocol)
                $runDir=if ($protocol -eq 'open-chat') {Join-Path $long $variant} else {Join-Path (Join-Path $long $protocol) $variant}
                Invoke-Measured 'benchmark_hermes_context.py' $inputs $runDir
            }
        }
        if ($stage -eq 'pilot' -or $stage -eq 'full') {
            $env:PYTHONPATH="$VerifierPath;$ReferencePythonPath"
            Invoke-Script 'grade_generation.py' @('--root',$math,'--stage',$stage)
            $env:PYTHONPATH=$ReferencePythonPath
        } elseif ($stage -eq 'aime') {
            Invoke-Script 'benchmark_aime.py' @('grade','--root',(Join-Path $evidence 'aime2025'))
        }
        Invoke-Script 'prepare_hf_bundle.py' @('--root',$ModelRoot,'--llama',$LlamaRepo)
    }
} finally {
    $env:PYTHONPATH=$originalPath
}
