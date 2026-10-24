param([Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference='Stop'
Import-Module 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1'
Import-Module 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules/Microsoft.PowerShell.Management/Microsoft.PowerShell.Management.psd1'
$ProgressPreference='SilentlyContinue'
$build='H:/Strata/build/native-spin8'
$overlay=(Resolve-Path -LiteralPath (Join-Path $build 'ggml-tq-overlay')).Path
$proof=Join-Path 'H:/Strata/build/task5a-native-graph-20261024' ($Label+'.overlay-reuse.json')
if(Test-Path -LiteralPath $proof) { throw 'Preserve prior overlay evidence' }
$projects=@('strata_mmq.vcxproj','strata_kq.vcxproj','strata_mmq_w4a4.vcxproj')
$projectHashes=@{}
foreach($name in $projects) { $projectHashes[$name]=(Get-FileHash -LiteralPath (Join-Path $build $name) -Algorithm SHA256).Hash }
$compileInputs=@{}
foreach($dir in @('C:/Users/downl/Documents/ChatGPT/Strata/include','C:/Users/downl/Documents/ChatGPT/Strata/src/prefill','H:/Strata/deps/ggml-3cf03257/ggml/include','H:/Strata/deps/ggml-3cf03257/ggml/src')) {
  foreach($file in (Get-ChildItem -LiteralPath $dir -File -Recurse)) {
    $compileInputs[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  }
}
$before=@()
foreach($item in (Get-ChildItem -LiteralPath $overlay -File -Recurse)) {
  $before += [pscustomobject]@{path=$item.FullName;sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash;utc_ticks=$item.LastWriteTimeUtc.Ticks}
}
& 'C:/Program Files/CMake/bin/cmake.exe' -S 'C:/Users/downl/Documents/ChatGPT/Strata' -B $build -DSTRATA_ENABLE_NATIVE_CACHE=ON
$result=$LASTEXITCODE
if($result -ne 0) { exit $result }
$sameProjects=$true
foreach($name in $projects) { if((Get-FileHash -LiteralPath (Join-Path $build $name) -Algorithm SHA256).Hash -ne $projectHashes[$name]) { $sameProjects=$false } }
$sameInputs=$true
foreach($path in $compileInputs.Keys) {
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $compileInputs[$path]) { $sameInputs=$false }
}
$sameOverlay=$true
foreach($old in $before) {
  if((Get-FileHash -LiteralPath $old.path -Algorithm SHA256).Hash -ne $old.sha256) { $sameOverlay=$false }
}
$records=@()
foreach($old in $before) {
  $resolved=(Resolve-Path -LiteralPath $old.path).Path
  if(-not $resolved.StartsWith($overlay+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Overlay path escaped its verified build directory' }
  $after=(Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash
  $afterTicks=(Get-Item -LiteralPath $resolved).LastWriteTimeUtc.Ticks
  $restore=$sameProjects -and $sameInputs -and $sameOverlay
  if($restore) { (Get-Item -LiteralPath $resolved).LastWriteTimeUtc=[DateTime]::new($old.utc_ticks,[DateTimeKind]::Utc) }
  $records += [pscustomobject]@{path=$resolved;before_sha256=$old.sha256;after_sha256=$after;timestamp_restored=$restore;prior_utc_ticks=$old.utc_ticks;postconfigure_utc_ticks=$afterTicks;final_utc_ticks=(Get-Item -LiteralPath $resolved).LastWriteTimeUtc.Ticks}
}
[IO.File]::WriteAllText($proof,([ordered]@{schema=1;cmake_exit_code=$result;identical_mmq_projects=$sameProjects;identical_compile_inputs=$sameInputs;identical_overlay=$sameOverlay;compile_inputs_sha256=$compileInputs;project_sha256=$projectHashes;files=$records}|ConvertTo-Json -Depth 6))
exit 0
