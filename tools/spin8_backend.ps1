<#
.SYNOPSIS
Acquire an exact Bonsai llama.cpp revision and build it beside Strata on H:.
.DESCRIPTION
Does not replace Strata's ggml, install globally, download models, or operate a server.
The manifest records actual artifact hashes. Spin8 attention is not available in
either pinned revision; no flag-only integration is represented as support.
#>
[CmdletBinding()]
param(
    [ValidateSet('prism', 'zapabob', 'turboquant')][string]$Backend = 'prism',
    [string]$StorageRoot = 'H:\Strata',
    [ValidateSet('cpu', 'cuda')][string]$Device = 'cuda',
    [ValidateSet('120')][string]$CudaArchitecture = '120',
    [ValidateRange(1, 32)][int]$Jobs = 4,
    [string]$CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3',
    [switch]$AcquireOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'spin8_backend_verify.ps1')
$pins = @{
    prism = @{ repository = 'https://github.com/PrismML-Eng/llama.cpp.git'; commit = '73bfe6cc485554822f80c473a3c0c4f25e80f41b' }
    zapabob = @{ repository = 'https://github.com/zapabob/llama.cpp.git'; commit = '2c8e9655cdc6ea31051d4437a71492e717d046a4' }
    turboquant = @{ repository = 'https://github.com/TheTom/llama-cpp-turboquant.git'; commit = '643956891dfdf51aecdbd05ca508dd21e21e8195' }
}
$pin = $pins[$Backend]
$storage = [IO.Path]::GetFullPath($StorageRoot)
$source = Join-Path $storage "deps\$Backend-$($pin.commit.Substring(0,8))"
$buildName = "$Backend-$($pin.commit.Substring(0,8))-$Device"
if ($Device -eq 'cuda' -and -not $AcquireOnly) { $buildName += '-sm120'; if ($Backend -eq 'turboquant') { $buildName += '-standard' } }
$build = Join-Path $storage "build\$buildName"
$commands = [Collections.Generic.List[object]]::new()
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    $commands.Add(@{ executable = $Exe; arguments = $Arguments })
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}
Get-Command git, cmake -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path (Split-Path $source), $build -Force | Out-Null
if (-not (Test-Path -LiteralPath $source)) {
    Invoke-Checked git @('clone', '--filter=blob:none', '--no-checkout', $pin.repository, $source)
    Invoke-Checked git @('-C', $source, 'checkout', '--detach', $pin.commit)
}
$remote = (& git -C $source remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $remote -ne $pin.repository) { throw "Unexpected source repository at $source" }
$revision = (& git -C $source rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $revision -ne $pin.commit) { throw "Source revision mismatch at $source; existing work is preserved." }
$dirty = @(& git -C $source status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $dirty.Count) { throw "Source is not clean at $source; existing work is preserved." }
$manifestPath = Join-Path $build 'bonsai-runtime.json'
$buildSource = $source
$manifest = [ordered]@{
    schemaVersion = 1; backend = $Backend
    source = @{ repository = $remote; commit = $revision; dirty = $false; path = $source; patches = @() }
    build = @{ status = 'not-built'; device = $Device; cudaArchitecture = $CudaArchitecture; directory = $build }
    spin8 = @{ available = $false; modes = @('off'); attentionHook = $false; profiling = $false }
    modelFormats = $(if ($Backend -eq 'prism') { @('PQ2_0', 'PTQ1_0', 'Q2_0') } elseif ($Backend -eq 'turboquant') { @('standard-gguf') } else { @('Q2_0') })
    modelLoadTested = $false
    commands = $commands; files = @(); binary = $null
    createdAt = [DateTime]::UtcNow.ToString('o')
}
if ($AcquireOnly) {
    # Acquisition evidence is separate so it cannot replace an existing success manifest.
    $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $build 'source-pin.json') -Encoding utf8NoBOM
    Write-Output "Pinned source verified: $source"
    return
}
try {
    if ($Device -eq 'cuda' -and $Backend -eq 'zapabob') { throw 'The zapabob CUDA runtime has not been qualified. Use -AcquireOnly.' }
    if ($Device -eq 'cuda' -and $Backend -in @('prism', 'turboquant')) {
        $buildSource = "$source-sm120"
        $patch = Join-Path $PSScriptRoot $(if ($Backend -eq 'prism') { 'spin8_backend_sm120.patch' } else { 'turboquant_backend_sm120.patch' })
        $patchHash = (Get-FileHash -LiteralPath $patch -Algorithm SHA256).Hash.ToLowerInvariant()
        if (-not (Test-Path -LiteralPath $buildSource)) {
            Invoke-Checked git @('-C', $source, 'worktree', 'add', '--detach', $buildSource, $pin.commit)
            Invoke-Checked git @('-C', $buildSource, 'apply', '--check', $patch)
            Invoke-Checked git @('-C', $buildSource, 'apply', $patch)
        }
        $appliedPatch = Join-Path $build 'source-patch.diff'
        Assert-BonsaiSourcePatch -Source $buildSource -BaseCommit $pin.commit -PatchPath $patch -OutputPath $appliedPatch | Out-Null
        $manifest.source.path = $buildSource
        $manifest.source.basePath = $source
        $manifest.source.dirty = $true
        $manifest.source.patches = @(@{ id = "$Backend-standard-sm120-v1"; sha256 = $patchHash })
        $manifest.source.verification = @{ comparedAgainst = 'HEAD'; includesStagedChanges = $true; untrackedRejected = $true }
    }
    $generator = @()
    if ($IsWindows) {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
        $installation = (& $vswhere -latest -version '[17,18)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
        if (-not $installation) { throw 'Visual Studio 2022 C++ build tools were not found.' }
        $vcvars = Join-Path $installation 'VC\Auxiliary\Build\vcvars64.bat'
        # Installer-owned command; build paths and caller input never enter cmd.exe.
        $vcEnvironment = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
        if ($LASTEXITCODE -ne 0) { throw 'Failed to initialize the Visual Studio environment.' }
        foreach ($line in $vcEnvironment) {
            if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') }
        }
        $ninja = Join-Path $installation 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
        if (-not (Test-Path -LiteralPath $ninja)) { throw 'Visual Studio Ninja was not found.' }
        $generator = @('-G', 'Ninja', "-DCMAKE_MAKE_PROGRAM=$ninja")
    }
    $configure = @('-S', $buildSource, '-B', $build) + $generator + @(
        '-DCMAKE_BUILD_TYPE=Release', '-DLLAMA_BUILD_SERVER=ON', '-DLLAMA_BUILD_TESTS=OFF',
        '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_TOOLS=ON', '-DLLAMA_OPENSSL=OFF',
        '-DGGML_NATIVE=OFF', "-DGGML_CUDA=$(if ($Device -eq 'cuda') { 'ON' } else { 'OFF' })",
        '-DLLAMA_BUILD_UI=OFF', '-DLLAMA_BUILD_APP=OFF'
    )
    if ($Device -eq 'cuda') {
        $nvcc = Join-Path $CudaRoot 'bin\nvcc.exe'
        if (-not (Test-Path -LiteralPath $nvcc)) { throw "CUDA compiler missing: $nvcc" }
        $configure += @("-DCMAKE_CUDA_COMPILER=$nvcc", "-DCUDAToolkit_ROOT=$CudaRoot", "-DCMAKE_CUDA_ARCHITECTURES=$CudaArchitecture")
        $configure += '-DGGML_CUDA_STANDARD_SM120=ON'
        $manifest.build.cudaVersion = (& $nvcc --version) -join "`n"
    }
    $manifest.build.cmakeVersion = (& cmake --version) -join "`n"
    Invoke-Checked cmake $configure
    Invoke-Checked cmake @('--build', $build, '--config', 'Release', '--target', 'llama-server', '--parallel', [string]$Jobs)
    $binary = Join-Path $build $(if ($IsWindows) { 'bin\llama-server.exe' } else { 'bin/llama-server' })
    if (-not (Test-Path -LiteralPath $binary)) { throw "Build did not produce $binary" }
    $manifest.build.versionOutput = (& $binary --version 2>&1) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw 'Built server failed its --version smoke test.' }
    $manifest.files = @(Get-ChildItem -LiteralPath (Split-Path $binary) -File | Where-Object {
        $_.Extension -in @('.dll', '.so', '.dylib') -or $_.FullName -eq $binary
    } | ForEach-Object {
        @{ path = [IO.Path]::GetRelativePath($build, $_.FullName); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
    })
    $manifest.binary = @{ path = $binary; sha256 = (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() }
    if ($Device -eq 'cuda') {
        $cudaLibrary = Join-Path (Split-Path $binary) 'ggml-cuda.dll'
        $cuobjdump = Join-Path $CudaRoot 'bin\cuobjdump.exe'
        $commands.Add(@{ executable = $cuobjdump; arguments = @('--list-elf', $cudaLibrary) })
        $cubinEvidence = @(& $cuobjdump --list-elf $cudaLibrary 2>&1) -join "`n"
        if ($LASTEXITCODE -ne 0) { throw 'Could not inspect CUDA library architecture.' }
        $architectures = @([regex]::Matches($cubinEvidence, 'sm_([0-9]+[af]?)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
        if ($architectures.Count -ne 1 -or $architectures[0] -ne '120') { throw 'CUDA artifact is not exclusively standard sm_120.' }
        $architecturePath = Join-Path $build 'cuda-architectures.txt'
        Set-Content -LiteralPath $architecturePath -Value $cubinEvidence -Encoding utf8NoBOM
        $manifest.build.cudaCubins = @('sm_120')
        $manifest.files += @{ path = 'cuda-architectures.txt'; bytes = (Get-Item -LiteralPath $architecturePath).Length; sha256 = (Get-FileHash -LiteralPath $architecturePath -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
    if ($manifest.source.patches.Count) {
        $manifest.files += @{ path = 'source-patch.diff'; bytes = (Get-Item -LiteralPath $appliedPatch).Length; sha256 = $patchHash }
        $verifiedPatch = Join-Path $build 'source-patch-after-build.diff'
        Assert-BonsaiSourcePatch -Source $buildSource -BaseCommit $pin.commit -PatchPath $patch -OutputPath $verifiedPatch | Out-Null
    }
    if (@(& git -C $source status --porcelain --untracked-files=all).Count) { throw 'Source changed during the build.' }
    $manifest.build.status = 'success'
} catch {
    $manifest.build.status = 'failed'
    $manifest.build.error = $_.Exception.Message
    throw
} finally {
    $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
    Write-Output "Build evidence: $manifestPath"
}
Write-Output "Built server: $($manifest.binary.path)"
Write-Output "SHA256: $($manifest.binary.sha256)"
