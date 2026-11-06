$ErrorActionPreference='Stop'
$target='C:\Users\downl\AppData\Local\Programs\Strata\strata-desktop.exe'
$out='H:\Strata\releases\local-052-20261106-opencode'
$shell=New-Object -ComObject WScript.Shell
$paths=@((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Strata.lnk'),(Join-Path ([Environment]::GetFolderPath('Programs')) 'Strata.lnk'))
$checked=0
foreach($path in $paths){
 if(-not(Test-Path -LiteralPath $path)){throw 'Expected Strata shortcut missing'}
 $link=$shell.CreateShortcut($path)
 if($link.TargetPath -ine $target){throw 'Strata shortcut still targets another installation'}
 if($link.Arguments){throw 'Unexpected Strata shortcut arguments'}
 $checked++
}
$version=(Get-Item -LiteralPath $target).VersionInfo.ProductVersion
if($version -ne '0.5.2-local.1'){throw 'Installed shell product version differs'}
$report=[ordered]@{ok=$true;shortcutsChecked=$checked;allTargetCDrive=$true;shellProductVersion=$version}
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'shortcuts.json') -Encoding utf8
$report | ConvertTo-Json -Compress
