param(
    [Parameter(Mandatory)][string]$WorkDir,
    [ValidateSet('120','80')][string]$CudaArchitecture = '120',
    [switch]$Strata
)
$ErrorActionPreference = 'Stop'
function Invoke-Checked([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command exited with $LASTEXITCODE" }
}
$revisionFile = if ($Strata) {'strata-revision.txt'} else {'upstream-revision.txt'}
$base = (Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot $revisionFile)).Trim()
if ($base -notmatch '^[0-9a-f]{40}$') { throw 'Invalid upstream revision' }
$work = [IO.Path]::GetFullPath($WorkDir)
$name = if ($Strata) {'Strata'} else {'llama.cpp'}
$upstream = if ($Strata) {'https://github.com/zapabob/Strata.git'} else {'https://github.com/ggml-org/llama.cpp.git'}
$patchFile = if ($Strata) {'strata-native.patch'} else {'inkling-pq2.patch'}
$source = Join-Path $work $name
$buildName = if ($Strata) {"strata-sm$CudaArchitecture"} else {"build-sm$CudaArchitecture"}
$build = Join-Path $work $buildName
$patch = Join-Path $PSScriptRoot $patchFile
New-Item -ItemType Directory -Force -Path $work | Out-Null
if (!(Test-Path -LiteralPath $source)) {
    Invoke-Checked git @('init',$source)
    Invoke-Checked git @('-C',$source,'remote','add','origin',$upstream)
    Invoke-Checked git @('-C',$source,'fetch','--depth','1','origin',$base)
    Invoke-Checked git @('-C',$source,'checkout','--detach','FETCH_HEAD')
}
$actual = (& git -C $source rev-parse HEAD)
if ($LASTEXITCODE -ne 0 -or $actual -ne $base) { throw 'Choose an empty work directory or the pinned checkout' }
if ((Get-Item -LiteralPath $patch).Length -gt 0) {
    & git -C $source apply --reverse --check $patch 2>$null
    if ($LASTEXITCODE -ne 0) {
        Invoke-Checked git @('-C',$source,'apply','--check',$patch)
        Invoke-Checked git @('-C',$source,'apply',$patch)
    }
} elseif (!$Strata) {
    throw 'The upstream llama.cpp build requires its integration patch'
}
if ($Strata) {
    & (Join-Path $PSScriptRoot 'compile-strata.ps1') -StrataNative -Source (Join-Path $source 'engine/src/inkling2') -Build $build -Architectures $CudaArchitecture
    if ($LASTEXITCODE) { throw 'Native Strata build failed' }
    Write-Output (Join-Path $build 'strata-inkling.exe')
    return
}
Invoke-Checked cmake @('-S',$source,'-B',$build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
    '-DGGML_CUDA=ON','-DGGML_CUDA_FA=ON','-DGGML_NATIVE=OFF','-DBUILD_SHARED_LIBS=ON',
    '-DLLAMA_OPENSSL=OFF',"-DCMAKE_CUDA_ARCHITECTURES=$CudaArchitecture-real")
Invoke-Checked cmake @('--build',$build,'--config','Release','--parallel','5',
    '--target','llama-server','llama-completion','llama-bench','llama-mtmd-cli')
Write-Output (Join-Path $build 'bin')
