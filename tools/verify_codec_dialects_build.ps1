<#
.SYNOPSIS
Runs one bounded Windows validation command; keeps every labelled receipt.
.DESCRIPTION
Requires Windows 10+ and Windows PowerShell 5.1+ with an existing native executable.
MaxOutputBytes covers the entire evidence root, including earlier files. Select
an explicit larger cap for a larger operation; old evidence is never removed.
Stdout and stderr are byte-capped together. Other files are sampled every 20 ms:
their cap is a stop threshold, not a filesystem quota. ExpectedAdditionalPeakBytes
must cover ALL additional disk use, including objects outside the evidence root.
The reserve is at least 10 GiB on H:. This is a guard for trusted build commands,
not a security sandbox against malicious children or concurrent same-user writes.
#>
param(
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][string]$Executable,
    [AllowEmptyCollection()][AllowEmptyString()][string[]]$CommandArgs = @(),
    [long]$ReserveBytes = 10GB,
    [long]$ExpectedAdditionalPeakBytes = 96MB,
    [long]$MaxOutputBytes = 96MB,
    [int]$TimeoutSeconds = 1800
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
if ($Label -notmatch '^[a-zA-Z0-9-]{1,100}$' -or
    $Label -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$') {
    throw 'Invalid evidence label'
}
$helper = Join-Path $PSScriptRoot 'verify_bounded_process.cs'
if (-not ('StrataValidation.BoundedProcess' -as [type])) { Add-Type -Path $helper }
$sha = [Security.Cryptography.SHA256]::Create()
try { $helperHash = [BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($helper))).Replace('-', '') }
finally { $sha.Dispose() }
$scope = $null; $receiptStream = $null
$savedTemp = $env:TEMP; $savedTmp = $env:TMP
$resultCode = 125
try {
    $scope = New-Object StrataValidation.EvidenceScope($OutputRoot)
    $receiptPath = Join-Path $scope.Root ($Label + '.receipt.json')
    foreach ($suffix in @('.stdout.log', '.stderr.log', '.receipt.json', '.temp')) {
        if (Test-Path -LiteralPath (Join-Path $scope.Root ($Label + $suffix))) {
            throw 'Preserve prior receipts; use a new label'
        }
    }
    # CreateNew reserves the label against concurrent runs and prevents replacement.
    $receiptStream = [IO.File]::Open($receiptPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $record = [ordered]@{
        schema = 1; label = $Label; state = 'starting'
        started_utc = [DateTime]::UtcNow.ToString('o')
        powershell_version = $PSVersionTable.PSVersion.ToString()
        helper_sha256 = $helperHash
        reserve_bytes = $ReserveBytes; expected_additional_peak_bytes = $ExpectedAdditionalPeakBytes
        max_output_bytes = $MaxOutputBytes; timeout_seconds = $TimeoutSeconds
        child_exit_code = $null; guard_reason = $null; error = $null
        contained_before_resume = $null; active_processes_after_cleanup = $null
        captured_bytes = 0; output_bytes = 0; free_bytes = $scope.FreeBytes()
    }
    function Save-Receipt {
        $bytes = [Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Depth 4))
        $receiptStream.Position = 0
        $receiptStream.Write($bytes, 0, $bytes.Length)
        $receiptStream.SetLength($bytes.Length)
        $receiptStream.Flush($true)
    }
    Save-Receipt
    try {
        if ($ReserveBytes -lt 10GB -or $ExpectedAdditionalPeakBytes -lt $MaxOutputBytes -or
            $MaxOutputBytes -le 0 -or $TimeoutSeconds -le 0) { throw 'Invalid resource limits' }
        if ($record.free_bytes -lt $ReserveBytes -or
            $ExpectedAdditionalPeakBytes -gt ($record.free_bytes - $ReserveBytes)) {
            $record.guard_reason = 'start_capacity'
        } else {
            $temp = Join-Path $scope.Root ($Label + '.temp')
            [IO.Directory]::CreateDirectory($temp) | Out-Null
            $env:TEMP = $temp; $env:TMP = $temp
            if ([IO.Path]::IsPathRooted($Executable)) {
                $resolvedExecutable = (Get-Item -LiteralPath $Executable -ErrorAction Stop).FullName
            } else {
                $resolvedExecutable = (Get-Command -Name $Executable -CommandType Application -ErrorAction Stop).Source
            }
            $run = [StrataValidation.BoundedProcess]::Run($scope, $Label, $resolvedExecutable,
                $CommandArgs, (Get-Location).ProviderPath, $ReserveBytes,
                $ExpectedAdditionalPeakBytes, $MaxOutputBytes, $TimeoutSeconds)
            $record.child_exit_code = $run.ChildExitCode
            $record.guard_reason = $run.GuardReason
            $record.error = $run.Error
            $record.contained_before_resume = $run.ContainedBeforeResume
            $record.active_processes_after_cleanup = $run.ActiveProcessesAfterCleanup
            $record.captured_bytes = $run.CapturedBytes
            $record.output_bytes = $run.OutputBytes
            $record.free_bytes = $run.FreeBytes
            if ($null -eq $run.GuardReason -and $null -ne $run.ChildExitCode) {
                $resultCode = [BitConverter]::ToInt32([BitConverter]::GetBytes([uint32]$run.ChildExitCode), 0)
            }
        }
    } catch {
        $record.guard_reason = 'runner_error'
        $record.error = $_.Exception.Message
    } finally {
        $record.state = 'finished'
        $record.finished_utc = [DateTime]::UtcNow.ToString('o')
        Save-Receipt
    }
    Write-Output ('exit={0}; guard={1}; output_bytes={2}; free_bytes={3}; receipt={4}' -f
        $record.child_exit_code, $record.guard_reason, $record.output_bytes, $record.free_bytes, $receiptPath)
} finally {
    $env:TEMP = $savedTemp; $env:TMP = $savedTmp
    if ($null -ne $receiptStream) { $receiptStream.Dispose() }
    if ($null -ne $scope) { $scope.Dispose() }
}
exit $resultCode
