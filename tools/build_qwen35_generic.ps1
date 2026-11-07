<# Build only the reviewed private generic runtime in an isolated H: directory. No acquisition or installation. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Probe','Configure','Build')][string]$Phase,
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceCommit,
    [Parameter(Mandatory=$true)][string]$BuildDirectory,
    [string]$CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:QWEN35_TEST_OUT -eq $null) { throw 'Run under the owned resource/job guard.' }
if ($BuildDirectory -notmatch '^H:[\\/]' -or $env:TEMP -notmatch '^H:[\\/]') { throw 'Build and TEMP must be on H:.' }
if ($ExpectedSourceCommit -notmatch '^[0-9a-f]{40}$') { throw 'Frozen source commit required.' }
$actual = (& git -C $Source rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $ExpectedSourceCommit) { throw 'Source commit differs.' }
# Cached Git status missed NUL-filled checkout files; verify every committed blob.
$python = 'C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe'
& $python -B (Join-Path $PSScriptRoot 'verify_frozen_llama_source.py') --source $Source --commit $ExpectedSourceCommit --receipt (Join-Path $env:QWEN35_TEST_OUT "source-$Phase.json")
if ($LASTEXITCODE -ne 0) { throw 'Source byte verification failed.' }
if (-not (Test-Path -LiteralPath (Split-Path $BuildDirectory))) { throw 'Build parent must exist.' }
if (-not (Test-Path -LiteralPath $BuildDirectory)) { New-Item -ItemType Directory -Path $BuildDirectory | Out-Null }
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$installation = (& $vswhere -latest -version '[17,18)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
if (-not $installation) { throw 'Existing VS2022 C++ tools required.' }
$vcvars = Join-Path $installation 'VC\Auxiliary\Build\vcvars64.bat'
$vcEnvironment = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'Cannot initialize existing MSVC.' }
foreach ($line in $vcEnvironment) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') }
}
function Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed ($LASTEXITCODE)" }
}
if ($Phase -eq 'Probe') {
    Checked 'cl.exe' @('/nologo','/std:c++17','/EHsc','/W4','/WX','/utf-8','/MD',"/I$Source\include", "/I$Source\ggml\include",(Join-Path $PSScriptRoot 'qwen35_mtp_loader_probe.cpp'),"/Fo$BuildDirectory\probe.obj","/Fe$BuildDirectory\qwen35-loader-probe.exe")
} elseif ($Phase -eq 'Configure') {
    $ninja = Join-Path $installation 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
    $nvcc = Join-Path $CudaRoot 'bin\nvcc.exe'
    if (-not (Test-Path -LiteralPath $ninja) -or -not (Test-Path -LiteralPath $nvcc)) { throw 'Existing Ninja/CUDA 13.3 required.' }
    Checked 'cmake.exe' @('-S',$Source,'-B',$BuildDirectory,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$ninja",'-DCMAKE_BUILD_TYPE=Release',
        '-DLLAMA_BUILD_SERVER=ON','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_TOOLS=ON',
        '-DLLAMA_BUILD_UI=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_OPENSSL=OFF','-DGGML_NATIVE=OFF','-DGGML_CUDA=ON',
        '-DCMAKE_CUDA_ARCHITECTURES=120','-DGGML_CUDA_STANDARD_SM120=ON',"-DCMAKE_CUDA_COMPILER=$nvcc", "-DCUDAToolkit_ROOT=$CudaRoot")
} else {
    Checked 'cmake.exe' @('--build',$BuildDirectory,'--config','Release','--target','llama-server','--parallel','1')
}
