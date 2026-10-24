$ErrorActionPreference = "Stop"

$srcExe = "H:\Strata\build\native-spin8\Release\strata.exe"
$srcDll = "H:\Strata\build\native-spin8\Release\strata_kq.dll"

Write-Host "Source Exe:" $srcExe "(" (Get-Item $srcExe).Length "bytes )"
Write-Host "Source Dll:" $srcDll "(" (Get-Item $srcDll).Length "bytes )"

$engineTargets = @(
    "C:\Users\downl\AppData\Local\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13",
    "C:\Users\downl\AppData\Local\Programs\Strata\engine-bundle\0.1.47-windows-x86_64-cuda-cuda13"
)

foreach ($t in $engineTargets) {
    if (Test-Path $t) {
        Write-Host "Updating engine target: $t"
        Copy-Item -Path $srcExe -Destination "$t\strata.exe" -Force
        Copy-Item -Path $srcDll -Destination "$t\strata_kq.dll" -Force
    }
}

# Synchronize full control scripts from repository
$repo = "C:\Users\downl\Documents\ChatGPT\Strata"
$control = "C:\Users\downl\AppData\Local\Programs\Strata\control"

Write-Host "Synchronizing Python control files to: $control"
Copy-Item -Path "$repo\strata.py" -Destination "$control\strata.py" -Force
Copy-Item -Path "$repo\setup.py" -Destination "$control\setup.py" -Force
Copy-Item -Path "$repo\strata_cli" -Destination $control -Recurse -Force
Copy-Item -Path "$repo\strata_control" -Destination $control -Recurse -Force
Copy-Item -Path "$repo\serve" -Destination $control -Recurse -Force
Copy-Item -Path "$repo\tools" -Destination $control -Recurse -Force

# Synchronize host build
$hostDistSrc = "$repo\apps\host\dist"
$hostDistDst = "C:\Users\downl\AppData\Local\Programs\Strata\host\dist"
if (Test-Path $hostDistSrc) {
    Write-Host "Synchronizing host dist to: $hostDistDst"
    Copy-Item -Path "$hostDistSrc\*" -Destination $hostDistDst -Recurse -Force
}
$hostServerSrc = "$repo\apps\host\server"
$hostServerDst = "C:\Users\downl\AppData\Local\Programs\Strata\host\server"
if (Test-Path $hostServerSrc) {
    Write-Host "Synchronizing host server to: $hostServerDst"
    Copy-Item -Path "$hostServerSrc\*" -Destination $hostServerDst -Recurse -Force
}

# Ensure C:\Users\downl\AppData\Local\Programs\Strata\control\bin is in User PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$binDir = "C:\Users\downl\AppData\Local\Programs\Strata\control\bin"
if ($userPath -notmatch [regex]::Escape($binDir)) {
    Write-Host "Adding $binDir to User PATH..."
    $newPath = "$binDir;$userPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "User PATH updated."
} else {
    Write-Host "$binDir is already in User PATH."
}

Write-Host "Full installation synchronization complete!"
