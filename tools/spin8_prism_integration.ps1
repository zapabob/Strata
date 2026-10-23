<# Builds only the exact composed query-v3 patch. Does not acquire or reset source. #>
[CmdletBinding()]
param(
    [string]$Source = 'H:\Strata\deps\prism-73bfe6cc-sm120',
    [string]$Build = 'H:\Strata\build\prism-73bfe6cc-cuda-sm120',
    [string]$BaselineSource = 'H:\Strata\deps\prism-73bfe6cc',
    [switch]$CpuOnly,
    [Parameter(Mandatory)][string]$Evidence,
    [string]$CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'spin8_backend_verify.ps1')
$root = Split-Path $PSScriptRoot
$pin = '73bfe6cc485554822f80c473a3c0c4f25e80f41b'
$patch = Join-Path $PSScriptRoot 'spin8_prism_query_integration.patch'
if (Test-Path -LiteralPath $Evidence) { throw 'Use a fresh evidence directory; earlier evidence is preserved.' }
New-Item -ItemType Directory -Path $Evidence | Out-Null
$receipt = [ordered]@{schemaVersion=1; pin=$pin; status='started'; source=$Source; build=$Build; jobs=1; start=[DateTime]::UtcNow.ToString('o')}
try {
    $receipt.patchSha256 = Assert-BonsaiSourcePatch -Source $Source -BaseCommit $pin -PatchPath $patch -OutputPath (Join-Path $Evidence 'source-before.diff')
    $receipt.strataHead = (& git -C $root rev-parse HEAD).Trim()
    $baselineHead = & git -C $BaselineSource rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $baselineHead.Trim() -ne $pin) { throw 'Baseline headers must use the exact pristine Prism pin.' }
    $baselineStatus = & git -C $BaselineSource status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0 -or $baselineStatus) { throw 'Baseline header source must be clean.' }
    $receipt.baselineHeaders = @(Get-ChildItem -LiteralPath (Join-Path $BaselineSource 'include'),(Join-Path $BaselineSource 'ggml/include') -File | ForEach-Object {
        @{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}
    })
    $receipt.testSources = @('spin8_prism_model_test.cpp','spin8_prism_model_test.py','spin8_prism_capabilities_test.cpp','spin8_prism_bridge_test.cpp','spin8_prism_integration.ps1','spin8_prism_process.py','spin8_prism_msvc.py','spin8_prism_baseline_test.cpp','spin8_prism_ui_test.cpp','test_spin8_prism_msvc.py','spin8_prism_dependency_audit.py','test_spin8_prism_process.py','test_spin8_prism_no_ui.py' | ForEach-Object {
        @{path=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $_)).Hash.ToLowerInvariant()}
    })
    $receipt.spin8Sources = @(Get-ChildItem -LiteralPath (Join-Path $root 'spin8') -Recurse -File | ForEach-Object {
        @{path=[IO.Path]::GetRelativePath($root,$_.FullName); sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}
    })
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    $installation = (& $vswhere -latest -version '[17,18)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
    if (-not $installation) { throw 'Visual Studio 2022 unavailable.' }
    $vcvars = Join-Path $installation 'VC\Auxiliary\Build\vcvars64.bat'
    $vcEnvironment = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
    if ($LASTEXITCODE -ne 0) { throw 'Visual Studio environment failed.' }
    foreach ($line in $vcEnvironment) {
        if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process') }
    }
    $env:VSLANG = '1041' # installed compiler resource, disposable process only
    $python = (& uv run --no-project --no-managed-python python -c 'import sys; print(sys.executable)').Trim()
    $launcher = $python + ';' + (Join-Path $PSScriptRoot 'spin8_prism_msvc.py')
    $configure = @('-S',$Source,'-B',$Build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS=/DWIN32 /D_WINDOWS /EHsc /utf-8',
        "-DCMAKE_CXX_COMPILER_LAUNCHER=$launcher","-DCMAKE_C_COMPILER_LAUNCHER=$launcher",
        '-DSTRATA_SPIN8_MSVC_UTF8_DIAGNOSTICS=ON',"-DSTRATA_SPIN8_SOURCE=$(Join-Path $root 'spin8')",'-DSTRATA_SPIN8_TESTS=ON',"-DSTRATA_SPIN8_BASELINE_SOURCE=$BaselineSource",
        '-DLLAMA_EMBED_UI=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF',
        '-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_TOOLS=ON','-DLLAMA_BUILD_SERVER=ON','-DLLAMA_OPENSSL=OFF')
    if($CpuOnly) { $configure += '-DGGML_CUDA=OFF' }
    else { $configure += @('-DGGML_CUDA=ON','-DGGML_CUDA_STANDARD_SM120=ON','-DCMAKE_CUDA_ARCHITECTURES=120',
        "-DCMAKE_CUDA_COMPILER=$(Join-Path $CudaRoot 'bin\nvcc.exe')","-DCUDAToolkit_ROOT=$CudaRoot") }
    $receipt.cpuOnly = [bool]$CpuOnly
    $receipt.configure = $configure
    & cmake @configure *> (Join-Path $Evidence 'configure.log')
    if ($LASTEXITCODE -ne 0) { throw 'Configure failed; see configure.log.' }
    $ninja = ((Get-Content -LiteralPath (Join-Path $Build 'CMakeCache.txt') | Where-Object { $_ -like 'CMAKE_MAKE_PROGRAM:FILEPATH=*' }) -split '=',2)[1]
    & $python -B (Join-Path $PSScriptRoot 'test_spin8_prism_msvc.py') --ninja $ninja --evidence (Join-Path $Evidence 'header-regression')
    if ($LASTEXITCODE -ne 0) { throw 'Real header-change regression failed.' }
    $object = 'ggml/src/CMakeFiles/ggml-base.dir/ggml-spin8.cpp.obj'
    & cmake --build $Build --target $object --parallel 1 *> (Join-Path $Evidence 'dependency-probe-build.log')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency probe compilation failed.' }
    $ninja = ((Get-Content -LiteralPath (Join-Path $Build 'CMakeCache.txt') | Where-Object { $_ -like 'CMAKE_MAKE_PROGRAM:FILEPATH=*' }) -split '=',2)[1]
    $dependencies = & $ninja -C $Build -t deps $object
    $dependencies | Set-Content -LiteralPath (Join-Path $Evidence 'dependency-probe.txt') -Encoding utf8NoBOM
    if (-not ($dependencies -match '#deps [1-9]') -or -not ($dependencies -match 'ggml-spin8.h')) { throw 'Ninja did not record actual header dependencies.' }
    & cmake --build $Build --target llama-server strata-spin8-model-test strata-spin8-bridge-test strata-spin8-ui-test strata-spin8-baseline-test strata-spin8-capabilities-test --parallel 1 *> (Join-Path $Evidence 'build.log')
    if ($LASTEXITCODE -ne 0) { throw 'Build failed; see build.log.' }
    Assert-BonsaiSourcePatch -Source $Source -BaseCommit $pin -PatchPath $patch -OutputPath (Join-Path $Evidence 'source-after.diff') | Out-Null
    foreach ($entry in $receipt.spin8Sources) {
        if ((Get-FileHash -LiteralPath (Join-Path $root $entry.path)).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'libspin8 changed during build.' }
    }
    foreach ($entry in $receipt.testSources) {
        if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $entry.path)).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Probe source changed during build.' }
    }
    foreach ($entry in $receipt.baselineHeaders) {
        if ((Get-FileHash -LiteralPath $entry.path).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Baseline ABI headers changed during build.' }
    }
    $binary = Join-Path $Build 'bin\llama-server.exe'
    & uv run --no-project --no-managed-python python -B (Join-Path $PSScriptRoot 'spin8_prism_process.py') --receipt (Join-Path $Evidence 'version.json') -- $binary --version
    if ($LASTEXITCODE -ne 0) { throw 'Controlled version probe failed.' }
    $expectedCuda = if($CpuOnly) { '0' } else { '1' }
    & $python -B (Join-Path $PSScriptRoot 'spin8_prism_process.py') --receipt (Join-Path $Evidence 'capabilities.json') -- (Join-Path $Build 'bin/strata-spin8-capabilities-test.exe') $expectedCuda
    if($LASTEXITCODE -ne 0) { throw 'Compiled/runtime capability probe failed.' }
    $receipt.files = @(Get-ChildItem -LiteralPath (Join-Path $Build 'bin') -File | Where-Object { $_.Extension -in '.dll','.exe' } | ForEach-Object {
        @{path=$_.FullName;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}
    })
    $receipt.status = 'compiled-probe-passed'
} catch {
    $receipt.status = 'failed'; $receipt.error = $_.Exception.Message; throw
} finally {
    $receipt.end = [DateTime]::UtcNow.ToString('o')
    $receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $Evidence 'manifest.json') -Encoding utf8NoBOM
}
