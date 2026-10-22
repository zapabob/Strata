<#
.SYNOPSIS
Prepare or test the opt-in strict Spin8 Prism reference graph patch.
.DESCRIPTION
Uses a detached pinned worktree. Does not operate servers, change weights, or install globally.
This stage rotates unquantized cache reads. It does not implement three quantized rotated K caches.
#>
[CmdletBinding()]
param(
    [ValidateSet('Prepare', 'Test')][string]$Action = 'Test',
    [string]$StorageRoot = 'H:\Strata',
    [ValidateRange(1, 4)][int]$Jobs = 1
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$graphCommit = '73bfe6cc485554822f80c473a3c0c4f25e80f41b'
$graphBase = Join-Path $StorageRoot 'deps\prism-73bfe6cc'
$graphSource = Join-Path $StorageRoot 'deps\prism-spin8-graph'
$graphBuild = Join-Path $StorageRoot 'build\prism-spin8-graph-test'
$graphRoot = Split-Path $PSScriptRoot
$graphPatch = Join-Path $PSScriptRoot 'spin8_prism_graph.patch'
function Invoke-GraphChecked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}
if ((& git -C $graphBase rev-parse HEAD).Trim() -ne $graphCommit) { throw 'Pinned Prism base is unavailable or has changed.' }
if (-not (Test-Path -LiteralPath $graphSource)) {
    Invoke-GraphChecked git @('-C', $graphBase, 'worktree', 'add', '--detach', $graphSource, $graphCommit)
    Invoke-GraphChecked git @('-C', $graphSource, 'apply', '--check', $graphPatch)
    Invoke-GraphChecked git @('-C', $graphSource, 'apply', $graphPatch)
}
if ((& git -C $graphSource rev-parse HEAD).Trim() -ne $graphCommit) { throw 'Graph worktree base has changed.' }
Invoke-GraphChecked git @('-C', $graphSource, 'apply', '--reverse', '--check', $graphPatch)
# Compare all changed tracked files and the one added header, preserving unrelated work on mismatch.
$graphExpectedFiles = @('common/arg.cpp', 'common/common.cpp', 'common/common.h', 'include/llama.h',
    'src/CMakeLists.txt', 'src/llama-context.cpp', 'src/llama-cparams.h', 'src/llama-graph.cpp', 'src/llama-spin8.h')
$graphActualFiles = @(& git -C $graphSource diff HEAD --name-only) + @(& git -C $graphSource ls-files --others --exclude-standard)
if (@(Compare-Object ($graphExpectedFiles | Sort-Object -Unique) ($graphActualFiles | Sort-Object -Unique)).Count) {
    throw 'Graph worktree contains unexpected changes; existing work is preserved.'
}
if ($Action -eq 'Prepare') { Write-Output "Reference graph source prepared: $graphSource"; return }
$graphVswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$graphVs = (& $graphVswhere -latest -version '[17,18)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
if (-not $graphVs) { throw 'Visual Studio 2022 C++ tools are required.' }
$graphVcvars = Join-Path $graphVs 'VC\Auxiliary\Build\vcvars64.bat'
$graphEnvironment = & $env:ComSpec /d /c "`"$graphVcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize compiler environment.' }
foreach ($graphLine in $graphEnvironment) {
    if ($graphLine -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') }
}
$graphNinja = Join-Path $graphVs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
Invoke-GraphChecked cmake @('-S', (Join-Path $PSScriptRoot 'spin8_prism_graph_test'), '-B', $graphBuild,
    '-G', 'Ninja', "-DCMAKE_MAKE_PROGRAM=$graphNinja", '-DCMAKE_BUILD_TYPE=Release',
    "-DPRISM_SOURCE=$graphSource", "-DSPIN8_SOURCE=$(Join-Path $graphRoot 'spin8')")
Invoke-GraphChecked cmake @('--build', $graphBuild, '--target', 'spin8_prism_graph_test', '--parallel', "$Jobs")
$graphTest = Join-Path $graphBuild 'spin8_prism_graph_test.exe'
Invoke-GraphChecked $graphTest @((Join-Path $graphRoot 'data\spin8\reference.profile'))
$graphEvidence = [ordered]@{
    schemaVersion = 1
    baseCommit = $graphCommit
    patchSha256 = (Get-FileHash -LiteralPath $graphPatch -Algorithm SHA256).Hash.ToLowerInvariant()
    testExecutableSha256 = (Get-FileHash -LiteralPath $graphTest -Algorithm SHA256).Hash.ToLowerInvariant()
    capability = 'reference-graph'
    numericalTest = 'passed'
    fullServerBuildTested = $false
    modelLoadTested = $false
    rotatedQuantizedKCache = $false
    createdAt = [DateTime]::UtcNow.ToString('o')
}
$graphEvidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $graphBuild 'spin8-graph-test.json') -Encoding utf8NoBOM
