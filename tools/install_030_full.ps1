$ErrorActionPreference = "Stop"

Write-Host "--- Strata 0.3.0 Desktop & Engine Deployment ---"

# 1. Kill any existing strata desktop or server processes
Get-Process -Name "strata-desktop", "strata", "strata-vision" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Terminating active process: $($_.Name) (PID: $($_.Id))"
    Stop-Process -Id $_.Id -Force
}

$repo = "C:\Users\downl\Documents\ChatGPT\Strata"
$srcExe = "H:\Strata\build\native-spin8\Release\strata.exe"
$srcDll = "H:\Strata\build\native-spin8\Release\strata_kq.dll"
$srcEngine0147 = "C:\Users\downl\AppData\Local\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13"

# 2. Deploy 0.3.0 Engine Component
$destEngines = @(
    "C:\Users\downl\AppData\Local\Strata\components\engine\0.3.0-windows-x86_64-cuda-cuda13",
    "C:\Users\downl\AppData\Local\Programs\Strata\engine-bundle\0.3.0-windows-x86_64-cuda-cuda13"
)

foreach ($dest in $destEngines) {
    Write-Host "Creating 0.3.0 engine directory: $dest"
    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }
    # Copy all base libraries from 0.1.47
    Copy-Item -Path "$srcEngine0147\*" -Destination $dest -Recurse -Force
    # Ensure strata.exe and strata_kq.dll are latest 0.3.0 binaries
    Copy-Item -Path $srcExe -Destination "$dest\strata.exe" -Force
    Copy-Item -Path $srcDll -Destination "$dest\strata_kq.dll" -Force

    # Update manifest to version 0.3.0
    $manifestFile = "$dest\engine-component.json"
    $exeHash = (Get-FileHash -Algorithm SHA256 "$dest\strata.exe").Hash.ToLower()
    $exeBytes = (Get-Item "$dest\strata.exe").Length
    $dllHash = (Get-FileHash -Algorithm SHA256 "$dest\strata_kq.dll").Hash.ToLower()
    $dllBytes = (Get-Item "$dest\strata_kq.dll").Length

    $manifest = Get-Content $manifestFile -Raw | ConvertFrom-Json
    $manifest.version = "0.3.0"
    $manifest.build_id = "0.3.0+cuda13.2+sm120+spin8"
    foreach ($f in $manifest.files) {
        if ($f.path -eq "strata.exe") {
            $f.sha256 = $exeHash
            $f.bytes = $exeBytes
        }
        elseif ($f.path -eq "strata_kq.dll") {
            $f.sha256 = $dllHash
            $f.bytes = $dllBytes
        }
    }
    $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestFile -Encoding UTF8
    Write-Host "  Manifest verified for 0.3.0: $manifestFile"
}

# 3. Update updater state.json
$stateFile = "C:\Users\downl\AppData\Local\Strata\components\.updates\state.json"
if (Test-Path $stateFile) {
    $state = Get-Content $stateFile -Raw | ConvertFrom-Json
    $state.last_check.app = "0.3.0"
    $state.last_check.control = "0.3.0"
    $state.last_check.engine = "0.3.0"
    $state.last_check.engine_installed = "0.3.0"
    $state | ConvertTo-Json -Depth 10 | Set-Content $stateFile -Encoding UTF8
    Write-Host "Updated state.json to version 0.3.0"
}

# 4. Synchronize host dist (Vite build) and server
$hostDistSrc = "$repo\apps\host\dist"
$hostDistDst = "C:\Users\downl\AppData\Local\Programs\Strata\host\dist"
Write-Host "Deploying UI dist to: $hostDistDst"
Copy-Item -Path "$hostDistSrc\*" -Destination $hostDistDst -Recurse -Force

$hostServerSrc = "$repo\apps\host\server"
$hostServerDst = "C:\Users\downl\AppData\Local\Programs\Strata\host\server"
Write-Host "Deploying server scripts to: $hostServerDst"
Copy-Item -Path "$hostServerSrc\*" -Destination $hostServerDst -Recurse -Force

# 5. Synchronize control
$controlDst = "C:\Users\downl\AppData\Local\Programs\Strata\control"
Write-Host "Deploying control to: $controlDst"
Copy-Item -Path "$repo\strata.py" -Destination "$controlDst\strata.py" -Force
Copy-Item -Path "$repo\setup.py" -Destination "$controlDst\setup.py" -Force
Set-Content -Path "$controlDst\VERSION" -Value "0.3.0" -NoNewline
Copy-Item -Path "$repo\strata_cli" -Destination $controlDst -Recurse -Force
Copy-Item -Path "$repo\strata_control" -Destination $controlDst -Recurse -Force
Copy-Item -Path "$repo\serve" -Destination $controlDst -Recurse -Force
Copy-Item -Path "$repo\tools" -Destination $controlDst -Recurse -Force

# 6. Verify components engine resolution
Write-Host "Verifying components engine..."
$engineCheck = & "C:\Users\downl\AppData\Local\Programs\Strata\control\python\python.exe" -c "
from strata_control import engine_component
c = engine_component.resolve(full=True)
print(f'RESOLVED_ENGINE: {c.version} at {c.exe}')
"
Write-Host $engineCheck

Write-Host "Deployment completed successfully!"
