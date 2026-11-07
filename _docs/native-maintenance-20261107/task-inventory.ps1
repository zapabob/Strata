# Read-only. Private stdout pipe only; no task enable/disable/start/stop calls.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
if ([Console]::In.ReadLine() -ne 'PRIVATE_PIPE') { exit 2 }
try {
    $rows = @(Get-ScheduledTask | Where-Object {
        $_.TaskName -match '(?i)hermes.*(llama|generation)' -or
        @($_.Actions | Where-Object { $_.Arguments -match '(?i)Ensure-HermesGeneration|\.hermes[\\/]llama' }).Count -gt 0
    } | ForEach-Object {
        $task = $_
        [pscustomobject]@{
            name = $task.TaskName; path = $task.TaskPath; state = [string]$task.State
            actions = @($task.Actions | ForEach-Object {
                [pscustomobject]@{execute=$_.Execute; arguments=$_.Arguments; workingDirectory=$_.WorkingDirectory}
            })
            triggers = @($task.Triggers | ForEach-Object {
                [pscustomobject]@{type=$_.CimClass.CimClassName; enabled=$_.Enabled;
                    interval=$_.Repetition.Interval; duration=$_.Repetition.Duration}
            })
        }
    })
    ConvertTo-Json -InputObject $rows -Depth 7 -Compress
} catch { exit 1 }
