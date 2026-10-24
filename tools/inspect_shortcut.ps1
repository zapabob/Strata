$sh = New-Object -ComObject WScript.Shell
$target = $sh.CreateShortcut("C:\Users\downl\Desktop\Strata.lnk")
[PSCustomObject]@{
    TargetPath = $target.TargetPath
    Arguments = $target.Arguments
    WorkingDirectory = $target.WorkingDirectory
    IconLocation = $target.IconLocation
} | Format-List

# Also check Start Menu shortcuts
$startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
Get-ChildItem -Path $startMenu -Filter "*strata*" -Recurse | ForEach-Object {
    $lnk = $sh.CreateShortcut($_.FullName)
    Write-Host "Start Menu Shortcut:" $_.FullName
    Write-Host "  TargetPath:" $lnk.TargetPath
    Write-Host "  Arguments:" $lnk.Arguments
    Write-Host "  WorkingDir:" $lnk.WorkingDirectory
}
