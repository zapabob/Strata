# Create/repair the Strata desktop and Start Menu shortcuts for the real install.
$ErrorActionPreference='Stop'
$exe='C:\Users\downl\AppData\Local\Programs\Strata\strata-desktop.exe'
$work='C:\Users\downl\AppData\Local\Programs\Strata'
if(-not (Test-Path $exe)){ throw "strata-desktop.exe not found: $exe" }
$desktop=[Environment]::GetFolderPath('Desktop') + '\Strata.lnk'
$start=[Environment]::GetFolderPath('StartMenu') + '\Programs\Strata.lnk'
$sh=New-Object -ComObject WScript.Shell
foreach($p in @($desktop,$start)){
  $sc=$sh.CreateShortcut($p)
  $sc.TargetPath=$exe
  $sc.Arguments=''
  $sc.WorkingDirectory=$work
  $sc.IconLocation="$exe,0"
  $sc.Description='Hakua / Strata - local model desktop app'
  $sc.Save()
  $v=$sh.CreateShortcut($p)
  "$p -> $($v.TargetPath)"
}
