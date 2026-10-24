param(
  [Parameter(Mandatory=$true)][string]$Label,
  [Parameter(Mandatory=$true)][string]$Binary,
  [string[]]$CommandArgs,
  [Parameter(Mandatory=$true)][string]$Prerequisite,
  [int]$Timeout=900,
  [string]$ModelSourceReceipt="",
  [string[]]$ExtraSources=@()
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
if ($null -eq $CommandArgs) { $CommandArgs=@() }
$root='H:/Strata/build/task5a-native-graph-20261024'
if (-not (Test-Path -LiteralPath $root)) { New-Item -ItemType Directory -Path $root | Out-Null }
if (([IO.DriveInfo]::new('H')).AvailableFreeSpace -lt 14GB) { throw 'Insufficient additional peak plus reserve' }
$src=@('CMakeLists.txt','tqcodec/CMakeLists.txt','spin8/CMakeLists.txt','tools/native_graph_step.ps1','tools/run_native_validation_step.py','tools/verify_codec_dialects_build.ps1','tools/verify_bounded_process.cs')
foreach($dir in @('src','include','cmake','spin8/src','spin8/include','spin8/third_party/sha256','tqcodec/src','tqcodec/include','tests/core','third_party','tools')) {
  $src += Get-ChildItem -LiteralPath $dir -File -Recurse | Where-Object { $_.Extension -in @('.h','.hpp','.c','.cpp','.cu','.cuh','.py','.ps1','.cs','.cmake','.manifest','.in','.txt','.json') } | ForEach-Object { $_.FullName.Substring($pwd.Path.Length+1).Replace('\','/') }
}
$build='H:/Strata/build/native-spin8'
foreach($dir in @('H:/Strata/deps/ggml-3cf03257/ggml/src','H:/Strata/deps/ggml-3cf03257/ggml/include','H:/Strata/deps/ggml-3cf03257/ggml/cmake',"$build/ggml-tq-overlay","$build/mmq_tab","$build/CMakeFiles/4.4.0")) {
  if(Test-Path -LiteralPath $dir) { $src += Get-ChildItem -LiteralPath $dir -File -Recurse | Where-Object { $_.Extension -in @('.h','.hpp','.c','.cpp','.cu','.cuh','.cmake','.in','.txt') } | ForEach-Object { $_.FullName } }
}
$src += Get-ChildItem -LiteralPath $build -File -Recurse -Filter '*.vcxproj' | ForEach-Object { $_.FullName }
$src += @("$build/CMakeCache.txt",'H:/Strata/deps/ggml-3cf03257/ggml/CMakeLists.txt',
  'C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/nvcc.exe',
  'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe',
  'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe')
$src += $ExtraSources
$hashes=[ordered]@{}
foreach($p in ($src | Sort-Object -Unique)) { $hashes[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
$path=Join-Path $root ($Label+'.plan.json')
if(Test-Path -LiteralPath $path) { throw 'Preserve prior evidence' }
[IO.File]::WriteAllText((Join-Path $root ($Label+'.sources.json')),($hashes|ConvertTo-Json))
$plan=[ordered]@{source_manifest=(Join-Path $root ($Label+'.sources.json'));source_manifest_sha256=(Get-FileHash -LiteralPath (Join-Path $root ($Label+'.sources.json')) -Algorithm SHA256).Hash.ToLowerInvariant();output_root=$root;binary=$Binary;binary_sha256=(Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash.ToLowerInvariant();command_args=@($CommandArgs);timeout_seconds=$Timeout;expected_additional_peak_bytes=4294967296;max_output_bytes=2147483648;reserve_bytes=10737418240}
if($ModelSourceReceipt) { $plan.model_source_receipt=$ModelSourceReceipt }
$plan.process_environment=@{PATH_prepend='C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/x64';CUDA_CACHE_PATH="$root/cuda-cache"}
[IO.File]::WriteAllText($path,($plan|ConvertTo-Json -Depth 6))
& uv run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B tools/run_native_validation_step.py --plan $path --label $Label --prerequisite $Prerequisite
exit $LASTEXITCODE
