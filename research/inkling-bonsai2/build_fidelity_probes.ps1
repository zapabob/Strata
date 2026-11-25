param(
  [Parameter(Mandatory)][string]$LlamaSource,
  [Parameter(Mandatory)][string]$LlamaBuild,
  [Parameter(Mandatory)][string]$StrataBuild,
  [string]$VsDev='C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/Tools/VsDevCmd.bat'
)
$ErrorActionPreference='Stop'
Push-Location -LiteralPath (Split-Path $VsDev -Parent)
try { $lines=& $env:ComSpec /d /c 'call VsDevCmd.bat -arch=x64 -host_arch=x64 >nul && set' }
finally { Pop-Location }
if ($LASTEXITCODE) { throw 'MSVC environment setup failed' }
foreach ($line in $lines) {
  if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1],$matches[2],'Process') }
}
$repo=(Resolve-Path "$PSScriptRoot/../..").Path
$common=@('/nologo','/std:c++17','/EHsc','/O2','/MD','/utf-8')
$inc=@("/I$LlamaSource/include","/I$LlamaSource/src","/I$LlamaSource/ggml/include","/I$LlamaSource/ggml/src")
$libs=@("/LIBPATH:$LlamaBuild/src","/LIBPATH:$LlamaBuild/ggml/src",'llama.lib','ggml.lib','ggml-base.lib')
foreach ($tool in @('termination_probe','audit_loop_scales')) {
  $name=if ($tool -eq 'termination_probe') { 'termination-probe' } else { 'prism-loop-scales' }
  & cl @common @inc "/Fo$LlamaBuild/$tool.obj" "$PSScriptRoot/$tool.cpp" /link "/OUT:$LlamaBuild/bin/$name.exe" @libs
  if ($LASTEXITCODE) { throw "Compilation of $name failed" }
}
& cl @common /DSTRATA_SCALE_AUDIT "/I$repo/engine/src/inkling2" "/I$repo/engine/include" "/I$repo/engine/src" "/I$repo/engine/third_party" "/Fo$StrataBuild/audit_loop_scales.obj" "$PSScriptRoot/audit_loop_scales.cpp" /link "/OUT:$StrataBuild/strata-loop-scales.exe" "/LIBPATH:$StrataBuild" strata_inkling_core.lib strata_quant.lib strata_zstd_dec.lib
if ($LASTEXITCODE) { throw 'Compilation of the native Strata scale audit failed' }
