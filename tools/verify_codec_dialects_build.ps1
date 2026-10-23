param(
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string[]]$CommandArgs
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($OutputRoot)
if (-not $root.StartsWith('H:\Strata\build\task5a-', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Expected dedicated H:/Strata/build/task5a-* output root'
}
if ($Label -notmatch '^[a-zA-Z0-9-]+$') { throw 'Invalid evidence label' }
New-Item -ItemType Directory -Path $root -Force | Out-Null
$stdout = Join-Path $root ($Label + '.stdout.log')
$stderr = Join-Path $root ($Label + '.stderr.log')
if ((Test-Path $stdout) -or (Test-Path $stderr)) { throw 'Preserve prior receipts; use a new label' }
$temp = Join-Path $root 'temp'
New-Item -ItemType Directory -Path $temp -Force | Out-Null
$savedTemp=$env:TEMP; $savedTmp=$env:TMP
try {
    $env:TEMP=$temp; $env:TMP=$temp
    $quoted = foreach($a in $CommandArgs) {
        if ($a.Contains('"')) {throw 'Embedded quotes not supported'}
        '"' + $a + '"'
    }
    if ((Get-PSDrive H).Free -lt 256MB) {throw 'Start capacity below 256MiB'}
    $process = Start-Process -FilePath $Executable -ArgumentList $quoted -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    do {
        $used = (Get-ChildItem -LiteralPath $root -File -Recurse | Measure-Object Length -Sum).Sum
        if ($used -gt 96MB -or (Get-PSDrive H).Free -lt 128MB) {
            # Only this owned process tree; retain every partial output.
            if(-not $process.HasExited) {$process.Kill($true)}
            throw 'Owned build stopped at capacity guard; partial evidence retained'
        }
        Start-Sleep -Milliseconds 300
        $process.Refresh()
    } while (-not $process.HasExited)
    $process.WaitForExit()
    Get-Content -LiteralPath $stdout
    Get-Content -LiteralPath $stderr
    Write-Output "exit=$($process.ExitCode); output_bytes=$used; free_bytes=$((Get-PSDrive H).Free)"
    exit $process.ExitCode
} finally { $env:TEMP=$savedTemp; $env:TMP=$savedTmp }
