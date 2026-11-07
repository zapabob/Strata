# Called only with stdout/stderr captured in memory by foundation.py.
# Never run this helper directly in a console or transcript: commands can contain keys.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
if ([Console]::In.ReadLine() -ne 'PRIVATE_PIPE') { exit 2 }
try {
    $rows = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -eq 'C:\Users\downl\.hermes\llama\prism-b10826-c9c34bc\bin\llama-server.exe' -or
        $_.ExecutablePath -like 'C:\Users\downl\AppData\Local\Programs\Strata\*' -or
        $_.ExecutablePath -like 'C:\Users\downl\AppData\Local\Strata\components\*'
    } | ForEach-Object {
        [pscustomobject]@{pid=[int]$_.ProcessId; ppid=[int]$_.ParentProcessId; exe=$_.ExecutablePath;
            createdUtc=$_.CreationDate.ToUniversalTime().ToString('o'); commandLine=$_.CommandLine}
    })
    ConvertTo-Json -InputObject $rows -Depth 4 -Compress
} catch { exit 1 }
