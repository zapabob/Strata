param(
  [Parameter(Mandatory)][string]$Source,
  [Parameter(Mandatory)][string]$Build,
  [string]$Architectures = '80-real;120-real',
  [string]$Toolkit = 'C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.5',
  [string]$VsDev = 'C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/Tools/VsDevCmd.bat',
  [string[]]$Targets = @('llama-completion','llama-bench','llama-perplexity','llama-mtmd-cli','llama-quantize','llama-server','inkling-logits'),
  [switch]$KernelsOnly,
  [switch]$StrataNative
)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath (Split-Path $VsDev -Parent)
try {
  $environmentLines = & $env:ComSpec /d /c 'call VsDevCmd.bat -arch=x64 -host_arch=x64 >nul && set'
} finally { Pop-Location }
foreach ($entry in $environmentLines) {
  if ($entry -match '^([^=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
  }
}
if ($LASTEXITCODE -ne 0) { throw 'MSVC environment initialisation failed' }
$buildPath = [IO.Path]::GetFullPath($Build)
$tmpPath = Join-Path $buildPath 'tmp'
New-Item -ItemType Directory -Path $tmpPath -Force | Out-Null
$env:TMP = $tmpPath
$env:TEMP = $tmpPath
$env:CUDA_PATH = $Toolkit
$env:Path = "$Toolkit/bin;" + $env:Path
if ($KernelsOnly) {
  $cccl=Join-Path $Toolkit 'include/cccl'
  if (Test-Path -LiteralPath (Join-Path $cccl 'cccl/cub/cub.cuh')) { $cccl=Join-Path $cccl 'cccl' }
  $argsCuda=@('-std=c++17','-O3','-shared','-Xcompiler','/utf-8,/Zc:preprocessor',"-I$cccl")
  foreach ($arch in ($Architectures -split ';')) {
    $sm=$arch.Split('-')[0]
    $argsCuda += "-gencode=arch=compute_$sm,code=sm_$sm"
  }
  Push-Location $buildPath
  try {
    & "$Toolkit/bin/nvcc.exe" @argsCuda (Join-Path $Source 'ggml/src/ggml-cuda/spin8_hadamard.cu') (Join-Path $PSScriptRoot 'spin8_encode.cu') -o (Join-Path $buildPath 'spin8-pq2.dll')
    if ($LASTEXITCODE) { throw 'Spin(8) CUDA kernel compilation failed' }
  } finally { Pop-Location }
  return
}
if (!(Test-Path -LiteralPath (Join-Path $Toolkit 'include/nvml.h'))) {
  $nvml = Get-ChildItem -LiteralPath (Split-Path $Toolkit -Parent) -Directory |
    Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'include/nvml.h' } |
    Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (!$nvml) { throw 'The NVIDIA Management Library development header is missing' }
  $headerDir = Join-Path $buildPath 'nvml-header'
  New-Item -ItemType Directory -Path $headerDir -Force | Out-Null
  Copy-Item -LiteralPath $nvml -Destination (Join-Path $headerDir 'nvml.h')
  $env:INCLUDE = "$headerDir;" + $env:INCLUDE
  Write-Output "NVML development header $nvml"
}
$ninja = Join-Path (Split-Path (Split-Path $VsDev -Parent) -Parent) 'IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
if (!(Test-Path -LiteralPath $ninja)) { $ninja = (Get-Command ninja -ErrorAction Stop).Source }
$opts = @('-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$ninja",'-DCMAKE_BUILD_TYPE=Release',
  "-DCMAKE_CUDA_ARCHITECTURES=$Architectures",
  "-DCMAKE_CUDA_COMPILER=$Toolkit/bin/nvcc.exe",'-DCMAKE_C_FLAGS=/utf-8',
  '-DCMAKE_CXX_FLAGS=/utf-8 /EHsc','-DCMAKE_CUDA_FLAGS=-Xcompiler=/utf-8,/Zc:preprocessor,/EHsc')
if ($StrataNative) {
  $opts += @('-DSTRATA_ENABLE_CUDA=ON',"-DSTRATA_INK_CUDA_ARCHS=$Architectures",'-DSTRATA_BUILD_TESTS=ON')
  if (!$PSBoundParameters.ContainsKey('Targets')) { $Targets = @('strata-inkling') }
} else {
  $opts += @('-DGGML_CUDA=ON','-DGGML_NATIVE=OFF','-DGGML_CCACHE=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_TESTS=ON')
}
& cmake -S $Source -B $buildPath @opts
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed' }
& cmake --build $buildPath --parallel 5 --target @Targets
if ($LASTEXITCODE -ne 0) { throw 'Native compilation failed' }
