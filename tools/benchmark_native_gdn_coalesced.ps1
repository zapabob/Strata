param([switch]$BuildOnly, [switch]$SelfTest, [switch]$Quick)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$out=Join-Path $repo 'build/gdn-coalesced-experiment'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$nvcc=(Get-Command nvcc.exe -ErrorAction Stop).Source
$vswhere=Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -version '[17,18)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'Visual Studio 2022 C++ tools required' }
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$exe=Join-Path $out 'native_gdn_coalesced_bench.exe'
$buildCmd=Join-Path $out 'build.cmd'
$common='"'+$nvcc+'" -std=c++17 -O3 -arch=sm_120 -lineinfo -Xcompiler /EHsc,/utf-8 -I "'+(Join-Path $repo 'include')+'"'
$lines=@('@echo off',('call "'+$vcvars+'" >nul'),'if errorlevel 1 exit /b %errorlevel%')
$units=@(
 @{source='bench/native_gdn_coalesced_bench.cpp';obj='bench.obj';fast=$false}
 @{source='src/kernels/cuda/native_gdn.cu';obj='native.obj';fast=$true}
 @{source='src/kernels/cuda/native_gdn_preprocess.cu';obj='preprocess.obj';fast=$true}
 @{source='src/kernels/cuda/fused_gdn.cu';obj='fused.obj';fast=$false}
)
# Match CMakeLists.txt: fast math belongs to the pinned native adapters only.
foreach ($unit in $units) {
 $flags=if($unit.fast){' --use_fast_math'}else{''}
 $lines+=($common+$flags+' -c "'+(Join-Path $repo $unit.source)+'" -o "'+(Join-Path $out $unit.obj)+'"')
 $lines+='if errorlevel 1 exit /b %errorlevel%'
}
$objects=($units | ForEach-Object {'"'+(Join-Path $out $_.obj)+'"'}) -join ' '
$lines+=('"'+$nvcc+'" '+$objects+' -o "'+$exe+'"')
$lines+='exit /b %errorlevel%'
[IO.File]::WriteAllLines($buildCmd,$lines,[Text.UTF8Encoding]::new($false))
Push-Location $out
try {
 & $env:ComSpec /d /c $buildCmd 2>&1 | Tee-Object -FilePath (Join-Path $out 'build.log')
 if ($LASTEXITCODE -ne 0) { throw "nvcc failed: $LASTEXITCODE" }
 if (-not $BuildOnly) {
  $benchArgs=@()
  if ($SelfTest) { $benchArgs+='--selftest' }
  if ($Quick) { $benchArgs+='--quick' }
  & $exe @benchArgs
  if ($LASTEXITCODE -ne 0) { throw "GDN experiment failed: $LASTEXITCODE" }
 }
} finally { Pop-Location }
