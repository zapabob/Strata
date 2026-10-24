$ErrorActionPreference = "Stop"

$srcExe = "H:\Strata\build\native-spin8\Release\strata.exe"
$srcDll = "H:\Strata\build\native-spin8\Release\strata_kq.dll"

$exeHash = (Get-FileHash -Algorithm SHA256 $srcExe).Hash.ToLower()
$exeBytes = (Get-Item $srcExe).Length
$dllHash = (Get-FileHash -Algorithm SHA256 $srcDll).Hash.ToLower()
$dllBytes = (Get-Item $srcDll).Length

Write-Host "New engine: strata.exe ($exeBytes bytes, $exeHash)"
Write-Host "New engine: strata_kq.dll ($dllBytes bytes, $dllHash)"

$allEngineDirs = @(
    "C:\Users\downl\AppData\Local\Strata\components\engine\0.1.45.3-windows-x86_64-cuda-cuda13",
    "C:\Users\downl\AppData\Local\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13",
    "C:\Users\downl\AppData\Local\Programs\Strata\engine-bundle\0.1.47-windows-x86_64-cuda-cuda13"
)

foreach ($dir in $allEngineDirs) {
    if (Test-Path $dir) {
        Write-Host "Overwriting engine in: $dir"
        Copy-Item -Path $srcExe -Destination "$dir\strata.exe" -Force
        Copy-Item -Path $srcDll -Destination "$dir\strata_kq.dll" -Force

        # Update engine-component.json
        $manifestPath = "$dir\engine-component.json"
        if (Test-Path $manifestPath) {
            $json = Get-Content $manifestPath -Raw | ConvertFrom-Json
            foreach ($file in $json.files) {
                if ($file.path -eq "strata.exe") {
                    $file.sha256 = $exeHash
                    $file.bytes = $exeBytes
                }
                elseif ($file.path -eq "strata_kq.dll") {
                    $file.sha256 = $dllHash
                    $file.bytes = $dllBytes
                }
            }
            $json | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
            Write-Host "  Updated manifest: $manifestPath"
        }
    }
}

Write-Host "Verification of engine files:"
Get-ChildItem -Path "C:\Users\downl\AppData\Local\Strata\components\engine\*\strata.exe", "C:\Users\downl\AppData\Local\Programs\Strata\engine-bundle\*\strata.exe" | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
